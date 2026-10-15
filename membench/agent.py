"""智能体适配层:定义统一的 AgentAdapter 接口,便于接入真实智能体。

任何真实智能体(KylinBot / Hermes Agent / kylin-agent / OpenClaw 等)
只要实现本接口,即可被评测框架驱动与评分,无需改动评测逻辑本身。

接口约定的四个方法对应评测框架的四个交互阶段:
    1. reset()            —— 清空状态,开始一个评测单元。
    2. on_user(message)   —— 处理一条用户消息(播种或探针),返回智能体回复。
    3. memory_snapshot()  —— 返回智能体当前"可回忆"的记忆(键 -> 值)。
                            边界识别评分依赖于此:敏感/临时信息若出现在这里,
                            即判为"不该记却记了"。
    4. action_trace()     —— 返回行动轨迹(任务复用证据)。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class AgentAdapter(ABC):
    """智能体适配器抽象基类。"""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def reset(self) -> None:
        """清空内部状态,准备开始一个新的评测单元。"""

    @abstractmethod
    def on_user(self, message: str) -> str:
        """处理一条用户消息,返回智能体回复。"""

    def memory_snapshot(self) -> Dict[str, str]:
        """返回智能体当前可被回忆的记忆(键 -> 值)。默认无记忆。"""
        return {}

    def action_trace(self) -> List[str]:
        """返回智能体的行动轨迹(任务复用证据)。默认空。"""
        return []
