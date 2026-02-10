from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMBackend(ABC):
    @abstractmethod
    def ensure_model(self, model: str) -> None:
        pass

    @abstractmethod
    def run_prompt(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None,
        temperature: float | None,
        options: dict | None,
        stream: bool,
    ) -> Dict[str, Any]:
        """
        Must return:
        {
            "text": str,
            "stats": dict,
            "wall_time_s": float,
        }
        """

