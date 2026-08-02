from sqlalchemy.orm import Session

from app.core.database import (
    SessionLocal,
)

from app.scripts.initialize_identity import (
    seed_permissions,
    seed_role_permissions,
    seed_roles,
)
from app.scripts.bootstrap_admin import (
    seed_bootstrap_admin,
)


def initialize_security_data():

    db: Session = SessionLocal()

    try:
        seed_permissions(db)
        seed_roles(db)
        seed_role_permissions(db)
        seed_bootstrap_admin(db)
    finally:
        db.close()