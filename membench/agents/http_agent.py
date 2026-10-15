"""真实智能体 HTTP 适配器骨架(OpenAI 兼容)。

openKylin 中的 KylinBot / Hermes Agent / kylin-agent / OpenClaw 等真实智能体
通常暴露类 OpenAI 的聊天接口。本模块提供可配置的 HttpAgentAdapter,并给出
KylinBot / Hermes Agent 两个具体骨架。

使用前请按各框架实际接口调整:
- `on_user` 默认 POST {base_url}/chat/completions(OpenAI 兼容)。
- `memory_snapshot` 需读取该框架的记忆存储(向量库/知识库),默认返回空,请覆盖。

配置方式(环境变量或实例化参数):
    MEMBENCH_BASE_URL  服务地址,如 http://127.0.0.1:8000/v1
    MEMBENCH_API_KEY   API 密钥(可选)
    MEMBENCH_MODEL     模型名(可选)
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict, List

from membench.agent import AgentAdapter


class HttpAgentAdapter(AgentAdapter):
    """基于 HTTP 的通用智能体适配器(OpenAI 兼容聊天接口)。"""

    name = "http"
    description = "通用 HTTP(OpenAI 兼容)智能体适配器"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("MEMBENCH_BASE_URL") or "").rstrip("/")
        self.api_key = (
            api_key
            or os.environ.get("MEMBENCH_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        )
        self.model = model or os.environ.get("MEMBENCH_MODEL") or ""
        self.timeout = timeout
        self._history: List[Dict[str, str]] = []

    def reset(self) -> None:
        self._history = []

    def on_user(self, message: str) -> str:
        if not self.base_url:
            raise RuntimeError(
                f"[{self.name}] 未配置 base_url。请设置环境变量 MEMBENCH_BASE_URL,"
                "或实例化时传入 base_url。"
            )
        self._history.append({"role": "user", "content": message})
        payload = {"model": self.model, "messages": list(self._history)}
        data = self._post(f"{self.base_url}/chat/completions", payload)
        try:
            reply = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"[{self.name}] 响应不符合 OpenAI 兼容协议: {exc!r}"
            ) from exc
        self._history.append({"role": "assistant", "content": reply})
        return reply

    def _post(self, url: str, payload: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"[{self.name}] HTTP {exc.code}: {body[:500]}") from exc

    def memory_snapshot(self) -> Dict[str, str]:
        # 真实智能体的记忆存储需按框架读取(向量库/知识库检索),默认空,请覆盖。
        return {}

    def action_trace(self) -> List[str]:
        return []


class KylinBotAdapter(HttpAgentAdapter):
    name = "kylinbot"
    description = "openKylin KylinBot 适配器骨架(OpenAI 兼容,按实际接口调整)"

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", os.environ.get("KYLINBOT_MODEL", "kylinbot"))
        super().__init__(**kwargs)


class HermesAgentAdapter(HttpAgentAdapter):
    name = "hermes_agent"
    description = "openKylin Hermes Agent 适配器骨架(OpenAI 兼容,按实际接口调整)"

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", os.environ.get("HERMES_MODEL", "hermes-agent"))
        super().__init__(**kwargs)
