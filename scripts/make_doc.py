#!/usr/bin/env python3
"""将 docs/作品介绍.md 渲染为自包含 HTML,并用 Edge 无头模式导出 PDF。

用法:
    python scripts/make_doc.py

产物:
    docs/作品介绍.html   自包含(雷达图内嵌为 base64)的打印排版 HTML
    docs/作品介绍.pdf    依赖本机 Microsoft Edge 的无头打印导出

说明:
    若 Edge 无头打印失败,可打开 docs/作品介绍.html,浏览器「打印 → 另存为 PDF」即可。
"""
from __future__ import annotations

import base64
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "docs" / "作品介绍.md"
HTML = ROOT / "docs" / "作品介绍.html"
PDF = ROOT / "docs" / "作品介绍.pdf"
RADAR = ROOT / "results" / "radar.png"

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CSS = """
@page { size: A4; margin: 20mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  font-size: 12.5px; line-height: 1.75; color: #1a1a1a; margin: 0;
}
h1 { font-size: 24px; text-align: center; margin: 0 0 6px; color: #1a365d; }
.subtitle { text-align: center; color: #666; margin: 0 0 24px; font-size: 13px; }
h2 { font-size: 17px; border-left: 4px solid #2b6cb0; padding-left: 10px;
     margin: 26px 0 10px; color: #1a365d; page-break-after: avoid; }
p { margin: 6px 0; }
strong { color: #1a365d; }
code { background: #f0f3f7; padding: 1px 5px; border-radius: 3px;
       font-family: Consolas, "Courier New", monospace; font-size: 11.5px; }
pre { background: #f7f9fb; border: 1px solid #e2e8f0; border-radius: 6px;
      padding: 10px 12px; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 12px; }
th, td { border: 1px solid #d5dde5; padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: #eef3f8; color: #1a365d; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 18px 0; }
ul, ol { margin: 6px 0; padding-left: 24px; }
li { margin: 3px 0; }
img.figure { max-width: 88%; display: block; margin: 12px auto; }
a { color: #2b6cb0; text-decoration: none; }
"""


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text: str) -> str:
    text = _escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    def _img(m: re.Match) -> str:
        alt, src = m.group(1), m.group(2)
        if src == "radar.png" and RADAR.exists():
            data = base64.b64encode(RADAR.read_bytes()).decode("ascii")
            return f'<img class="figure" src="data:image/png;base64,{data}" alt="{alt}">'
        return ""

    text = re.sub(r"!\[([^\]]*)\]\(([^)]*)\)", _img, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def _render_table(rows: list[str]) -> str:
    rows = [r for r in rows if r.strip().startswith("|")]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]  # 第二行为 |---| 分隔线
    out = ["<table>", "<thead><tr>"]
    out += [f"<th>{_inline(c)}</th>" for c in header]
    out += ["</tr></thead><tbody>"]
    for row in body:
        out.append("<tr>")
        out += [f"<td>{_inline(c)}</td>" for c in row]
        out.append("</tr>")
    out += ["</tbody></table>"]
    return "\n".join(out)


def _is_list_line(s: str) -> bool:
    return bool(re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s))


def render_markdown(text: str) -> str:
    lines = text.splitlines()
    html: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("```"):  # 代码块
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(_escape(lines[i]))
                i += 1
            i += 1
            html.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:  # 标题
            level = len(m.group(1))
            html.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if re.fullmatch(r"[-=*]{3,}", stripped):  # 分隔线
            html.append("<hr>")
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < n and re.fullmatch(r"\|?[\s:|-]+\|?", lines[i + 1].strip()):
            block = []  # 表格
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            html.append(_render_table(block))
            continue
        if _is_list_line(stripped):  # 列表
            ordered = bool(re.match(r"^\d+\.\s+", stripped))
            items = []
            while i < n and lines[i].strip() and _is_list_line(lines[i].strip()):
                item = re.sub(r"^(?:[-*]|\d+\.)\s+", "", lines[i].strip())
                items.append(f"<li>{_inline(item)}</li>")
                i += 1
            tag = "ol" if ordered else "ul"
            html.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        # 段落
        buf = [stripped]
        i += 1
        while i < n and lines[i].strip() and not _is_list_line(lines[i].strip()) \
                and not lines[i].strip().startswith(("#", "```", "|")) \
                and not re.fullmatch(r"[-=*]{3,}", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        html.append("<p>" + _inline(" ".join(buf)) + "</p>")
    return "\n".join(html)


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    body = render_markdown(text)
    doc = (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>membench · 智能体长期记忆可解释评测框架</title>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )
    HTML.write_text(doc, encoding="utf-8")
    print(f"[OK] 已生成 HTML: {HTML}")

    if not RADAR.exists():
        print("[警告] 未找到 results/radar.png,已跳过图片嵌入。可先运行 `membench run` 生成。")

    if not Path(EDGE).exists():
        print(f"[跳过] 未找到 Edge({EDGE}),请手动打开 HTML 打印为 PDF。")
        return 0

    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={PDF}", HTML.as_uri()]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        if PDF.exists():
            print(f"[OK] 已生成 PDF: {PDF}")
        else:
            print("[警告] Edge 未产出 PDF,请手动打开 HTML 打印为 PDF。")
    except subprocess.CalledProcessError as exc:
        print(f"[警告] Edge 无头打印失败: {exc.stderr.decode(errors='ignore')[:300]}")
        print("       可手动打开 docs/作品介绍.html → 打印 → 另存为 PDF。")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
