"""Canonical request/response models — protocol-agnostic intermediate format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentRequest:
    """Protocol-agnostic agent request (intermediate representation)."""

    route: str
    message: str
    context: list[dict[str, str]] = field(default_factory=list)  # conversation history
    tool_choice: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    source_protocol: str = "unknown"


@dataclass
class ToolResult:
    """A tool call result."""

    name: str
    arguments: dict[str, Any]
    result: Any = None
    error: str | None = None


@dataclass
class AgentResponse:
    """Protocol-agnostic agent response (intermediate representation)."""

    content: str = ""
    tool_calls: list[ToolResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "completed"  # "completed", "in_progress", "failed"
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == "completed" and self.error is None
