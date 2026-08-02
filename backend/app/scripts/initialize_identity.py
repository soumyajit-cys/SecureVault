from sqlalchemy.orm import Session

from app.domain.models.permission import Permission
from app.domain.models.role import Role
from app.domain.models.role_permission import (
    RolePermission
)

from app.scripts.seed_permissions import (
    PERMISSIONS,
)
from app.scripts.seed_roles import (
    ROLES,
)


def seed_role_permissions(
    db: Session,
):
    """
    Link roles to permissions based on the ROLES mapping.

    A `"*"` entry grants every known permission (used by Admin).
    """

    for role_name, permission_names in ROLES.items():

        role = (
            db.query(Role)
            .filter(Role.name == role_name)
            .first()
        )

        if not role:
            continue

        if "*" in permission_names:
            permission_names = PERMISSIONS

        for permission_name in permission_names:

            permission = (
                db.query(Permission)
                .filter(
                    Permission.name
                    == permission_name
                )
                .first()
            )

            if not permission:
                continue

            existing = (
                db.query(RolePermission)
                .filter(
                    RolePermission.role_id
                    == role.id,
                    RolePermission.permission_id
                    == permission.id,
                )
                .first()
            )

            if existing:
                continue

            db.add(
                RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
            )

    db.commit()


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