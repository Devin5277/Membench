# membench —— 智能体长期记忆可解释评测框架

面向 **openKylin 操作系统** 的智能体长期记忆能力,提供**可解释、确定性**的自动化评测。
对应 2026 上海开源软件应用创新大赛「开源 AI 工具赛道」openKylin 命题
《面向 openKylin 操作系统的智能体长期记忆自动化评测 Benchmark 设计》。

它把「对话、记忆记录、行动轨迹、文件」统一组织为证据,以**确定性、可解释**的方式
自动评估智能体的六项长期记忆能力,一键产出 JSON / Markdown 报告与多维对比雷达图。

## 六项能力指标

| 指标 | 含义 |
| --- | --- |
| 长期保持 | 偏好/路径/模板等稳定信息长期记住 |
| 记忆调用 | 在需要时正确调出相关记忆 |
| 动态更新 | 冲突/新信息覆盖旧信息 |
| 相近区分 | 相似信息之间正确区分 |
| 边界识别 | 临时/敏感/风险信息被正确排除 |
| 任务复用 | 记忆与行动轨迹复用到新任务 |

## 快速开始

```bash
# 1. 安装(核心零第三方依赖;雷达图需 matplotlib)
pip install -e .

# 2. 列出可用的智能体
membench agents

# 3. 一键运行评测(默认对 mock_good / mock_typical / mock_weak 三个模拟智能体)
membench run

# 等价于
python -m membench run

# 使用语义判分(字符 n-gram 基线,零依赖,可插拔)
membench run --scorer semantic

# 生成自动播放演示幻灯片(用于 3–5 分钟录屏)
python scripts/make_demo.py --out demo
```

运行后在 `results/` 下得到:

- `report.json` —— 机器可读的完整评分(每条检查含判定与原因)
- `report.md`   —— 人可读的报告
- `radar.png`   —— 六维能力对比雷达图

## 自定义

```bash
# 生成样例数据集到指定位置
membench init --out mydata

# 批量扩展数据集(确定性生成器,默认 120 例)
python scripts/gen_dataset.py --per 20
membench run --dataset data/generated/episodes.json

# 用自定义数据集、指定智能体、指定输出目录运行
membench run --dataset mydata/episodes.json --agents mock_good,mock_typical,mock_weak --out myresults
```

## 接入真实智能体

只需实现 `membench.agent.AgentAdapter` 的四个方法
(`reset` / `on_user` / `memory_snapshot` / `action_trace`),
并在 `membench/agents/__init__.py` 的 `REGISTRY` 中登记即可。
详见 `docs/DESIGN.md`。

已内置 **KylinBot / Hermes Agent** 的 OpenAI 兼容 HTTP 适配器骨架
(名称为 `kylinbot` / `hermes_agent`),设置环境变量 `MEMBENCH_BASE_URL`
(必要时还有 `MEMBENCH_API_KEY`、`MEMBENCH_MODEL`)后即可 `membench run --agents kylinbot,...` 接入。

## 项目结构

```
mem-bench/
├── membench/            # 核心包
│   ├── cli.py           # 一键 CLI
│   ├── models.py        # 数据结构(六项能力/Episode/Probe/评分模型)
│   ├── agent.py         # AgentAdapter 抽象接口
│   ├── protocol.py      # 事实协议与别名表(样例/模拟智能体共用)
│   ├── dataset.py       # 数据集加载/校验
│   ├── runner.py        # 评测运行器
│   ├── scorer.py        # 自动评分引擎(可解释)
│   ├── scorer_semantic.py # 语义判分器(可插拔,零依赖基线)
│   ├── metrics.py       # 六维指标聚合
│   ├── report.py        # JSON/Markdown 报告
│   ├── radar.py         # 多维对比雷达图
│   ├── agents/          # 智能体适配器(模拟 + KylinBot/HermesAgent 骨架)
│   └── data/            # 内置样例数据集
├── data/samples/        # 可编辑样例数据集副本
├── data/generated/      # 生成器产出的扩展集(120 例)
├── docs/DESIGN.md       # 方案说明文档
├── docs/openKylin.md    # openKylin 集成与安装说明
├── docs/作品介绍.md/.pdf # 作品介绍文档(提交用 PDF)
├── tests/               # 测试
├── scripts/build_deb.sh # .deb 打包脚本
├── scripts/make_demo.py # 演示录屏脚本
├── scripts/gen_dataset.py # 数据集生成器(批量扩展)
└── debian/control       # Debian 打包元数据
```

## 许可证

MIT
