from dataclasses import dataclass, field


@dataclass
class PromptConfig:
    overrides: dict[str, str] = field(default_factory=dict)

    def get(self, name: str, default: str) -> str:
        return self.overrides.get(name, default)
