from sqlalchemy import select

from app.models.role import Role
from app.roles import ROLE_DESCRIPTIONS
from app.seed import seed_roles

def test_seed_roles_creates_all_roles(db_session):
    seed_roles(db_session)

    roles = db_session.scalars(select(Role)).all()

    expected_names = {
        role_name.value
        for role_name in ROLE_DESCRIPTIONS
    }

    actual_names = {
        role.name
        for role in roles
    }

    assert actual_names == expected_names

    for role in roles:
        role_name = next(
            name
            for name in ROLE_DESCRIPTIONS
            if name.value == role.name
        )

        assert role.description == ROLE_DESCRIPTIONS[role_name]


def test_seed_roles_is_idempotent(db_session):
    seed_roles(db_session)
    seed_roles(db_session)

    roles = db_session.scalars(select(Role)).all()

    assert len(roles) == len(ROLE_DESCRIPTIONS)