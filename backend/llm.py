# backend/llm.py
import os
from typing import Type, TypeVar
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

T = TypeVar("T", bound=BaseModel)

def call_llm_structured(
    messages: list[dict],
    response_model: Type[T],
    model: str = "gpt-4o-mini",
    temperature: float = 0,
) -> T:
    """
    Calls OpenAI while enforcing a strict Pydantic schema output.
    """
    response = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format=response_model,
    )
    
    return response.choices[0].message.parsed