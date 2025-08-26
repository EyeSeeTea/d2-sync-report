import subprocess
import tempfile
import shutil
import os
from typing import Optional


class DockerSyncTemporalFolder:
    temp_dir: Optional[str]

    def __init__(self, container_name: str, container_source_folder: str):
        self.container_name = container_name
        self.container_source_folder = container_source_folder
        self.temp_dir = None

    def __enter__(self) -> str:
        self.temp_dir = tempfile.mkdtemp()
        command = [
            "docker",
            "cp",
            f"{self.container_name}:{self.container_source_folder}/.",
            self.temp_dir,
        ]

        subprocess.run(command, check=True)
        print(f"Copied: {self.container_name}:{self.container_source_folder} to {self.temp_dir}")

        return self.temp_dir

    def __exit__(
        self,
        _exc_type: Optional[type],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[object],
    ) -> None:
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up temporary directory {self.temp_dir}")
