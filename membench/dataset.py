"""数据集:加载、校验与默认样例。

数据集为 JSON 文件,顶层结构 {"episodes": [ ... ]}。
Episode 字段见 models.Episode;probe 字段见 models.Probe。

示例(部分):
{
  "episodes": [
    {
      "id": "retention-01",
      "capability": "retention",
      "title": "长期保持:稳定信息不受无关对话干扰",
      "turns": [
        {"role": "user", "content": "[记住] name = 张三"},
        {"role": "user", "content": "今天天气不错"}
      ],
      "probe": {
        "query": "请问我的名字是什么?",
        "should_contain": ["张三"],
        "expected_memory_present": ["name"],
        "rationale": "稳定信息应被长期保持。"
      }
    }
  ]
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from membench.models import CAPABILITIES, Episode, Probe, Turn

# 默认样例数据集(包内置,安装后也能定位;项目根 data/samples 下另存一份可编辑副本)
DEFAULT_DATASET = Path(__file__).resolve().parent / "data" / "episodes.json"


# ---------------------------------------------------------------------------
# 解析与序列化
# ---------------------------------------------------------------------------
def parse_probe(d: Dict[str, Any]) -> Probe:
    return Probe(
        query=d.get("query", ""),
        should_contain=list(d.get("should_contain", [])),
        should_not_contain=list(d.get("should_not_contain", [])),
        expected_memory_present=list(d.get("expected_memory_present", [])),
        expected_memory_absent=list(d.get("expected_memory_absent", [])),
        rationale=d.get("rationale", ""),
    )


def parse_episode(d: Dict[str, Any]) -> Episode:
    turns = [Turn(role=t.get("role", "user"), content=t.get("content", "")) for t in d.get("turns", [])]
    probe = parse_probe(d["probe"]) if d.get("probe") else None
    return Episode(
        id=d.get("id", ""),
        capability=d.get("capability", ""),
        title=d.get("title", ""),
        description=d.get("description", ""),
        turns=turns,
        files=dict(d.get("files", {})),
        probe=probe,
        tags=list(d.get("tags", [])),
    )


def episode_to_dict(ep: Episode) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "id": ep.id,
        "capability": ep.capability,
        "title": ep.title,
        "description": ep.description,
        "turns": [{"role": t.role, "content": t.content} for t in ep.turns],
        "files": dict(ep.files),
        "tags": list(ep.tags),
    }
    if ep.probe is not None:
        d["probe"] = {
            "query": ep.probe.query,
            "should_contain": list(ep.probe.should_contain),
            "should_not_contain": list(ep.probe.should_not_contain),
            "expected_memory_present": list(ep.probe.expected_memory_present),
            "expected_memory_absent": list(ep.probe.expected_memory_absent),
            "rationale": ep.probe.rationale,
        }
    return d


# ---------------------------------------------------------------------------
# 加载 / 写入 / 校验
# ---------------------------------------------------------------------------
def load(path: str | Path) -> List[Episode]:
    """从 JSON 文件加载数据集。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"数据集文件不存在: {p}")
    raw = json.loads(p.read_text(encoding="utf-8"))
    items = raw.get("episodes", raw) if isinstance(raw, dict) else raw
    return [parse_episode(item) for item in items]


def write(path: str | Path, episodes: List[Episode]) -> None:
    """把数据集序列化为 JSON 写入 path。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"episodes": [episode_to_dict(ep) for ep in episodes]}
    p.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate(episodes: List[Episode]) -> List[str]:
    """校验数据集,返回错误信息列表(空表示合法)。"""
    errors: List[str] = []
    seen: set[str] = set()
    for ep in episodes:
        if not ep.id:
            errors.append("存在缺少 id 的用例")
        elif ep.id in seen:
            errors.append(f"用例 id 重复: {ep.id}")
        seen.add(ep.id)

        if ep.capability not in CAPABILITIES:
            errors.append(f"[{ep.id}] 未知能力 {ep.capability!r},应为 {list(CAPABILITIES)} 之一")

        if ep.probe is None:
            errors.append(f"[{ep.id}] 缺少 probe")
            continue

        if not ep.probe.query:
            errors.append(f"[{ep.id}] probe.query 为空")
        if not ep.probe.should_contain and not ep.probe.should_not_contain \
                and not ep.probe.expected_memory_present and not ep.probe.expected_memory_absent:
            errors.append(f"[{ep.id}] probe 未定义任何检查项")
    return errors
