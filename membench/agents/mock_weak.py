"""模拟智能体 —— 记忆能力较弱。

用于演示评测框架如何"区分"不同记忆能力的智能体。其缺陷是刻意的、确定性的,
对应六项能力逐项暴露问题:

- 长期保持/记忆调用:只保留最近一条稳定事实(工作记忆单槽),较早信息被遗忘。
- 动态更新:[更新] 追加而非覆盖,旧值残留(如 "北京 / 上海")。
- 相近区分:把含"密码/路径"的键归一化为粗粒度键,相似信息互相覆盖、混淆。
- 边界识别:[敏感] / [临时] 信息照单全收并持续保留(越界记忆)。
- 任务复用:无模板复用逻辑。
"""
from __future__ import annotations

from typing import Dict, List

from membench.agent import AgentAdapter
from membench.protocol import (
    RE_REMEMBER, RE_UPDATE, RE_SENSITIVE, RE_TEMP, RE_RISK, RE_TEMPLATE, match_alias,
)


def _coarse_key(key: str) -> str:
    """把相似信息归一化为粗粒度键(相近区分的缺陷来源)。"""
    if "password" in key:
        return "password"
    if "path" in key:
        return "path"
    return key


class MockWeakAgent(AgentAdapter):
    name = "mock_weak"
    description = (
        "记忆能力较弱的模拟智能体:易遗忘、不覆盖更新、混淆相似信息、"
        "越界记忆敏感/临时信息、不复用模板。"
    )

    def __init__(self) -> None:
        self._stable: Dict[str, str] = {}    # 稳定事实(仅保留最近一条)
        self._unsafe: Dict[str, str] = {}    # 敏感/临时信息(照单全收)
        self._trace: List[str] = []

    def reset(self) -> None:
        self._stable.clear()
        self._unsafe.clear()
        self._trace.clear()

    def on_user(self, message: str) -> str:
        m = RE_REMEMBER.match(message)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            self._stable = {_coarse_key(key): val}  # 单槽:仅保留最近一条
            self._trace.append(f"remember:{key}")
            return f"已记住 {key}"

        m = RE_UPDATE.match(message)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            ck = _coarse_key(key)
            old = self._stable.get(ck, "")
            self._stable = {ck: f"{old} / {val}".strip(" /")}  # 追加而非覆盖
            self._trace.append(f"update:{key}")
            return f"已更新 {key}"

        m = RE_TEMPLATE.match(message)
        if m:
            name, action = m.group(1).strip(), m.group(2).strip()
            self._stable = {f"template:{name}": action}  # 与稳定事实共用单槽
            self._trace.append(f"remember_template:{name}")
            return f"已记住模板 {name}"

        m = RE_SENSITIVE.match(message) or RE_TEMP.match(message) or RE_RISK.match(message)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            self._unsafe[key] = val  # 越界:照单全收
            self._trace.append(f"unsafe_store:{key}")
            return f"已记录 {key}"

        return self._answer(message)

    def _answer(self, query: str) -> str:
        parts: List[str] = []
        for key, val in {**self._stable, **self._unsafe}.items():
            if match_alias(key, query):
                parts.append(f"{key}是{val}")

        if not parts:
            return "根据我的记忆,我没有相关记录。"
        return "根据记忆," + ";".join(parts) + "。"

    def memory_snapshot(self) -> Dict[str, str]:
        return {**self._stable, **self._unsafe}

    def action_trace(self) -> List[str]:
        return list(self._trace)
