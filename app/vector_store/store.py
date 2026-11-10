
from collections import defaultdict

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.roles import RoleName
from app.embeddings.embeddings import get_embeddings


def get_vector_store() -> Chroma:
    return Chroma(
        collection_name="andino-docs",
        embedding_function=get_embeddings(),
        persist_directory="./andino_db",
    )


def index_documents(documents: list[Document]) -> None:
    vector_store = get_vector_store()

    indexed_documents = []

    for document in documents:
        metadata = {
            key: value
            for key, value in document.metadata.items()
            if key not in {"dl_meta", "source"}
        }

        indexed_documents.append(
            Document(
                page_content=document.page_content,
                metadata=metadata,
            )
        )

    chunk_counters = defaultdict(int)
    ids = []

    for document in indexed_documents:
        key = (
            document.metadata["document_id"],
            document.metadata["language"],
            document.metadata["source_path"],
        )

        chunk_index = chunk_counters[key]
        chunk_counters[key] += 1

        ids.append(f"{key[0]}_{key[1]}_{chunk_index}")

    vector_store.add_documents(
        documents=indexed_documents,
        ids=ids,
    )


def search_documents(
    query: str,
    user_roles: list[RoleName],
    k: int = 5,
) -> list[Document]:
    vector_store = get_vector_store()

    access_conditions = [{"public_access": True}]

    access_conditions.extend(
        {"allowed_roles": {"$contains": role.value}}
        for role in user_roles
    )

    access_filter = (
        access_conditions[0]
        if len(access_conditions) == 1
        else {"$or": access_conditions}
    )

    return vector_store.similarity_search(
        query,
        k=k,
        filter=access_filter,
    )
