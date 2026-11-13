import csv
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models import User, UserRole
from app.services.retrieval import retrieve_documents
from app.vector_store.store import get_vector_store

MATRIX_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "andino_dataset"
    / "evaluation"
    / "access_matrix.csv"
)

VISITOR_EMAIL = "visitor@andino.com"


def load_expected_access() -> dict[str, set[str]]:
    with open(MATRIX_PATH, encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    emails = [column for column in rows[0] if "@" in column]

    return {
        email: {row["document_id"] for row in rows if row[email] == "ALLOW"}
        for email in emails
    }


EXPECTED_ACCESS = load_expected_access()


def test_access_matrix_oracle_is_sane():
    assert len(EXPECTED_ACCESS) == 7
    assert EXPECTED_ACCESS[VISITOR_EMAIL] == {"G12"}
    assert all("X04" not in docs for docs in EXPECTED_ACCESS.values())
    assert all("G12" in docs for docs in EXPECTED_ACCESS.values())


@pytest.fixture(scope="module")
def chunk_count() -> int:
    count = len(get_vector_store().get()["ids"])

    if count == 0:
        pytest.skip("The Chroma index is empty. Run: python -m app.ingestion.cli")

    return count


@pytest.mark.integration
@pytest.mark.parametrize("email", list(EXPECTED_ACCESS))
def test_retrievable_documents_match_access_matrix(email, chunk_count):
    with SessionLocal() as db:
        user = db.scalar(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.email == email)
        )
        assert user is not None, f"{email} is not seeded. Run: python -m app.seed"

        documents = retrieve_documents("any query", user, k=chunk_count)

    retrieved = {document.metadata["document_id"] for document in documents}
    expected = EXPECTED_ACCESS[email]

    leaked = retrieved - expected
    missing = expected - retrieved

    assert not leaked, f"SECURITY LEAK for {email}: retrieved {sorted(leaked)}"
    assert not missing, (
        f"Index incomplete or wrong permissions for {email}: "
        f"missing {sorted(missing)}"
    )
