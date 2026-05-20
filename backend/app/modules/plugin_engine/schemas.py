from pydantic import BaseModel, Field
from typing import List, Optional

class PluginManifest(BaseModel):
    name: str
    version: str
    type: str  # e.g., 'wasm', 'python', 'python_native', 'pyo3'
    url: str
    sha256: str
    is_official: bool = False
    permissions: List[str] = Field(default_factory=list)
