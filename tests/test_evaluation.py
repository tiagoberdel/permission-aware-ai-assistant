from langchain_core.documents import Document

from app.evaluation.runner import (calculate_metrics, get_unique_document_ids)

def test_get_unique_document_ids_preserves_order():
    documents = [
        Document(page_content="A", metadata={"document_id": "G01"}),
        Document(page_content="B", metadata={"document_id": "G01"}),
        Document(page_content="C", metadata={"document_id": "G03"}),
        Document(page_content="D", metadata={"document_id": "G01"}),
        Document(page_content="E", metadata={"document_id": "G05"}),
    ]

    assert get_unique_document_ids(documents) == [
        "G01",
        "G03",
        "G05",
    ]

def test_calculate_metrics():
    relevant_document_ids = {"G01", "G03", "G05"}
    retrieved_document_ids = ["G08", "G03", "G11", "G01", "G09"]

    calculated_metrics = calculate_metrics(
        relevant_document_ids=relevant_document_ids,
        retrieved_document_ids=retrieved_document_ids,
    )

    assert calculated_metrics["precision_at_k"] == 0.4
    assert calculated_metrics["recall_at_k"] == 2 / 3
    assert calculated_metrics["mrr_at_k"] == 0.5