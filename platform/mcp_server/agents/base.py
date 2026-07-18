"""Shared contract for every specialist agent.

Hard rule enforced by convention across every subclass: `.respond()` must call
at least one grounded tool from `mcp_server/tools/` and build its answer only
from that tool's return value. No subclass may format a number it did not
receive from a tool call — that is what makes the chat safe to demo live.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    answer: str
    sources: list[str] = field(default_factory=list)


class Agent(ABC):
    name: str

    @abstractmethod
    def respond(self, question: str) -> AgentResponse:
        ...
