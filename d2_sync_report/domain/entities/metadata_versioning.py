from dataclasses import dataclass


@dataclass
class MetadataVersioning:
    local: str
    remote: str
