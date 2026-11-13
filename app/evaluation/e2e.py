import json


def _tool_content_to_texts(content) -> list[str]:
    if isinstance(content, str):
        return [content]

    texts = []

    for block in content:
        if isinstance(block, str):
            texts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            texts.append(block["text"])

    return texts


def extract_retrieved_documents(messages) -> list[dict]:
    documents: list[dict] = []

    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue

        if getattr(message, "status", "success") == "error":
            continue

        for text in _tool_content_to_texts(message.content):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Tool message content is not valid JSON: {text[:200]!r}"
                ) from exc

            if isinstance(parsed, list):
                documents.extend(parsed)
            elif isinstance(parsed, dict):
                documents.append(parsed)

    return documents


def get_retrieved_document_ids(messages) -> list[str]:
    ids: list[str] = []

    for document in extract_retrieved_documents(messages):
        document_id = document["document_id"]

        if document_id not in ids:
            ids.append(document_id)

    return ids