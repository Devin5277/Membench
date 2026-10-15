"""演示录屏辅助脚本:生成自动播放的 HTML 演示 + 可选 MP4。

用法:
    python scripts/make_demo.py [--agents mock_good,mock_typical,mock_weak] [--out demo] [--seconds 25]

生成内容(位于 --out 目录):
    index.html     自动播放的幻灯片(全屏打开后即可录屏)
    radar.png      六维对比雷达图
    report.json / report.md  完整评测结果

录屏建议:浏览器全屏打开 index.html,用系统录屏(如 OBS / GNOME Screen Recorder)
录制 3–5 分钟即可。--seconds 控制每页停留时长,默认 25 秒 × 8 页 ≈ 3 分 20 秒。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from membench.models import CAPABILITIES, CAPABILITY_ORDER  # noqa: E402
from membench.radar import draw_radar  # noqa: E402
from membench.report import build_payload, write_json, write_markdown  # noqa: E402
from membench.runner import run_benchmark  # noqa: E402


def _cap_table_html(reports) -> str:
    agents = [r.agent_name for r in reports]
    head = "<tr><th>能力维度</th>" + "".join(f"<th>{a}</th>" for a in agents) + "</tr>"
    rows = []
    for cap in CAPABILITY_ORDER:
        label = CAPABILITIES[cap]["label"]
        cells = "".join(
            f"<td>{r.capability_scores.get(cap, 0.0):.1f}</td>" for r in reports
        )
        rows.append(f"<tr><td>{label}</td>{cells}</tr>")
    overall = "".join(f"<td><b>{r.overall:.1f}</b></td>" for r in reports)
    rows.append(f"<tr><td><b>综合</b></td>{overall}</tr>")
    return f"<table>{head}{''.join(rows)}</table>"


def _episode_table_html(report) -> str:
    rows = []
    for r in report.results:
        icon = "✅" if r.score >= 100 else ("⚠️" if r.score >= 50 else "❌")
        rows.append(
            f"<tr><td>{icon}</td><td>{r.episode_id}</td>"
            f"<td>{CAPABILITIES[r.capability]['label']}</td>"
            f"<td>{r.title}</td><td>{r.score:.1f}</td></tr>"
        )
    return (
        "<table><tr><th></th><th>用例</th><th>能力</th><th>场景</th><th>得分</th></tr>"
        + "".join(rows) + "</table>"
    )


def build_html(reports, episodes, seconds: int, title: str, radar_ok: bool = True) -> str:
    slides = []
    agents = "、".join(r.agent_name for r in reports)

    slides.append(f"""
    <section class="slide" data-title="标题">
      <h1>智能体长期记忆<br>可解释评测框架</h1>
      <p class="sub">面向 openKylin 操作系统 · 六维能力 · 确定性可解释评分</p>
      <p class="small">评测对象:{agents}</p>
    </section>""")

    cap_items = "".join(
        f"<li><b>{CAPABILITIES[c]['label']}</b> — {CAPABILITIES[c]['desc']}</li>"
        for c in CAPABILITY_ORDER
    )
    slides.append(f"""
    <section class="slide" data-title="六项能力">
      <h2>六项核心能力指标</h2>
      <ul class="caps">{cap_items}</ul>
    </section>""")

    slides.append("""
    <section class="slide" data-title="流程">
      <h2>评测流程</h2>
      <ol class="flow">
        <li>重置智能体状态</li>
        <li>播种:回放对话,灌输稳定/敏感/临时/模板信息</li>
        <li>探针:提问并采集回答、记忆快照、行动轨迹</li>
        <li>评分:确定性检查,区分「记住/误记/不该记却记了」</li>
        <li>聚合:六维 0–100 分 + 综合分 + 雷达图</li>
      </ol>
    </section>""")

    if radar_ok:
        slides.append("""
        <section class="slide" data-title="雷达图">
          <h2>六维能力对比雷达图</h2>
          <img src="radar.png" alt="雷达图" class="radar">
        </section>""")

    slides.append(f"""
    <section class="slide" data-title="得分总览">
      <h2>六维得分总览</h2>
      {_cap_table_html(reports)}
    </section>""")

    for report in reports:
        slides.append(f"""
        <section class="slide" data-title="{report.agent_name}">
          <h2>智能体:{report.agent_name}</h2>
          {_episode_table_html(report)}
        </section>""")

    slides.append("""
    <section class="slide" data-title="结束">
      <h2>谢谢观看</h2>
      <p class="sub">一键运行:<code>membench run</code></p>
      <p class="small">报告:report.json / report.md · 雷达图:radar.png</p>
    </section>""")

    slides_html = "".join(slides)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ margin:0; background:#10141f; color:#e6e9f0; font-family:"Microsoft YaHei","Noto Sans SC",sans-serif; }}
  .slide {{ display:none; width:100vw; height:100vh; box-sizing:border-box; padding:8vh 10vw;
            flex-direction:column; justify-content:center; align-items:center; text-align:center; }}
  .slide.active {{ display:flex; }}
  h1 {{ font-size:3.4rem; line-height:1.3; }}
  h2 {{ font-size:2.4rem; margin-bottom:4vh; }}
  .sub {{ font-size:1.5rem; color:#9aa3b5; }}
  .small {{ font-size:1.1rem; color:#6b7280; margin-top:2vh; }}
  code {{ background:#1f2937; padding:2px 10px; border-radius:6px; }}
  ul.caps {{ text-align:left; font-size:1.5rem; line-height:2.2; list-style:none; padding:0; }}
  ul.caps li::before {{ content:"▸ "; color:#5b8def; }}
  ol.flow {{ text-align:left; font-size:1.5rem; line-height:2.4; }}
  table {{ border-collapse:collapse; font-size:1.4rem; min-width:60vw; }}
  th,td {{ border:1px solid #2a3244; padding:10px 18px; }}
  th {{ background:#1b2233; }}
  img.radar {{ max-width:70vw; max-height:70vh; background:#fff; border-radius:10px; }}
</style>
</head>
<body>
{slides_html}
<script>
  const slides = Array.from(document.querySelectorAll('.slide'));
  let i = 0;
  function show(n) {{
    slides.forEach(s => s.classList.remove('active'));
    slides[n % slides.length].classList.add('active');
  }}
  show(0);
  setInterval(() => show(++i), {seconds * 1000});
</script>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="生成演示录屏用的自动播放 HTML 幻灯片")
    parser.add_argument("--dataset", default=None, help="数据集 JSON 路径(默认内置样例)")
    parser.add_argument("--agents", default="mock_good,mock_typical,mock_weak", help="逗号分隔的智能体名")
    parser.add_argument("--scorer", default="keyword", choices=["keyword", "semantic"])
    parser.add_argument("--out", default="demo", help="输出目录")
    parser.add_argument("--seconds", type=int, default=25, help="每页停留秒数")
    parser.add_argument("--title", default="智能体长期记忆能力对比")
    args = parser.parse_args()

    from membench.dataset import DEFAULT_DATASET
    dataset = args.dataset or str(DEFAULT_DATASET)
    agent_names = [a.strip() for a in args.agents.split(",") if a.strip()]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    episodes, reports = run_benchmark(dataset, agent_names, scorer=args.scorer)

    radar_path = out / "radar.png"
    radar_ok = True
    try:
        draw_radar(reports, radar_path, title=args.title)
    except ImportError:
        radar_ok = False
        print("[警告] 未安装 matplotlib,已跳过雷达图(其余演示页不受影响)。")
    write_json(out / "report.json", build_payload(episodes, reports, {"agents": agent_names}))
    write_markdown(out / "report.md", reports)

    html = build_html(reports, episodes, args.seconds, args.title, radar_ok=radar_ok)
    (out / "index.html").write_text(html, encoding="utf-8")

    print(f"演示已生成: {out.resolve()}")
    print(f"  - index.html (浏览器全屏打开即可录屏)")
    print(f"  - radar.png / report.json / report.md")
    print(f"共 {len(reports)} 个智能体、{len(episodes)} 个用例、约 {args.seconds * (len(reports) + 6)} 秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
