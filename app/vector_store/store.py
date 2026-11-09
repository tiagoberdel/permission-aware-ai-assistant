from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.roles import RoleName
from app.embeddings.embeddings import get_embeddings

def get_vector_store():
    return Chroma(
        collection_name="andino-docs",
        embedding_function=get_embeddings(),
        persist_directory="./andino_db"
    )

def index_documents(documents: list[Document]) -> None:
    vector_store = get_vector_store()
    vector_store.add_documents(documents)

def search_documents(
    query: str,
    user_roles: list[RoleName],
    k: int = 5
) -> list[Document]:

    if not user_roles:
        return []

    vector_store = get_vector_store()

    return vector_store.similarity_search(
        query,
        k=k,
        filter={
            "$or": [
                {"allowed_roles": {"$contains": role.value}}
                for role in user_roles
            ]
        }
    )