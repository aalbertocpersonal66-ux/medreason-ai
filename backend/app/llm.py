"""Adaptador híbrido. La fuente de verdad clínica sigue siendo el guion validado."""
import os
from typing import Protocol

class LLMProvider(Protocol):
    async def generate(self, system: str, user: str) -> str: ...

class DisabledLLM:
    async def generate(self, system: str, user: str) -> str:
        raise RuntimeError("LLM no configurado")

class OpenAICompatibleLLM:
    """Adaptador opcional compatible con API de chat completions."""
    def __init__(self):
        self.api_key=os.getenv("LLM_API_KEY", "")
        self.base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model=os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def generate(self, system: str, user: str) -> str:
        if not self.api_key:
            raise RuntimeError("Falta LLM_API_KEY")
        import httpx
        async with httpx.AsyncClient(timeout=25) as client:
            r=await client.post(self.base_url.rstrip('/')+'/chat/completions',
                headers={"Authorization":f"Bearer {self.api_key}"},
                json={"model":self.model,"temperature":0.2,"messages":[
                    {"role":"system","content":system},{"role":"user","content":user}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

def get_llm():
    if os.getenv("LLM_API_KEY"):
        return OpenAICompatibleLLM()
    return DisabledLLM()
