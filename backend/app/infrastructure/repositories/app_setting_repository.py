from sqlalchemy import select

from app.domain.models.app_setting import AppSetting
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyAppSettingRepository(
    SQLAlchemyRepository[AppSetting]
):
    model = AppSetting

    def get(
        self,
        key: str,
    ) -> AppSetting | None:

        stmt = (
            select(AppSetting)
            .where(
                AppSetting.key == key
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def set(
        self,
        key: str,
        value: str,
    ) -> AppSetting:

        setting = self.get(key)

        if setting is None:

            setting = AppSetting(
                key=key,
                value=value,
            )

            self.db.add(setting)

        else:

            setting.value = value

        self.db.flush()

        return setting
