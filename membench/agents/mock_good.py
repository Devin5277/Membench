"""模拟智能体 —— 记忆能力较强。

用于离线跑通评测流程、验证框架正确性,并与弱智能体形成可区分的对比结果。

其记忆机制(相对"理想"):
- [记住] / [更新] 以键值形式长期保存,[更新] 覆盖旧值(不残留)。
- [模板] 保存为模板,并能在新任务(如"写周报")中复用日报模板。
- [敏感] / [临时] 拒绝长期保存(边界识别正确)。
- 回答时按别名精确命中对应记忆,不串、不漏。
"""
from __future__ import annotations

from typing import Dict, List

from membench.agent import AgentAdapter
from membench.protocol import (
    RE_REMEMBER, RE_UPDATE, RE_SENSITIVE, RE_TEMP, RE_RISK, RE_TEMPLATE, match_alias,
)


class MockGoodAgent(AgentAdapter):
    name = "mock_good"
    description = (
        "记忆能力较强的模拟智能体:正确长期保持、调用、更新、相近区分与边界排除,"
        "并能将模板复用到新任务。"
    )

    def __init__(self) -> None:
        self._entries: Dict[str, str] = {}
        self._trace: List[str] = []

    def reset(self) -> None:
        self._entries.clear()
        self._trace.clear()

    def on_user(self, message: str) -> str:
        m = RE_REMEMBER.match(message)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            self._entries[key] = val
            self._trace.append(f"remember:{key}")
            return f"已记住 {key}"

        m = RE_UPDATE.match(message)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            self._entries[key] = val  # 覆盖旧值
            self._trace.append(f"update:{key}")
            return f"已更新 {key}"

        m = RE_TEMPLATE.match(message)
        if m:
            name, action = m.group(1).strip(), m.group(2).strip()
            self._entries[f"template:{name}"] = action
            self._trace.append(f"remember_template:{name}")
            return f"已记住模板 {name}"

        # 敏感 / 临时 / 风险信息:拒绝长期保存
        if RE_SENSITIVE.match(message) or RE_TEMP.match(message) or RE_RISK.match(message):
            self._trace.append("block_sensitive_or_temp")
            return "该信息涉及敏感、临时或风险内容,我不做长期保留。"

        return self._answer(message)

    def _answer(self, query: str) -> str:
        parts: List[str] = []
        for key, val in self._entries.items():
            if match_alias(key, query):
                parts.append(f"{key}是{val}")

        # 任务复用:query 命中报告/总结/计划等关键词且无精确命中时,复用首个模板
        if not parts and any(w in query for w in ("报", "总结", "计划")):
            for key, val in self._entries.items():
                if key.startswith("template:"):
                    name = key.split(":", 1)[1]
                    parts.append(f"复用{name}模板:{val}")
                    self._trace.append(f"reuse_template:{name}")
                    break

        if not parts:
            return "根据我的记忆,我没有相关记录。"
        return "根据记忆," + ";".join(parts) + "。"

    def memory_snapshot(self) -> Dict[str, str]:
        return dict(self._entries)

    def action_trace(self) -> List[str]:
        return list(self._trace)
