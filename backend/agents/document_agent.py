from typing import Any


class DocumentAgent:
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt

    def run(self, documents: dict[str, str]) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        for name, text in documents.items():
            normalized[name] = {
                "name": name,
                "text": text,
                "word_count": len(text.split()),
            }
        return normalized
