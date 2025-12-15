from typing import Any


try:
    from langchain_community.chat_models import ChatOllama
except Exception:  # pragma: no cover
    ChatOllama = None


from langchain_core.messages import HumanMessage, SystemMessage


class LLM:
    def __init__(self, provider: str = "ollama", model: str = "llama3.1:8b-instruct"):
        self.provider = provider
        self.model = model
        if provider == "ollama":
            if ChatOllama is None:
                raise RuntimeError("LangChain Ollama not installed")
            self.llm = ChatOllama(model=model, temperature=0.2)
        else:
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(model=model, temperature=0.2)

    def ask(self, system: str, user: str) -> str:
        msgs = [SystemMessage(content=system), HumanMessage(content=user)]
        return self.llm.invoke(msgs).content
