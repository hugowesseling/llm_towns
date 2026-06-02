from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Union

import requests


DEFAULT_OPENAI_BASE = "http://192.168.1.117:8080/v1"
DEFAULT_MODEL = "models/Qwen_Qwen3.6-35B-A3B-Q2_K_L.gguf"
DEFAULT_TIMEOUT = 60


class OpenAIChatClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        organization: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_API_BASE", DEFAULT_OPENAI_BASE)
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        self.organization = organization or os.getenv("OPENAI_ORGANIZATION")

        if not self.api_key:
            self.api_key = "none"

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers

    def _endpoint(self, path: str) -> str:
        return self.base_url.rstrip("/") + "/" + path.lstrip("/")

    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop is not None:
            payload["stop"] = stop
        payload.update(kwargs)

        print(f"\n[LLM] >>> {json.dumps(payload, indent=2)}")
        response = requests.post(
            self._endpoint("chat/completions"),
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        reply = self.get_message_text(result)
        print(f"[LLM] <<< {reply}\n")
        return result

    def create_text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop is not None:
            payload["stop"] = stop
        payload.update(kwargs)

        print(f"\n[LLM] >>> {json.dumps(payload, indent=2)}")
        response = requests.post(
            self._endpoint("completions"),
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        print(f"[LLM] <<< {self.get_text(result)}\n")
        return result

    def get_message_text(self, completion: Dict[str, Any]) -> str:
        choices = completion.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if not content:
            content = message.get("reasoning_content", "")
        return content.strip()

    def get_text(self, completion: Dict[str, Any]) -> str:
        choices = completion.get("choices", [])
        if not choices:
            return ""
        text = choices[0].get("text") or ""
        return text

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        print(f"\n[LLM JSON >>>] system={messages[0]['content'][:60] if messages else 'N/A'}")
        print(f"[LLM JSON >>>] user={messages[-1]['content'][:60] if len(messages) > 1 else 'N/A'}...")
        completion = self.create_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        raw_text = self.get_message_text(completion)
        print(f"[LLM JSON <<<] raw={repr(raw_text[:300])}\n")
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            raise ValueError(f"LLM response is not valid JSON: {raw_text[:300]}")


class LLMBrain:
    def __init__(self, client: OpenAIChatClient) -> None:
        self.client = client

    def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        completion = self.client.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return self.client.get_message_text(completion)

    def chat_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self.client.chat_json(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def create_chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        return self.client.chat_json(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def generate_goal(self, system: str, user: str, **kwargs: Any) -> str:
        return self.chat(
            system=system,
            user=user,
            **kwargs,
        )

    def generate_goal_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self.create_chat_json(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def generate_plan(self, system: str, user: str, **kwargs: Any) -> str:
        return self.chat(
            system=system,
            user=user,
            **kwargs,
        )

    def generate_plan_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self.create_chat_json(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
