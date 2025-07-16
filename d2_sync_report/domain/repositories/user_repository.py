from abc import ABC, abstractmethod
from typing import List, Optional

from d2_sync_report.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    def get_list_by_group(
        self, name: Optional[str] = None, code: Optional[str] = None
    ) -> List[User]:
        """Get users by group code"""
        pass
