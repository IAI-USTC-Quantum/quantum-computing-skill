# quantum-computing.skill

[![Quantum Computing | AI](https://img.shields.io/badge/Quantum_Computing-AI-58a6ff?style=flat-square)](https://github.com/IAI-USTC-Quantum)
[![ClawHub](https://img.shields.io/badge/ClawHub-published-9b59b6?style=flat-square)](https://clawhub.ai/agony5757/quantum-computing)
[![SkillHub](https://img.shields.io/badge/SkillHub-published-58a6ff?style=flat-square)](https://www.skillhub.cn/skills/quantum-computing)

面向 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 的 Agent Skills 集合仓库。

当前版本已 follow-up UnifiedQuantum v0.0.8，重点同步了官方文档“最佳实践”章节中的推荐路径、显式 dummy backend id、dry-run、Calibration/QEM/XEB 和新模块入口约定。

当前提供的通用 skill 是 `uniqc-basic-usage`。它覆盖 UnifiedQuantum/uniqc 的基础使用路径，例如安装、线路构建、OriginIR / QASM 转换、本地模拟、CLI、config、dummy backend、dry-run、backend cache、简单提交和通用排障。

`uniqc-version-follow-up` 已改为 Claude Code 项目级 slash command，只供维护者在本仓库内主动调用，用于每次 UnifiedQuantum 发版后的最终同步。

## 当前 Skills

- `uniqc-basic-usage`: 通用、跨 Agent 的 UnifiedQuantum 基础使用 skill。

后续可以继续在 `skills/` 下增加更窄的专用 skill，例如算法开发、QEM 使用、真机提交、release 前测试等。

## 可以直接让 Agent 做什么

安装 `uniqc-basic-usage` 后，可以直接对 Agent 说这类请求：

- “帮我写一个 Bell state 的 UnifiedQuantum 示例，并导出 OriginIR。”
- “帮我把这段 QASM 转成更适合 `uniqc simulate` 的流程。”
- “帮我把这个线路先用 dummy 跑通。”
- “帮我打开 `uniqc config always-ai-hint` 并解释 CLI 的下一步提示。”
- “帮我根据 backend cache 看一下可用 backend。”

## 通过 npx skills 安装

同时安装到 Codex 和 Claude Code：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  --agent codex \
  --agent claude-code \
  --skill uniqc-basic-usage
```

只安装到 Codex：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  --agent codex \
  --skill uniqc-basic-usage
```

只安装到 Claude Code：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  --agent claude-code \
  --skill uniqc-basic-usage
```

安装到全局目录时加 `-g`。项目级安装时，Codex 会落到 `.agents/skills/`，Claude Code 会落到 `.claude/skills/`。

## 维护者命令

本仓库包含 Claude Code 项目级 slash command：

```text
/uniqc-version-follow-up [release-tag-or-version]
```

它位于 `.claude/commands/uniqc-version-follow-up.md`，只面向维护者在本仓库中主动调用，不作为跨 Agent skill 分发。

## 仓库内容

- `skills/uniqc-basic-usage/SKILL.md`：通用 skill 主入口
- `skills/uniqc-basic-usage/references/`：按主题整理的使用说明与排障参考
- `skills/uniqc-basic-usage/examples/`：可复用的示例代码
- `skills/uniqc-basic-usage/scripts/`：环境检查和辅助脚本
- `.claude/commands/uniqc-version-follow-up.md`：维护者 follow-up slash command

## 通过 ClawHub 安装（推荐）

```bash
# 访问 https://clawhub.ai/agony5757/quantum-computing 获取安装命令
```

ClawHub 支持直接从云端一键安装或克隆本 skill。

## 通过 SkillHub 发布

本 skill 已发布至 [SkillHub](https://www.skillhub.cn/skills/quantum-computing)，一个面向 AI Agent 的 Skill 市场，支持从云端直接安装。

## 许可证

Apache 2.0 许可证
