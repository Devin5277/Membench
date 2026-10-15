"""核心数据结构定义。

仅使用标准库 dataclasses,保证在 openKylin 上零第三方依赖即可运行。
数据模型覆盖:能力指标、对话轮次、探针、评测用例(Episode)、检查结果与报告。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# 六项核心能力指标(与命题要求一致)
# ---------------------------------------------------------------------------
CAPABILITIES: Dict[str, Dict[str, str]] = {
    "retention":      {"label": "长期保持", "desc": "偏好/路径/模板等稳定信息长期记住"},
    "recall":         {"label": "记忆调用", "desc": "在需要时正确调出相关记忆"},
    "update":         {"label": "动态更新", "desc": "冲突/新信息覆盖旧信息"},
    "discrimination": {"label": "相近区分", "desc": "相似信息之间正确区分"},
    "boundary":       {"label": "边界识别", "desc": "临时/敏感/风险信息被正确排除"},
    "reuse":          {"label": "任务复用", "desc": "记忆与行动轨迹复用到新任务"},
}

# 雷达图按固定顺序绘制六项能力
CAPABILITY_ORDER: List[str] = [
    "retention", "recall", "update", "discrimination", "boundary", "reuse",
]


@dataclass
class Turn:
    """一轮对话。role: user / assistant / system。"""
    role: str
    content: str


@dataclass
class Probe:
    """探针:评测阶段向智能体提出的问题及期望结果。

    - should_contain / should_not_contain: 期望回答中应出现 / 不应出现的关键词。
    - expected_memory_present / absent: 期望探针后智能体记忆中应存在 / 不应存在的键。
    """
    query: str
    should_contain: List[str] = field(default_factory=list)
    should_not_contain: List[str] = field(default_factory=list)
    expected_memory_present: List[str] = field(default_factory=list)
    expected_memory_absent: List[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class Episode:
    """一个评测单元(测试用例)。

    - capability: 六项能力之一(见 CAPABILITIES 的键)。
    - turns: 播种阶段对话,用于向智能体灌输信息。
    - files: 可选,播种阶段提供的外部文件证据(相对路径 -> 内容)。
    - probe: 探针。
    """
    id: str
    capability: str
    title: str
    description: str = ""
    turns: List[Turn] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)
    probe: Optional[Probe] = None
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 评分结果模型
# ---------------------------------------------------------------------------
@dataclass
class CheckResult:
    """单条检查结果(可解释)。classification 区分"记住/误记/不该记却记了"三类。"""
    check_type: str       # should_contain / should_not_contain / memory_present / memory_absent
    target: str
    passed: bool
    detail: str
    classification: str   # 正确记忆 / 遗漏误记 / 误记混淆 / 越界记忆


@dataclass
class EpisodeResult:
    """单个用例在某智能体上的评测结果。"""
    episode_id: str
    capability: str
    title: str
    score: float
    passed_checks: int
    total_checks: int
    checks: List[CheckResult] = field(default_factory=list)
    probe_answer: str = ""
    memory_snapshot: Dict[str, str] = field(default_factory=dict)
    action_trace: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


@dataclass
class AgentReport:
    """单个智能体的完整评测报告。"""
    agent_name: str
    results: List[EpisodeResult] = field(default_factory=list)
    capability_scores: Dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
