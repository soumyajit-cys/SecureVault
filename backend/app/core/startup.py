from sqlalchemy.orm import Session

from app.core.database import (
    SessionLocal,
)

from app.scripts.initialize_identity import (
    seed_permissions,
    seed_roles,
)


def initialize_security_data():

    db: Session = SessionLocal()

    try:
        seed_permissions(db)
        seed_roles(db)
    finally:
        db.close()

        