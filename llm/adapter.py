from typing import Any, Protocol

from openai import OpenAI


class LLMAdapter(Protocol):
    """Manager / AgentRuntime 依赖的最小模型接口。"""

    def set_user_template(self, template: str) -> None:
        ...

    def chat(self, messages: list, stream: bool, **kwargs: Any):
        ...


class DeepSeekAdapter:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "deepseek-chat",
        thinking: bool = False,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.thinking = thinking
        self.user_template = ""

    def set_user_template(self, template: str) -> None:
        self.user_template = template

    def chat(
        self,
        messages: list,
        stream: bool,
        response_format: dict | None = None,
        **kwargs: Any,
    ):
        try:
            create_kwargs = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                **kwargs,
            }
            if response_format is not None:
                create_kwargs["response_format"] = response_format
            return self.client.chat.completions.create(**create_kwargs)
        except Exception as exc:
            print(f"DeepSeek chat error: {type(exc).__name__}: {exc}")
            return None


class OpenAICompatibleAdapter:
    def __init__(
        self,
        api_key: str = "EMPTY",
        base_url: str = "http://localhost:11434/v1",
        model: str = "qwen3.5:2b",
    ) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.user_template = ""

    def set_user_template(self, template: str) -> None:
        self.user_template = template

    def chat(self, messages: list, stream: bool = False, **kwargs: Any):
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                **kwargs,
            )
        except Exception as exc:
            print(f"OpenAI-compatible chat error: {type(exc).__name__}: {exc}")
            return None


class LLMAdapterFactory:
    adapters = {
        "deepseek": DeepSeekAdapter,
        "openai-compatible": OpenAICompatibleAdapter,
    }

    @classmethod
    def create_adapter(cls, provider: str, **kwargs: Any):
        adapter_class = cls.adapters.get(provider)
        if adapter_class is None:
            raise ValueError(f"不支持的模型供应商: {provider}")
        return adapter_class(**kwargs)
