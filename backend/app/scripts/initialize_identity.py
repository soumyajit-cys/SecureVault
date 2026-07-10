from sqlalchemy.orm import Session

from app.domain.models.permission import Permission
from app.domain.models.role import Role

from app.scripts.seed_permissions import (
    PERMISSIONS,
)
from app.scripts.seed_roles import (
    ROLES,
)


def seed_permissions(
    db: Session,
):
    for permission_name in PERMISSIONS:

        existing = (
            db.query(Permission)
            .filter(
                Permission.name
                == permission_name
            )
            .first()
        )

        if existing:
            continue

        db.add(
            Permission(
                name=permission_name
            )
        )

    db.commit()


def seed_roles(
    db: Session,
):
    for role_name in ROLES.keys():

        existing = (
            db.query(Role)
            .filter(
                Role.name == role_name
            )
            .first()
        )

        if existing:
            continue

        db.add(
            Role(
                name=role_name
            )
        )

    db.commit()