"""byakugan.toml config management."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tomli_w


BYAKUGAN_DIR = ".byakugan"
CONFIG_FILE = "byakugan.toml"
DB_FILE = "byakugan.db"


@dataclass
class ProjectProfile:
    name: str = ""
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    project_types: list[str] = field(default_factory=list)
    test_runner: str | None = None
    package_manager: str | None = None
    linter: str | None = None
    formatter: str | None = None
    type_checker: str | None = None
    python_version: str | None = None
    node_version: str | None = None
    database: str | None = None
    deployment: str | None = None
    context: str | None = None


@dataclass
class ByakuganConfig:
    version: str = "0.3.0"
    initialized_at: str = ""
    last_updated: str | None = None
    active_templates: list[str] = field(default_factory=list)
    project: ProjectProfile = field(default_factory=ProjectProfile)
    superpowers_detected: bool = False
    superpowers_installed_by_byakugan: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ByakuganConfig":
        project_data = data.pop("project", {})
        profile = ProjectProfile(**{
            k: v for k, v in project_data.items()
            if k in ProjectProfile.__dataclass_fields__
        })
        return cls(project=profile, **{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__ and k != "project"
        })

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Strip None from project sub-dict and top-level (tomli_w can't serialize None)
        d["project"] = {k: v for k, v in d["project"].items() if v is not None}
        return {k: v for k, v in d.items() if v is not None}


def find_byakugan_root(start: Path | None = None) -> Path | None:
    """Walk up from start (or cwd) to find the directory containing .byakugan/."""
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / BYAKUGAN_DIR).is_dir():
            return parent
    return None


def get_byakugan_dir(root: Path) -> Path:
    return root / BYAKUGAN_DIR


def get_config_path(root: Path) -> Path:
    return root / BYAKUGAN_DIR / CONFIG_FILE


def get_db_path(root: Path) -> Path:
    return root / BYAKUGAN_DIR / DB_FILE


# Backward compat alias
def get_memory_path(root: Path) -> Path:
    return get_db_path(root)


def load_config(root: Path) -> ByakuganConfig:
    path = get_config_path(root)
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return ByakuganConfig.from_dict(data)


def save_config(config: ByakuganConfig, root: Path) -> None:
    path = get_config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config.to_dict(), f)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
