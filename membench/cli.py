"""一键运行命令行接口。

用法:
    membench init    [--out DIR]                 生成样例数据集
    membench agents                               列出已注册智能体
    membench run     [--dataset PATH] [--agents A,B] [--out DIR] [--title T]
                                                   运行评测,产出 report.json / report.md / radar.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from membench import __version__
from membench.agents import list_agents
from membench.dataset import DEFAULT_DATASET, load, write
from membench.metrics import aggregate  # noqa: F401  (保留语义导入)
from membench.models import CAPABILITIES, CAPABILITY_ORDER, AgentReport
from membench.radar import draw_radar
from membench.report import build_payload, render_markdown, write_json, write_markdown
from membench.runner import run_benchmark


def _cmd_init(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    episodes = load(DEFAULT_DATASET)
    target = out_dir / "episodes.json"
    write(target, episodes)
    print(f"已生成样例数据集: {target}  (共 {len(episodes)} 个用例)")
    return 0


def _cmd_agents(args: argparse.Namespace) -> int:
    agents = list_agents()
    for name, info in agents.items():
        print(f"- {name}: {info['description']}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    dataset_path = Path(args.dataset)
    agent_names = [a.strip() for a in args.agents.split(",") if a.strip()]
    out_dir = Path(args.out)

    print(f"数据集: {dataset_path}")
    print(f"智能体: {', '.join(agent_names)}")
    print()

    episodes, reports = run_benchmark(dataset_path, agent_names, scorer=args.scorer)

    # JSON 报告
    meta = {
        "version": __version__,
        "dataset": str(dataset_path),
        "agents": agent_names,
        "scorer": args.scorer,
    }
    payload = build_payload(episodes, reports, meta)
    json_path = out_dir / "report.json"
    write_json(json_path, payload)

    # Markdown 报告
    md_path = out_dir / "report.md"
    write_markdown(md_path, reports)

    # 雷达图
    radar_path = out_dir / "radar.png"
    radar_done = False
    try:
        draw_radar(reports, radar_path, title=args.title)
        radar_done = True
    except ImportError:
        print("[警告] 未安装 matplotlib,跳过雷达图生成。JSON/Markdown 报告已正常产出。")
    except Exception as exc:  # noqa: BLE001
        print(f"[警告] 雷达图生成失败: {exc}")

    # 终端摘要
    _print_summary(reports)

    print()
    print(f"结果已输出到目录: {out_dir.resolve()}")
    print(f"  - report.json")
    print(f"  - report.md")
    if radar_done:
        print(f"  - radar.png")
    return 0


def _print_summary(reports: list[AgentReport]) -> None:
    agents = [r.agent_name for r in reports]
    header = "能力维度".ljust(10) + "".join(f"{a:>16}" for a in agents)
    print(header)
    print("-" * len(header))
    for cap in CAPABILITY_ORDER:
        label = CAPABILITIES[cap]["label"]
        row = label.ljust(10) + "".join(f"{r.capability_scores.get(cap, 0.0):>16}" for r in reports)
        print(row)
    print("-" * len(header))
    overall = "综合".ljust(10) + "".join(f"{r.overall:>16}" for r in reports)
    print(overall)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="membench",
        description="智能体长期记忆可解释评测框架(membench)",
    )
    parser.add_argument("--version", action="version", version=f"membench {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="生成样例数据集")
    p_init.add_argument("--out", default="data/samples", help="输出目录 (默认 data/samples)")
    p_init.set_defaults(func=_cmd_init)

    p_agents = sub.add_parser("agents", help="列出已注册智能体")
    p_agents.set_defaults(func=_cmd_agents)

    p_run = sub.add_parser("run", help="运行评测并产出报告与雷达图")
    p_run.add_argument("--dataset", default=str(DEFAULT_DATASET), help="数据集 JSON 路径")
    p_run.add_argument("--agents", default="mock_good,mock_weak", help="逗号分隔的智能体名")
    p_run.add_argument("--out", default="results", help="结果输出目录 (默认 results)")
    p_run.add_argument("--title", default="智能体长期记忆能力对比", help="雷达图标题")
    p_run.add_argument("--scorer", default="keyword", choices=["keyword", "semantic"],
                       help="评分器:keyword(确定性关键词,默认) 或 semantic(字符 n-gram 语义基线)")
    p_run.set_defaults(func=_cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
