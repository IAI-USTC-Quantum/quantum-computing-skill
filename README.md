# quantum-computing.skill

[![Quantum Computing | AI](https://img.shields.io/badge/Quantum_Computing-AI-58a6ff?style=flat-square)](https://github.com/IAI-USTC-Quantum)
[![ClawHub](https://img.shields.io/badge/ClawHub-published-9b59b6?style=flat-square)](https://clawhub.ai/agony5757/quantum-computing)
[![SkillHub](https://img.shields.io/badge/SkillHub-published-58a6ff?style=flat-square)](https://www.skillhub.cn/skills/quantum-computing)

面向 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 的 Agent Skills 集合仓库。

当前版本已 follow-up UnifiedQuantum v0.0.12，重点同步了 v0.0.12 的新特性：uniqc-managed 任务 ID 间接层（`uqt_*`）、原生批量提交（OriginQ / IBM 单任务 ID 多线路）、自动分片，以及 v0.0.11 的 Quark 后端、标定/QEM 模块、timeline 可视化、顶层 config 模块、扩展的 dummy backend 标识符。

当前提供的通用 skill 是 `uniqc-basic-usage`。它覆盖 UnifiedQuantum/uniqc 的基础使用路径，例如安装、线路构建、OriginIR / QASM 转换、本地模拟、CLI、config、dummy backend、dry-run、backend cache、简单提交、标定/QEM、timeline 可视化和通用排障。

## 当前 Skills

通用入口：

- `uniqc-basic-usage`: 通用、跨 Agent 的 UnifiedQuantum 基础使用 skill。

流程类（按场景细分）：

- `uniqc-cloud-submit`: 真机 / 云端端到端提交 —— `uniqc config validate` 健康检查
  （注意：用户口中的 `uniqc doctor` **不存在**，请改用 `config validate`）、把 Python
  `Circuit` 持久化为 `.originir` / `.qasm`、`dry_run_task` → `submit_task` →
  `query_task` → `wait_for_result`，以及 `uqt_*` 任务 ID / shard 映射。
- `uniqc-result-analysis`: `UnifiedResult` 解析、counts / probability 表、histogram /
  distribution 可视化、Pauli 期望、circuit + timeline HTML、双跑对比（TV / Hellinger）。
- `uniqc-xeb-qem`: XEB 1q / 2q / parallel benchmarking、Readout 标定与 QEM
  （`ReadoutEM.apply` / `M3Mitigator.apply`），含 `find_cached_results(result_type=...)`、
  `StaleCalibrationError` 注意事项、`~/.uniqc/calibration_cache/` 布局。

算法类：

- `uniqc-qaoa`: 三层抽象的 QAOA —— `qaoa_workflow.run_qaoa_workflow` 一键、
  `qaoa_ansatz` + `pauli_expectation` + SciPy 手撸、以及真机 compile / batch / decode。
- `uniqc-quantum-ml`: PyTorch QML —— `QNNClassifier` / `QCNNClassifier` /
  `HybridQCLModel`（需 torchquantum）和 `QuantumLayer` parameter-shift 自动微分。
- `uniqc-algorithm-cases`: 规范化算法目录与模板 —— GHZ / W / Dicke / cluster / thermal
  state、QFT、QPE（位于 `uniqc.algorithms.core.circuits.qpe_circuit`，**不在顶层**）、
  Grover、amplitude estimation、Deutsch-Jozsa、VQE / VQD、state tomography、classical
  shadow。

每个 skill 都遵循 `SKILL.md` + `references/` + `examples/` + `agents/openai.yaml` 的
结构，可单独安装：`npx skills add ... --skill uniqc-cloud-submit`。

后续会继续在 `skills/` 下扩展更窄的专用 skill。

## 可以直接让 Agent 做什么

安装 `uniqc-basic-usage` 后，可以直接对 Agent 说这类请求：

- “帮我写一个 Bell state 的 UnifiedQuantum 示例，并导出 OriginIR。”
- “帮我把这段 QASM 转成更适合 `uniqc simulate` 的流程。”
- “帮我把这个线路先用 dummy 跑通。”
- “帮我打开 `uniqc config always-ai-hint` 并解释 CLI 的下一步提示。”
- “帮我根据 backend cache 看一下可用 backend。”

## 通过 npx skills 安装（推荐）

默认建议一次性安装本仓库下的所有 skills。当前只有 `uniqc-basic-usage`，后续新增算法开发、QEM、真机提交等专用 skills 后，下面的命令会一起安装。
这个命令与 `uniqc --help` 中展示的 AI 安装建议保持一致，是目前最推荐的安装方式。

### For Codex

安装到当前项目：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  --agent codex \
  --skill '*'
```

全局安装到当前用户：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  -g \
  --agent codex \
  --skill '*'
```

### For Claude Code

安装到当前项目：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  --agent claude-code \
  --skill '*'
```

全局安装到当前用户：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  -g \
  --agent claude-code \
  --skill '*'
```

### 安装到项目还是全局

不加 `-g` 时是项目级安装，适合只在当前仓库使用、或者希望团队通过仓库共享同一组 skills。项目级安装会写入当前目录下的 agent 配置目录：

- Codex: `.agents/skills/`
- Claude Code: `.claude/skills/`

加 `-g` 时是全局安装，适合个人常用、跨多个项目复用、不希望修改当前项目文件的情况。全局安装会写入用户目录：

- Codex: `~/.codex/skills/`
- Claude Code: `~/.claude/skills/`

如果你只想列出仓库里有哪些 skills，不安装，可以运行：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill --list
```

如果你确实想安装到所有已支持/检测到的 Agent，可以使用 `--all`；但日常更推荐显式写 `--agent codex` 或 `--agent claude-code`，避免安装到不需要的 Agent 目录。

## 仓库内容

- `skills/uniqc-basic-usage/`：通用 skill 主入口（基础使用、CLI、模拟、配置等）。
- `skills/uniqc-cloud-submit/`：流程类 —— 健康检查 + 真机提交 + 任务追踪。
- `skills/uniqc-result-analysis/`：流程类 —— 结果解析 + 可视化 + 期望值。
- `skills/uniqc-xeb-qem/`：流程类 —— XEB 标定 + 读出错误缓解。
- `skills/uniqc-qaoa/`：算法类 —— QAOA workflow / 手撸 / 真机。
- `skills/uniqc-quantum-ml/`：算法类 —— PyTorch QML（QNN / QCNN / Hybrid / QuantumLayer）。
- `skills/uniqc-algorithm-cases/`：算法类 —— 规范化算法目录与可运行模板。

每个 skill 目录的内部结构：

- `SKILL.md`：skill 主入口（含 `description` front-matter）。
- `references/`：按主题整理的使用说明与排障参考。
- `examples/`：可独立运行的示例代码。
- `agents/openai.yaml`：SkillHub / OpenAI Agent 接口元数据。

## 通过 ClawHub 安装

```bash
# 访问 https://clawhub.ai/agony5757/quantum-computing 获取安装命令
```

ClawHub 支持直接从云端一键安装或克隆本 skill。

## 通过 SkillHub 发布

本 skill 已发布至 [SkillHub](https://www.skillhub.cn/skills/quantum-computing)，一个面向 AI Agent 的 Skill 市场，支持从云端直接安装。

## 许可证

Apache 2.0 许可证
