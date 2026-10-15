"""模拟智能体 —— 中间档(拟真)。

用于在"强(mock_good)/ 弱(mock_weak)"两极之间,提供一个更接近真实大模型智能体的
参照档。它的记忆本身基本正确(像 mock_good 一样长期保存、覆盖更新、复用模板),
但刻意引入了两类真实 LLM 常见的、确定性的瑕疵:

1. 措辞简化(转述不精确):
   回答时对"复合长值"(带前缀的偏好、路径、地址、密码等)做省略改写,只复述前半,
   导致精确关键词命中率下降;短值(如姓名)则能完整复述。这对应真实 LLM"记对了、
   但表达时改写措辞"的现象。

2. 临时信息误记(越界记忆):
   把 [临时] 信息当作长期记忆保留(真实 LLM 常因"看似有用"而过度保留),
   而 [敏感] / [风险] 仍能正确排除。这对应真实 LLM 在边界识别上的部分失分。

结果:总分落在强 / 弱之间(约 80 分档),且六维呈现"有强有弱"的真实 profile,
而不是均匀的中间值。
"""
from __future__ import annotations

from typing import Dict, List

from membench.agent import AgentAdapter
from membench.protocol import (
    RE_REMEMBER, RE_UPDATE, RE_SENSITIVE, RE_TEMP, RE_RISK, RE_TEMPLATE, match_alias,
)


def _abbreviate(value: str) -> str:
    """模拟真实 LLM 转述时的措辞简化。

    - 含 "/" 的路径:只保留前两段(如 /opt/openkylin/... -> /opt)。
    - 超过 3 个字符的复合值:只复述前 3 字(如 "喜欢喝美式咖啡" -> "喜欢喝")。
    - 短值(<= 3 字,如姓名):完整复述。
    """
    if "/" in value:
        parts = value.split("/")
        if len(parts) > 2:
            return "/".join(parts[:2])
        return value
    return value if len(value) <= 3 else value[:3]


class MockTypicalAgent(AgentAdapter):
    name = "mock_typical"
    description = (
        "中间档拟真智能体:记忆基本正确,但转述时措辞简化(长值省略)、"
        "并会把临时信息误记为长期记忆,更接近真实 LLM 的常见瑕疵。"
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

        # 瑕疵 2:临时信息被当作长期记忆保留(越界记忆)
        m = RE_TEMP.match(message)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            self._entries[key] = val
            self._trace.append(f"remember_temp:{key}")
            return f"已记录 {key}"

        # 敏感 / 风险信息:仍能正确拒绝长期保存
        if RE_SENSITIVE.match(message) or RE_RISK.match(message):
            self._trace.append("block_sensitive_or_risk")
            return "该信息涉及敏感或风险内容,我不做长期保留。"

        return self._answer(message)

    def _answer(self, query: str) -> str:
        parts: List[str] = []
        for key, val in self._entries.items():
            if match_alias(key, query):
                # 瑕疵 1:事实值在转述时被措辞简化,精确关键词命中率下降
                parts.append(f"{key}是{_abbreviate(val)}")

        # 任务复用:命中报告/总结/计划等关键词且无精确命中时,复用首个模板(按原文)
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
