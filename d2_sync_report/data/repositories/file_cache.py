import os.path
from typing import Generic, Optional, Type, TypeVar

from pydantic import BaseModel


Props = TypeVar("Props", bound=BaseModel)


class FileCache(Generic[Props]):
    def __init__(self, props_class: Type[Props], filename: str):
        self.props_class = props_class
        self.filename = filename

    def save(self, props: Props) -> None:
        cache_path = self._get_cache_path()
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(props.model_dump_json(indent=4) + "\n")

        print(f"Cache saved: {cache_path}")

    def load(self) -> Optional[Props]:
        cache_path = self._get_cache_path()

        if os.path.exists(cache_path):
            print(f"Cache loaded: {cache_path}")
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = f.read()
                cache_props = self.props_class.model_validate_json(data)
                print(f"Cache: {cache_props}")
                return cache_props
            except ValueError as exc:
                print(f"Cache load error: {exc}")
                os.remove(cache_path)
                return None
        else:
            print(f"Cache file does not exist: {cache_path}")
            return None

    def _get_cache_path(self) -> str:
        script_folder = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(script_folder, self.filename)
