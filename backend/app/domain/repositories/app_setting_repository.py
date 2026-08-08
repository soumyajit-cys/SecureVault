from abc import abstractmethod

from app.domain.models.app_setting import AppSetting
from app.domain.repositories.base import Repository


class AppSettingRepository(Repository[AppSetting]):

    @abstractmethod
    def get(
        self,
        key: str,
    ) -> AppSetting | None:
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: str,
    ) -> AppSetting:
        pass
