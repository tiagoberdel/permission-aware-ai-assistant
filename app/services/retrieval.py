from langchain_core.documents import Document

from app.models.user import User
from app.roles import RoleName
from app.vector_store.store import search_documents


def retrieve_documents(
    query: str,
    user: User,
    k: int = 5,
) -> list[Document]:
    user_roles = [
        RoleName(user_role.role.name)
        for user_role in user.roles
    ]

    return search_documents(
        query=query,
        user_roles=user_roles,
        k=k,
    )