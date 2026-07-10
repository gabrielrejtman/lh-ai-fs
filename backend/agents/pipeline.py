from typing import Any
from .orchestrator import Orchestrator
from .schemas import PromptConfig


def build_verification_report(documents: dict[str, str], prompt_config: PromptConfig | None = None) -> dict[str, Any]:
    orchestrator = Orchestrator(prompt_config=prompt_config)
    return orchestrator.run(documents)
