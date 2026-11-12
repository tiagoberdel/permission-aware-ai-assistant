import json
from pathlib import Path
from langchain_core.documents import Document

from app.evaluation.database import get_user_roles
from app.evaluation.dataset import get_authorized_cases
from app.vector_store.store import search_documents, get_vector_store

def run_retrieval_evaluation():
    authorized_cases = get_authorized_cases()
    vector_store = get_vector_store()

    results = []

    for case in authorized_cases:
        roles = get_user_roles(case["asker"])
        search_results = search_documents(
            query=case["query"],
            user_roles=roles,
            store=vector_store,
            k=20
        )
        retrieved_document_ids = get_unique_document_ids(search_results)[:5]

        relevant_ids = set(case["relevant_document_ids"])

        metrics = calculate_metrics(
            relevant_document_ids=relevant_ids, 
            retrieved_document_ids=retrieved_document_ids, 
            k=5
        )
        
        results.append({
            "case": case,
            "retrieved_documents": search_results,
            "retrieved_document_ids": retrieved_document_ids,
            "metrics": metrics
        })

    total_cases = len(results)
    if total_cases == 0:
        raise ValueError("No authorized evaluation cases found.")

    avg_precision = sum(r["metrics"]["precision_at_k"] for r in results) / total_cases
    avg_recall = sum(r["metrics"]["recall_at_k"] for r in results) / total_cases
    avg_mrr = sum(r["metrics"]["mrr_at_k"] for r in results) / total_cases

    baseline_metrics = {
        "precision": avg_precision,
        "recall": avg_recall,
        "mrr": avg_mrr,
        "total_cases_evaluated": total_cases,
        "cases": [
            {
                "question_id": result["case"]["question_id"],
                "asker": result["case"]["asker"],
                "language": result["case"]["language"],
                "query": result["case"]["query"],
                "relevant_document_ids": sorted(
                    result["case"]["relevant_document_ids"]
                ),
                "retrieved_document_ids": result["retrieved_document_ids"],
                "metrics": result["metrics"],
            }
            for result in results
        ],
    }

    return baseline_metrics

def get_unique_document_ids(documents: list[Document]) -> list[str]:
    unique_ids = []
    seen_ids = set()

    for document in documents:
        document_id = document.metadata["document_id"]

        if document_id not in seen_ids:
            seen_ids.add(document_id)
            unique_ids.append(document_id)

    return unique_ids

def calculate_metrics(
        relevant_document_ids: set[str],
        retrieved_document_ids: list[str],
        k: int = 5,
) -> dict:
    if not relevant_document_ids:
        raise ValueError("relevant document ids cannot be empty")

    if k <= 0:
        raise ValueError("k must be greater than zero")

    relevant_retrieved = len(set(retrieved_document_ids[:k]) & relevant_document_ids)

    precision_at_k = relevant_retrieved / k
    recall_at_k = relevant_retrieved / len(relevant_document_ids)

    mrr_at_k = 0.0
    for position, document_id in enumerate(retrieved_document_ids[:k], start=1):
        if document_id in relevant_document_ids:
            mrr_at_k = 1 / position
            break

    return {
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "mrr_at_k": mrr_at_k,
    }

if __name__ == "__main__":
    metrics = run_retrieval_evaluation()

    print("\n" + "="*50)
    print(" RETRIEVAL EVALUATION BASELINE ")
    print("="*50)
    print(f"Precision@5: {metrics['precision']:.4f}")
    print(f"Recall@5:    {metrics['recall']:.4f}")
    print(f"MRR@5:       {metrics['mrr']:.4f}")
    print(f"Evaluated cases: {metrics['total_cases_evaluated']}")
    print("="*50 + "\n")

    baseline_path = Path(__file__).resolve().parent.parent.parent / "data" / "retrieval_baseline.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
    
    print(f"Baseline successfully saved to: {baseline_path}")