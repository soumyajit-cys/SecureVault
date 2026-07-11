from fastapi import Depends

from sqlalchemy.orm import Session

from app.api.dependencies.database import (
    get_db,
)

from app.core.unit_of_work import (
    UnitOfWork,
)


def get_uow(
    db: Session = Depends(
        get_db
    ),
):
    return UnitOfWork(db)