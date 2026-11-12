from collections import defaultdict
from pathlib import Path

from app.ingestion.service import ingest_documents
from app.vector_store.store import (
    index_documents,
    clear_collection,
    get_vector_store,
    search_documents,
)
from app.roles import RoleName

def main():
    try:
        base_dir = Path(__file__).resolve().parent.parent.parent / "data" / "andino_dataset"
        documents_json_path = base_dir / "metadata" / "documents.json"

        if not documents_json_path.exists():
            raise FileNotFoundError(f"Documents metadata file not found: {documents_json_path}")

        clear_collection()

        ingested_documents = ingest_documents(
            manifest_path=documents_json_path,
            dataset_root=base_dir
        )

        index_documents(ingested_documents)

        print("\n" + "="*50)
        print(" CHUNKS PER DOCUMENT SUMMARY ")
        print("="*50)

        chunks_per_doc = defaultdict(int)
        for doc in ingested_documents:
            doc_id = doc.metadata.get("document_id", "Unknown")
            chunks_per_doc[doc_id] += 1

        for doc_id, count in chunks_per_doc.items():
            print(f"Document: {doc_id} -> {count} chunks")

        print("="*50 + "\n")

        assert len(chunks_per_doc) == 42, f"Expected 42 indexed documents, but found {len(chunks_per_doc)}."

        store = get_vector_store()
        data = store.get(include=["metadatas", "documents"])

        print("\n" + "="*50)
        print(" STRICT INDEX & METADATA VERIFICATION ")
        print("="*50)

        found_x04 = False
        found_g12 = False

        for meta in data["metadatas"]:
            doc_id = meta.get("document_id")
            if doc_id == "X04":
                found_x04 = True
                assert meta.get("public_access") is False, "X04 has public_access set to True incorrectly."
                assert "allowed_roles" not in meta or not meta.get("allowed_roles"), "X04 must not have allowed_roles."
            elif doc_id == "G12":
                found_g12 = True
                assert meta.get("public_access") is True, "G12 must be public (public_access=True)."

        assert found_x04, "No chunks found for document X04."
        assert found_g12, "No chunks found for document G12."
        print("  [OK] X04 and G12 metadata validated successfully.")

        print("\n--- Verifying search as VISITOR (roles = []) ---")
        visitor_results = search_documents(query="Proyecto Horizonte", user_roles=[], store=store)
        for r in visitor_results:
            assert r.metadata.get("document_id") == "G12", f"Visitor accessed unauthorized document: {r.metadata.get('document_id')}"
        print("  [OK] Visitor sees G12 only.")

        users_profiles = {
            "Visitor": [],
            "Ramón (All roles)": [RoleName.EMPLOYEE, RoleName.SALES, RoleName.FINANCE, RoleName.HR],
            "Standard Employee": [RoleName.EMPLOYEE],
            "Sales": [RoleName.SALES],
            "Finance": [RoleName.FINANCE],
            "HR": [RoleName.HR],
            "Sales & Finance": [RoleName.SALES, RoleName.FINANCE]
        }

        print("\n--- Verifying that X04 NEVER leaks across all 7 user profiles ---")
        for profile_name, roles in users_profiles.items():
            results = search_documents(query="Proyecto Horizonte", user_roles=roles, store=store)
            for r in results:
                doc_id = r.metadata.get("document_id")
                assert doc_id != "X04", f"SECURITY BREACH: Profile '{profile_name}' gained access to restricted document X04."
            print(f"  [OK] Profile '{profile_name}' validated successfully (X04 safely restricted).")

        print("="*50)
        print(" ALL VERIFICATIONS PASSED SUCCESSFULLY! ")
        print("="*50 + "\n")

    except Exception as e:
        raise e

if __name__ == "__main__":
    main()