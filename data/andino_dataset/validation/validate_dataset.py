#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador del dataset Andino (bilingüe, permission-aware).

Uso:
    python validation/validate_dataset.py                 # valida e imprime resultado
    python validation/validate_dataset.py --write-report  # además escribe validation/validation_report.json

Sale con código 0 si TODOS los chequeos pasan y con código 1 si alguno falla.
Dependencias: Python 3.9+. Para extraer texto de PDF usa `pypdf` (pip install pypdf) o,
si no está, el comando `pdftotext` (poppler). DOCX se lee con la biblioteca estándar.
"""
import argparse, csv, datetime, json, os, re, subprocess, sys, zipfile

DENY_ALL_DOCS = {"X04"}  # sin permisos por diseño (deny-by-default)
N_DOCS, N_FILES, N_MD = 42, 84, 12
ROLES = {"employee", "sales", "finance", "hr"}
SENS = {"public", "internal", "confidential"}
LANGS = ("es", "en")
EXPECTED_USERS = {
    "sofia@andino.com": {"employee", "sales"},
    "ramon@andino.com": {"employee", "sales", "finance", "hr"},
    "martin@andino.com": {"employee", "finance"},
    "laura@andino.com": {"employee", "hr"},
    "diego@andino.com": {"employee", "sales"},
    "valentina@andino.com": {"employee", "finance"},
    "visitor@andino.com": set(),
}
IDENTITIES = list(EXPECTED_USERS)
SPANISH_ROLE_WORDS = {"ventas", "finanzas", "rrhh", "empleado"}
FOOTER_RE = re.compile(r"^(Página|Page) \d+ (de|of) \d+$")
NUM_RE = re.compile(r"\d[\d.,]*\d|\d")
ID_RE = re.compile(r"[A-Za-z]+-\d+(?:-\d+)?|[\w.\-]+@[\w.\-]+|[\w]+\.andino\.com|AndinoVisita-2026|H-LM")


# ----------------------------------------------------------------- helpers
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def norm(s):
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip().lower()

def extract_text(path):
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "md":
        with open(path, encoding="utf-8") as f:
            return f.read()
    if ext == "docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:tab/>", " ", xml)
        parts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>|(\n)", xml)
        text = "".join(a or b for a, b in parts)
        for k, v in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")):
            text = text.replace(k, v)
        return text
    if ext == "pdf":
        try:
            from pypdf import PdfReader
            return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
        except ImportError:
            try:
                return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout
            except Exception as e:
                raise RuntimeError("Se necesita pypdf o pdftotext para leer PDFs: %s" % e)
    raise ValueError(path)

def body_lines(text):
    return [l for l in text.splitlines() if not FOOTER_RE.match(l.strip())]

def number_tokens(text):
    toks = set()
    for l in body_lines(text):
        for m in NUM_RE.findall(l):
            toks.add(re.sub(r"[.,]", "", m))
    return toks

def id_tokens(text):
    return set(ID_RE.findall(text))

def can_read(roles, doc):
    return bool(doc.get("public_access")) or bool(set(roles) & set(doc["allowed_roles"]))


# ----------------------------------------------------------------- core
class Result:
    def __init__(self):
        self.checks = []
    def add(self, cid, desc, errors):
        self.checks.append({"id": cid, "description": desc, "status": "PASS" if not errors else "FAIL",
                            "error_count": len(errors), "errors": errors[:25]})
    @property
    def ok(self):
        return all(c["status"] == "PASS" for c in self.checks)


def run(root):
    R = Result()
    P = lambda *a: os.path.join(root, *a)
    try:
        docs = load_json(P("metadata", "documents.json"))
        users = load_json(P("users.json"))
        questions = load_json(P("evaluation", "questions.json"))
        attacks = load_json(P("evaluation", "attacks.json"))
        canaries = load_json(P("evaluation", "canaries.json"))
        injections = load_json(P("evaluation", "injection_docs.json"))
        tv = load_json(P("evaluation", "translation_validation.json"))
    except Exception as e:
        R.add("00", "Todos los archivos JSON existen y son válidos", [str(e)])
        return R, {}
    R.add("00", "Todos los archivos JSON existen y son válidos", [])
    by_id = {d["document_id"]: d for d in docs}
    uroles = {u["email"]: set(u["roles"]) for u in users}

    # 1 / 6
    errs = []
    if len(docs) != N_DOCS: errs.append("documentos lógicos = %d" % len(docs))
    R.add("01", "Exactamente %d documentos lógicos" % N_DOCS, errs)
    ids = [d["document_id"] for d in docs]
    R.add("06", "Ningún document_id duplicado", ["duplicado: %s" % i for i in set(ids) if ids.count(i) > 1])

    # 2 / 3 / 4 / 5
    files = [(d["document_id"], f) for d in docs for f in d.get("files", [])]
    R.add("02", "Exactamente %d archivos físicos referenciados" % N_FILES, [] if len(files) == N_FILES else ["archivos = %d" % len(files)])
    errs = []
    for lang in LANGS:
        for fmt, n in (("pdf", 20), ("docx", 10), ("md", N_MD)):
            c = sum(1 for _, f in files if f["language"] == lang and f["format"] == fmt)
            if c != n: errs.append("%s/%s = %d (esperado %d)" % (lang, fmt, c, n))
    R.add("03", "20 PDF, 10 DOCX y %d Markdown por idioma" % N_MD, errs)
    errs = []
    for d in docs:
        langs = sorted(f["language"] for f in d["files"])
        if langs != ["en", "es"]: errs.append("%s: idiomas %s" % (d["document_id"], langs))
    R.add("04", "Cada documento tiene versión en español e inglés", errs)
    errs = []
    for did, f in files:
        p = P(*f["path"].split("/"))
        if not os.path.isfile(p): errs.append("%s: falta %s" % (did, f["path"]))
        elif not f["path"].endswith("." + f["format"]): errs.append("%s: extensión no coincide con formato" % f["path"])
        elif ("/%s/" % f["language"]) not in "/" + f["path"]: errs.append("%s: carpeta no coincide con idioma" % f["path"])
    on_disk = set()
    for lang in LANGS:
        for fmt in ("pdf", "docx", "md"):
            dd = P("docs", lang, fmt)
            if os.path.isdir(dd):
                on_disk |= {"docs/%s/%s/%s" % (lang, fmt, x) for x in os.listdir(dd)}
    referenced = {f["path"] for _, f in files}
    for x in sorted(on_disk - referenced): errs.append("archivo huérfano no referenciado: %s" % x)
    R.add("05", "Todo archivo referenciado existe (y no hay huérfanos)", errs)

    # 7 / 8
    errs, errs8 = [], []
    for d in docs:
        for k in ("document_id", "title", "area", "sensitivity", "allowed_roles", "owner", "created_at", "original_language", "translations", "files"):
            if k not in d: errs.append("%s: falta %s" % (d.get("document_id"), k))
        if d.get("sensitivity") not in SENS: errs.append("%s: sensibilidad inválida" % d["document_id"])
        try: datetime.date.fromisoformat(d["created_at"])
        except Exception: errs.append("%s: fecha no ISO" % d["document_id"])
        if d.get("owner") not in EXPECTED_USERS or d.get("owner") == "visitor@andino.com": errs.append("%s: owner inválido" % d["document_id"])
        if d.get("original_language") != "es" or d.get("translations") != ["en"]: errs.append("%s: idiomas original/traducción" % d["document_id"])
        if not d.get("allowed_roles") and not d.get("public_access") and d["document_id"] not in DENY_ALL_DOCS: errs.append("%s: allowed_roles vacío" % d["document_id"])
        if d.get("sensitivity") == "public" and not d.get("public_access") and d.get("allowed_roles") != ["employee"]: errs.append("%s: público debe ser [employee]" % d["document_id"])
        for r in d.get("allowed_roles", []):
            if r not in ROLES: errs8.append("%s: rol inválido %s" % (d["document_id"], r))
    R.add("07", "Metadatos válidos en cada documento", errs)
    for u in users:
        for r in u["roles"]:
            if r not in ROLES: errs8.append("usuario %s: rol inválido %s" % (u["email"], r))
    R.add("08", "Todos los roles pertenecen a {employee, sales, finance, hr}", errs8)

    # 9 / 10 + exact identity model
    errs9, errs10 = [], []
    if {u["email"] for u in users} != set(IDENTITIES) or len(users) != 7: errs9.append("la lista de identidades no coincide con las 7 esperadas")
    for u in users:
        if u["email"] == "visitor@andino.com": continue
        if "employee" not in u["roles"]: errs9.append("%s sin employee" % u["email"])
        if u.get("is_visitor") is not False: errs9.append("%s debe tener is_visitor=false" % u["email"])
        if set(u["roles"]) != EXPECTED_USERS[u["email"]]: errs9.append("%s roles distintos de lo esperado" % u["email"])
    R.add("09", "Todo usuario interno tiene employee y los roles esperados", errs9)
    v = [u for u in users if u["email"] == "visitor@andino.com"]
    if not v or v[0].get("is_visitor") is not True or v[0]["roles"] != []: errs10.append("visitor debe tener is_visitor=true y roles=[]")
    if any(u.get("is_visitor") is True for u in users if u["email"] != "visitor@andino.com"): errs10.append("is_visitor=true en un usuario interno")
    R.add("10", "Visitor: is_visitor=true y sin roles", errs10)

    # 11 / 12
    errs11, errs12 = [], []
    with open(P("evaluation", "access_matrix.csv"), encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f); rows = list(rd); header = rd.fieldnames
    exp_header = ["document_id", "title", "sensitivity", "allowed_roles"] + IDENTITIES
    if header != exp_header: errs11.append("encabezado %s" % header)
    if len(rows) != N_DOCS: errs11.append("filas = %d" % len(rows))
    if {r["document_id"] for r in rows} != set(ids): errs11.append("los document_id de la matriz no coinciden con el manifiesto")
    R.add("11", "Matriz: %d filas y 7 columnas de identidades con emails exactos" % N_DOCS, errs11)
    for r in rows:
        d = by_id.get(r["document_id"])
        if not d: continue
        if [x for x in r["allowed_roles"].split("|") if x] != d["allowed_roles"]: errs12.append("%s: allowed_roles difiere del manifiesto" % r["document_id"])
        if r["sensitivity"] != d["sensitivity"]: errs12.append("%s: sensibilidad difiere" % r["document_id"])
        for e in IDENTITIES:
            exp = "ALLOW" if can_read(uroles.get(e, set()), d) else "DENY"
            if r[e] != exp: errs12.append("%s/%s: %s (esperado %s)" % (r["document_id"], e, r[e], exp))
    R.add("12", "Cada permiso de la matriz coincide con la regla de intersección de roles", errs12)

    # 13 / 14
    errs = [] if len(questions) == 30 else ["preguntas = %d" % len(questions)]
    R.add("13", "Exactamente 30 preguntas de evaluación", errs)
    na = sum(1 for q in questions if q["type"] == "authorized"); nu = sum(1 for q in questions if q["type"] == "unauthorized")
    R.add("14", "14 preguntas autorizadas y 16 no autorizadas", [] if (na, nu) == (14, 16) else ["autorizadas=%d no autorizadas=%d" % (na, nu)])
    errs = []
    qkeys = ["id", "asker", "question_es", "question_en", "target_doc_id", "type", "expected_behavior", "key_facts", "canary_markers", "notes"]
    for q in questions:
        for k in qkeys:
            if k not in q: errs.append("%s: falta %s" % (q.get("id"), k))
        if q["asker"] not in EXPECTED_USERS: errs.append("%s: asker inválido" % q["id"]); continue
        d = by_id.get(q["target_doc_id"])
        if not d: errs.append("%s: target_doc_id inválido" % q["id"]); continue
        allowed = can_read(uroles[q["asker"]], d)
        if q["type"] == "authorized" and not allowed: errs.append("%s: autorizada pero el asker no puede leer %s" % (q["id"], d["document_id"]))
        if q["type"] == "unauthorized" and allowed: errs.append("%s: no autorizada pero el asker SÍ puede leer %s" % (q["id"], d["document_id"]))
        for sid in q.get("supporting_doc_ids", []):
            if sid not in by_id: errs.append("%s: supporting_doc_id inválido %s" % (q["id"], sid))
            elif q["type"] == "authorized" and not can_read(uroles[q["asker"]], by_id[sid]): errs.append("%s: soporte %s no autorizado" % (q["id"], sid))
    R.add("13b", "Preguntas: campos completos y autorización coherente con la regla de roles", errs)

    # 15
    errs = [] if len(attacks) == 10 else ["ataques = %d" % len(attacks)]
    R.add("15", "Exactamente 10 escenarios de ataque", errs)
    errs = []
    akeys = ["id", "category", "asker", "prompt_es", "prompt_en", "must_not_leak_doc_ids", "leak_markers", "expected_behavior", "notes"]
    for a in attacks:
        for k in akeys:
            if k not in a: errs.append("%s: falta %s" % (a.get("id"), k))
        if a["asker"] not in EXPECTED_USERS: errs.append("%s: asker inválido" % a["id"]); continue
        for did in a["must_not_leak_doc_ids"]:
            if did not in by_id: errs.append("%s: doc inválido %s" % (a["id"], did))
            elif can_read(uroles[a["asker"]], by_id[did]): errs.append("%s: %s está AUTORIZADO para %s (no puede ser un must_not_leak)" % (a["id"], did, a["asker"]))
        if not a["leak_markers"]: errs.append("%s: sin leak_markers" % a["id"])
    if len({a["category"] for a in attacks}) < 8: errs.append("menos de 8 categorías de ataque")
    R.add("15b", "Ataques: campos completos, documentos realmente no autorizados y >=8 categorías", errs)

    # 16
    errs = []
    cids = [c["document_id"] for c in canaries]
    if sorted(cids) != sorted(ids): errs.append("canarios y documentos no coinciden 1 a 1")
    seen = {}
    for c in canaries:
        if c["document_id"] not in by_id: errs.append("canario con doc inválido %s" % c["document_id"]); continue
        if c["allowed_roles"] != by_id[c["document_id"]]["allowed_roles"]: errs.append("%s: allowed_roles del canario difiere del manifiesto" % c["document_id"])
        for k in ("canary_es", "canary_en", "sensitive_markers"):
            if not c.get(k): errs.append("%s: falta %s" % (c["document_id"], k))
        for k in ("canary_es", "canary_en"):
            key = norm(c[k])
            if key in seen and seen[key] != c["document_id"]: errs.append("canario duplicado entre %s y %s" % (seen[key], c["document_id"]))
            seen[key] = c["document_id"]
    R.add("16", "Cada canario referencia un documento válido; uno por documento, sin duplicados", errs)

    # 17
    errs = []
    for i in injections:
        if i["document_id"] not in by_id: errs.append("inyección con doc inválido %s" % i["document_id"])
        for t in i.get("restricted_doc_ids", []):
            if t not in by_id: errs.append("%s: restricted_doc_id inválido %s" % (i["document_id"], t))
        for aid in i.get("used_in_attacks", []):
            if aid not in {a["id"] for a in attacks}: errs.append("%s: ataque inexistente %s" % (i["document_id"], aid))
    R.add("17", "Cada referencia de inyección apunta a documentos (y ataques) válidos", errs)

    # extracción de texto
    texts, extract_errs = {}, []
    for did, f in files:
        try: texts[(did, f["language"])] = extract_text(P(*f["path"].split("/")))
        except Exception as e: extract_errs.append("%s: %s" % (f["path"], e))
    R.add("18a", "El texto se puede extraer de los %d archivos (PDF con texto seleccionable)" % N_FILES, extract_errs +
          ["%s/%s: texto casi vacío" % k for k, t in texts.items() if len(t.strip()) < 400])

    # 18 paridad de traducción
    errs = []
    tv_by = {x["document_id"]: x for x in tv.get("documents", [])}
    if set(tv_by) != set(ids): errs.append("translation_validation.json no cubre exactamente los %d documentos" % N_DOCS + "")
    for did in ids:
        if (did, "es") not in texts or (did, "en") not in texts: continue
        es, en = texts[(did, "es")], texts[(did, "en")]
        d = by_id[did]
        ne, nn = number_tokens(es), number_tokens(en)
        if ne != nn: errs.append("%s: cifras distintas. solo ES=%s solo EN=%s" % (did, sorted(ne - nn), sorted(nn - ne)))
        t = tv_by.get(did)
        if not t: continue
        for fct in t["critical_facts"]:
            if norm(fct["es"]) not in norm(es): errs.append("%s: hecho ES ausente: %r" % (did, fct["es"]))
            if norm(fct["en"]) not in norm(en): errs.append("%s: hecho EN ausente: %r" % (did, fct["en"]))
        for val in t["values_that_must_remain_identical"]:
            if re.search(r"\d", val) and not re.search(r"[A-Za-z@]", val):
                ok = val in ne and val in nn
            elif re.search(r"\d", val):
                ok = val in id_tokens(es) and val in id_tokens(en)
            else:
                ok = val in es and val in en
            if not ok: errs.append("%s: valor idéntico ausente en alguna versión: %r" % (did, val))
        # metadatos de autorización idénticos: las dos versiones heredan el mismo registro
        if len(d["files"]) != 2: errs.append("%s: debe tener exactamente 2 archivos" % did)
        if t.get("source_path_es") != next(f["path"] for f in d["files"] if f["language"] == "es") or \
           t.get("translation_path_en") != next(f["path"] for f in d["files"] if f["language"] == "en"):
            errs.append("%s: rutas de translation_validation no coinciden con el manifiesto" % did)
    # canarios presentes en ambos idiomas
    for c in canaries:
        did = c["document_id"]
        if (did, "es") not in texts: continue
        if norm(c["canary_es"]) not in norm(texts[(did, "es")]): errs.append("%s: canary_es no aparece en el archivo ES" % did)
        if norm(c["canary_en"]) not in norm(texts[(did, "en")]): errs.append("%s: canary_en no aparece en el archivo EN" % did)
        for m in c["sensitive_markers"]:
            if norm(m) not in norm(texts[(did, "es")]) and norm(m) not in norm(texts[(did, "en")]): errs.append("%s: marcador %r no aparece en ningún idioma" % (did, m))
    R.add("18", "Cada traducción conserva cifras, hechos críticos, canarios e identificadores; metadatos de permisos únicos", errs)

    # extra: marcadores no ambiguos entre documentos
    errs = []
    readers = {d["document_id"]: {e for e in IDENTITIES if can_read(uroles[e], d)} for d in docs}
    for c in canaries:
        for m in c["sensitive_markers"]:
            nm = norm(m)
            for (other, lang), t in texts.items():
                if other == c["document_id"]: continue
                if nm in norm(t) and not readers[other] <= readers[c["document_id"]]:
                    errs.append("marcador %r de %s aparece en %s/%s, legible por usuarios que no pueden leer %s" % (m, c["document_id"], other, lang, c["document_id"]))
    R.add("19", "Los marcadores de un documento no aparecen en documentos legibles por más usuarios (sin falsos positivos ni filtraciones cruzadas)", errs)

    # extra: ataques/inyecciones coherentes
    errs = []
    for i in injections:
        for lang in LANGS:
            key = "injected_instruction_" + lang
            tx = texts.get((i["document_id"], lang), "")
            if norm(i[key]) not in norm(tx): errs.append("%s: instrucción inyectada (%s) no aparece en el archivo" % (i["document_id"], lang))
    R.add("20", "Las instrucciones de inyección indirecta existen literalmente en ambos idiomas", errs)

    # extra: ningún rol/identificador en español, sin frontmatter con metadatos
    errs = []
    for blob_name, blob in (("documents.json", json.dumps(docs)), ("users.json", json.dumps(users)), ("canaries.json", json.dumps([c["allowed_roles"] for c in canaries])),
                            ("attacks/questions", json.dumps([q.get("asker") for q in questions] + [a.get("asker") for a in attacks]))):
        for w in SPANISH_ROLE_WORDS:
            if re.search(r'"%s"' % w, blob): errs.append("%s contiene el identificador en español %r" % (blob_name, w))
    for did, f in files:
        if f["format"] == "md" and extract_text(P(*f["path"].split("/"))).lstrip().startswith("---"):
            errs.append("%s: el Markdown no debe llevar frontmatter de metadatos" % f["path"])
    R.add("21", "Sin roles en español y sin metadatos de autorización embebidos en los documentos", errs)

    summary = {"logical_documents": len(docs), "physical_files": len(files), "users": len(users), "questions": len(questions),
               "authorized_questions": na, "unauthorized_questions": nu, "attacks": len(attacks)}
    return R, summary


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(here))
    ap.add_argument("--write-report", action="store_true")
    a = ap.parse_args()
    R, summary = run(a.root)
    for c in R.checks:
        print("[%s] %-4s %s" % (c["status"], c["id"], c["description"]))
        for e in c["errors"]: print("        - " + e)
    print("\nRESULTADO: %s (%d/%d chequeos OK)" % ("OK" if R.ok else "FALLÓ", sum(c["status"] == "PASS" for c in R.checks), len(R.checks)))
    if a.write_report:
        rep = {"tool": "validation/validate_dataset.py", "executed_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "overall_status": "PASS" if R.ok else "FAIL", "summary": summary, "checks": R.checks,
               "note": "Este reporte lo escribe el propio script al ejecutarse con --write-report; verifica integridad y consistencia del dataset, no la calidad de ningún sistema RAG."}
        with open(os.path.join(a.root, "validation", "validation_report.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
    sys.exit(0 if R.ok else 1)

if __name__ == "__main__":
    main()
