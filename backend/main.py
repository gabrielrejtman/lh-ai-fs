from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

try:
    from backend.agents import build_verification_report
except ImportError:
    from agents import build_verification_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOCUMENTS_DIR = Path(__file__).parent / "documents"


def load_documents() -> dict[str, str]:
    documents = {}
    for file_path in DOCUMENTS_DIR.glob("*.txt"):
        documents[file_path.stem] = file_path.read_text(encoding="utf-8")
    return documents


@app.post("/analyze")
async def analyze():
    documents = load_documents()
    report = build_verification_report(documents)
    return {"report": report}
