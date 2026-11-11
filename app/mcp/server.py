from fastmcp import FastMCP

from app.models.user import User
from app.services.retrieval import retrieve_documents

def create_mcp_server(user: User) -> FastMCP:
    mcp = FastMCP(name="andino")

    @mcp.tool
    def search_internal_documents(query: str):
        """
        Search Andino's internal company documents to find information relevant to the user's question.
        Only return documents the authenticated user is authorized to access.
        """

        retrieved_documents = retrieve_documents(
                query=query,
                user=user
            )

        documents = []

        for document in retrieved_documents:
            doc = {
                "document_id": document.metadata["document_id"],
                "title": document.metadata["title"],
                "content": document.page_content,
                "language": document.metadata["language"],
            }
            documents.append(doc)

        return documents

    return mcp
