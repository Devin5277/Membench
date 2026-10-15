"""智能体注册表。

新增智能体:实现 AgentAdapter 接口,在此登记到 REGISTRY 即可被 CLI 识别。
"""
from __future__ import annotations

from typing import Dict, Type

from membench.agent import AgentAdapter
from membench.agents.mock_good import MockGoodAgent
from membench.agents.mock_typical import MockTypicalAgent
from membench.agents.mock_weak import MockWeakAgent
from membench.agents.http_agent import KylinBotAdapter, HermesAgentAdapter

REGISTRY: Dict[str, Type[AgentAdapter]] = {
    "mock_good": MockGoodAgent,
    "mock_typical": MockTypicalAgent,
    "mock_weak": MockWeakAgent,
    "kylinbot": KylinBotAdapter,
    "hermes_agent": HermesAgentAdapter,
}


def list_agents() -> Dict[str, Dict[str, str]]:
    """返回 {name: {name, description}} 供 CLI 展示。"""
    return {
        name: {"name": cls.name, "description": cls.description}
        for name, cls in REGISTRY.items()
    }


def get_agent(name: str) -> AgentAdapter:
    """按名称实例化一个智能体。"""
    if name not in REGISTRY:
        raise KeyError(f"未知智能体 {name!r},可选: {', '.join(REGISTRY)}")
    return REGISTRY[name]()
