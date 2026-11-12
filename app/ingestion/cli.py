from collections import defaultdict
from pathlib import Path

from app.ingestion.service import ingest_documents
from app.vector_store.store import index_documents, clear_collection, get_vector_store, search_documents
from app.roles import RoleName

def main():
    try:
        base_dir = Path("data/andino_dataset")
        documents_json_path = base_dir / "metadata" / "documents.json"

        if not documents_json_path.exists():
            raise FileNotFoundError(
                f"Documents metadata file not found: {documents_json_path}"
            )

        clear_collection()

        ingested_documents = ingest_documents(
            manifest_path=documents_json_path,
            dataset_root=base_dir
        )

        index_documents(ingested_documents)

        print("\n" + "="*50)
        print(" CHUNKS PER DOCUMENT ")
        print("="*50)

        chunks_per_doc = defaultdict(int)
        for doc in ingested_documents:
            doc_id = doc.metadata.get("document_id", "Unknown")
            chunks_per_doc[doc_id] += 1

        for doc_id, count in chunks_per_doc.items():
            print(f"Document: {doc_id} -> {count} chunks")

        print("="*50 + "\n")

        store = get_vector_store()

        data = store.get(include=["metadatas", "documents"])

        print("\n" + "="*50)
        print(" METADATA INDEX VERIFICATION ")
        print("="*50)

        found_x04 = False
        found_g12 = False

        for meta in data["metadatas"]:
            doc_id = meta.get("document_id")
            if doc_id == "X04":
                found_x04 = True
                print(f"[X04] public_access: {meta.get('public_access')} | allowed_roles: {meta.get('allowed_roles')}")
            elif doc_id == "G12":
                found_g12 = True
                print(f"[G12] public_access: {meta.get('public_access')} | allowed_roles: {meta.get('allowed_roles')}")

        if not found_x04:
            print("Warn: No chunks found for document X04.")
        if not found_g12:
            print("Warn: No chunks found for document G12.")

        print("="*50)
        print(" SEARCH TEST WITH SEARCH_DOCUMENTS")
        print("="*50)

        print("\n--- SEARCH AS VISITTOR (roles = []) ---")
        visitor_results = search_documents(query="información general", user_roles=[], store=store)
        for r in visitor_results:
            print(f"  -> Found doc_id: {r.metadata.get('document_id')} (public: {r.metadata.get('public_access')})")

        print("\n--- Búsqueda como RAMÓN ---")
        ramon_roles = [RoleName.RAMON] if hasattr(RoleName, "RAMON") else [] 
        ramon_results = search_documents(query="información confidencial o general", user_roles=ramon_roles, store=store)
        
        x04_leaked = any(r.metadata.get('document_id') == "X04" for r in ramon_results)
        if x04_leaked:
            print("  [ERROR] ¡X04 leaked in Ramón results!")
        else:
            print("  [OK] X04 Didn't appear in Ramón results.")

        print("="*50 + "\n")

    except Exception as e:
        raise e

if __name__ == "__main__":
    main()