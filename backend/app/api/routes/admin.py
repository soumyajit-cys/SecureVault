from fastapi import APIRouter
from fastapi import Depends

from app.api.dependencies.rbac import (
    require_role,
)

from app.api.dependencies.storage import (
    get_garbage_collector,
    get_storage_service,
)

from app.schemas.admin import (
    GarbageCollectionResult,
    StorageUsageResponse,
)

from app.services.storage.garbage_collector import (
    GarbageCollector,
)

from app.services.storage.storage_service import (
    StorageService,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/status")
def admin_status(
    user=Depends(
        require_role(
            "Admin"
        )
    ),
):
    return {
        "status": "ok"
    }


@router.get(
    "/storage",
    response_model=StorageUsageResponse,
)
def storage_usage(
    user=Depends(
        require_role(
            "Admin"
        )
    ),
    storage: StorageService = Depends(
        get_storage_service
    ),
):

    containers = list(
        storage.iter_containers()
    )

    return StorageUsageResponse(
        storage_bytes=sum(
            c.stat().st_size
            for c in containers
        ),
        stored_file_count=len(
            containers
        ),
        temp_file_count=sum(
            1
            for t in storage.temp_dir.iterdir()
            if t.is_file()
        ),
    )


@router.post(
    "/garbage-collect",
    response_model=GarbageCollectionResult,
)
def garbage_collect(
    user=Depends(
        require_role(
            "Admin"
        )
    ),
    collector: GarbageCollector = Depends(
        get_garbage_collector
    ),
):

    summary = collector.run_all()

    return GarbageCollectionResult(
        orphaned_containers=summary["orphaned_containers"],
        missing_records=summary["missing_records"],
        purged_deleted=summary["purged_deleted"],
        temp_files=summary["temp_files"],
    )