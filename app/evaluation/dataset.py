import json
from pathlib import Path
from typing import Any

DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "andino_dataset"
    / "evaluation"
    / "questions.json"
)

def load_questions() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Questions dataset must be a JSON list")

    return data

def get_relevant_document_ids(
    question: dict[str, Any],
) -> set[str]:
    document_ids = {question["target_doc_id"]}

    document_ids.update(
        question.get("supporting_doc_ids", [])
    )

    return document_ids

def get_authorized_cases(
    questions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if questions is None:
        questions = load_questions()

    cases = []

    for question in questions:
        if question["type"] != "authorized":
            continue

        relevant_ids = get_relevant_document_ids(question)

        for language in ("es", "en"):
            cases.append({
                "question_id": question["id"],
                "asker": question["asker"],
                "language": language,
                "query": question[f"question_{language}"],
                "relevant_document_ids": relevant_ids,
            })

    return cases