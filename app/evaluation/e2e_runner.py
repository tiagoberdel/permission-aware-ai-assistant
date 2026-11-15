import argparse
import asyncio
import inspect
import json
import math
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app.config import settings
from app.evaluation.dataset import DATASET_PATH, load_questions
from app.evaluation.e2e import run_case
from app.evaluation.scoring import score_attack, score_authorized, score_unauthorized
from app.services.retrieval import retrieve_documents
from app.vector_store.store import get_vector_store

ATTACKS_PATH = DATASET_PATH.parent / "attacks.json"
MANIFEST_PATH = DATASET_PATH.parents[1] / "metadata" / "documents.json"
RESULTS_PATH = DATASET_PATH.parents[2] / "e2e_results.json"

KINDS = ("authorized", "unauthorized", "attack")


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_cases(questions, attacks):
    cases = []

    for question in questions:
        if question["type"] not in ("authorized", "unauthorized"):
            raise ValueError(f"Unknown question type in {question['id']}")

        for language in ("es", "en"):
            cases.append(
                {
                    "kind": question["type"],
                    "item": question,
                    "language": language,
                    "asker": question["asker"],
                    "query": question[f"question_{language}"],
                }
            )

    for attack in attacks:
        for language in ("es", "en"):
            cases.append(
                {
                    "kind": "attack",
                    "item": attack,
                    "language": language,
                    "asker": attack["asker"],
                    "query": attack[f"prompt_{language}"],
                }
            )

    return cases


def score_case(case, run, manifest):
    item = case["item"]
    language = case["language"]

    if case["kind"] == "authorized":
        return score_authorized(item, language, run)

    if case["kind"] == "unauthorized":
        document = manifest[item["target_doc_id"]]
        return score_unauthorized(item, language, run, document=document, query=case["query"])

    return score_attack(item, language, run)


async def execute_case(case, manifest, retries, retry_wait):
    attempts = 0

    while True:
        try:
            run = await run_case(case["asker"], case["query"])
            break
        except Exception as error:
            attempts += 1

            if attempts > retries:
                return {
                    "case_id": case["item"]["id"],
                    "kind": case["kind"],
                    "language": case["language"],
                    "verdict": "error",
                    "error": f"{type(error).__name__}: {error}",
                }

            await asyncio.sleep(retry_wait)

    result = score_case(case, run, manifest)

    return {
        **asdict(result),
        "answer": run.answer,
        "retrieved_document_ids": run.retrieved_document_ids,
        "tool_calls": run.tool_calls,
        "latency_s": run.latency_s,
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "finish_reason": run.finish_reason,
    }


def percentile(values, fraction):
    if not values:
        return None

    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)

    return ordered[index]


def rate(count, total):
    return round(count / total, 4) if total else None


def summarize(results):
    valid = [r for r in results if r["verdict"] != "error"]
    authorized = [r for r in valid if r["kind"] == "authorized"]
    unauthorized = [r for r in valid if r["kind"] == "unauthorized"]
    sensitive = [r for r in valid if r["kind"] in ("unauthorized", "attack")]
    latencies = [r["latency_s"] for r in valid]

    return {
        "cases": len(results),
        "by_kind": {
            kind: {
                "total": sum(1 for r in results if r["kind"] == kind),
                **Counter(r["verdict"] for r in results if r["kind"] == kind),
            }
            for kind in KINDS
        },
        "leaks": sum(1 for r in sensitive if r["verdict"] == "leak"),
        "leak_rate": rate(sum(1 for r in sensitive if r["verdict"] == "leak"), len(sensitive)),
        "false_refusal_rate": rate(
            sum(1 for r in authorized if r["verdict"] == "false_refusal"), len(authorized)
        ),
        "answer_accuracy": rate(sum(1 for r in authorized if r["verdict"] == "ok"), len(authorized)),
        "existence_leak_rate": rate(
            sum(1 for r in unauthorized if r["existence_leak"]), len(unauthorized)
        ),
        "truncated": sum(1 for r in valid if r["verdict"] == "truncated"),
        "errors": len(results) - len(valid),
        "latency_p50_s": percentile(latencies, 0.5),
        "latency_p95_s": percentile(latencies, 0.95),
        "input_tokens": sum(r["input_tokens"] or 0 for r in valid),
        "output_tokens": sum(r["output_tokens"] or 0 for r in valid),
    }


def format_summary(summary):
    lines = ["", "RESULTS", "-------"]

    for kind in KINDS:
        counts = {k: v for k, v in summary["by_kind"][kind].items() if k != "total"}
        lines.append(f"{kind:<13} {summary['by_kind'][kind]['total']:>3} cases  {counts}")

    lines += [
        "",
        f"leaks:               {summary['leaks']}  (leak rate {summary['leak_rate']})",
        f"false refusal rate:  {summary['false_refusal_rate']}",
        f"answer accuracy:     {summary['answer_accuracy']}",
        f"existence leak rate: {summary['existence_leak_rate']}",
        f"truncated: {summary['truncated']}   errors: {summary['errors']}",
        f"latency p50 / p95:   {summary['latency_p50_s']} s / {summary['latency_p95_s']} s",
        f"tokens in / out:     {summary['input_tokens']} / {summary['output_tokens']}",
    ]

    return "\n".join(lines)


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
            cwd=RESULTS_PATH.parent,
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def warm_up():
    get_vector_store().similarity_search("warm-up", k=1)


async def run_all(cases, manifest, retries, retry_wait, pause):
    results = []

    for index, case in enumerate(cases, start=1):
        result = await execute_case(case, manifest, retries, retry_wait)
        results.append(result)

        print(
            f"[{index}/{len(cases)}] {result['kind']:<12} "
            f"{result['case_id']:<5} {result['language']}  {result['verdict']}",
            flush=True,
        )

        if pause:
            await asyncio.sleep(pause)

    return results


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run the end-to-end evaluation.")
    parser.add_argument("--only", choices=KINDS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path, default=RESULTS_PATH)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-wait", type=float, default=20.0)
    parser.add_argument("--pause", type=float, default=0.0)

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    manifest = {doc["document_id"]: doc for doc in load_json(MANIFEST_PATH)}
    cases = build_cases(load_questions(), load_json(ATTACKS_PATH))

    if args.only:
        cases = [case for case in cases if case["kind"] == args.only]

    if args.limit:
        cases = cases[: args.limit]

    warm_up()

    results = asyncio.run(run_all(cases, manifest, args.retries, args.retry_wait, args.pause))
    summary = summarize(results)

    report = {
        "meta": {
            "date": date.today().isoformat(),
            "model": settings.GROQ_MODEL,
            "commit": git_commit(),
            "cases": len(cases),
            "documents": len(manifest),
            "retrieval_k": inspect.signature(retrieve_documents).parameters["k"].default,
        },
        "summary": summary,
        "cases": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(format_summary(summary))
    print(f"\nSaved to {args.output}")

    return 1 if summary["leaks"] else 0


if __name__ == "__main__":
    sys.exit(main())