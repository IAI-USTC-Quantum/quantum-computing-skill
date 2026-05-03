# quantum-computing.skill

[![Quantum Computing | AI](https://img.shields.io/badge/Quantum_Computing-AI-58a6ff?style=flat-square)](https://github.com/IAI-USTC-Quantum)
[![ClawHub](https://img.shields.io/badge/ClawHub-published-9b59b6?style=flat-square)](https://clawhub.ai/agony5757/quantum-computing)
[![SkillHub](https://img.shields.io/badge/SkillHub-published-58a6ff?style=flat-square)](https://www.skillhub.cn/skills/quantum-computing)

面向 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 的本地 skill 仓库。

当前版本已 follow-up UnifiedQuantum v0.0.8，重点同步了官方文档“最佳实践”章节中的推荐路径、显式 dummy backend id、dry-run、Calibration/QEM/XEB 和新模块入口约定。

安装后，支持 skills 的 Agent 可以更稳地处理 UnifiedQuantum 相关任务，例如线路构建、OriginIR / QASM 转换、本地模拟、v0.0.8 显式 dummy backend id、dry-run、云平台与真机实验、backend cache、RegionSelector、compile/transpile、Calibration/QEM/XEB、变分算法示例、PyTorch 集成和通用排障。

## 这个 skill 能帮你什么

适合让 Agent 帮你处理这类事情：

- 写或修改 `Circuit` 线路代码
- 把线路导出成 OriginIR 或 OpenQASM
- 用 `uniqc` CLI 做转换、模拟、提交和查结果
- 搭建本地模拟、`dummy` / `dummy:virtual-*` / `dummy:<platform>:<backend>` 任务排练、云平台 simulator 和真机实验工作流
- 查看 backend cache、选择真机 backend、使用 chip-display / RegionSelector 规划 qubit 区域
- 使用 v0.0.8 “最佳实践”路径覆盖配置、dry-run、API/CLI 提交、Calibration/QEM 和 XEB workflow
- 搭一个 VQE / QAOA / UCCSD 风格的算法开发示例
- 看 `QuantumLayer`、parameter-shift 和批处理接口怎么接进 PyTorch

## 你可以直接让 Agent 做什么

安装后，可以直接对 Agent 说这类请求：

- “帮我写一个 Bell state 的 UnifiedQuantum 示例，并导出 OriginIR。”
- “帮我把这段 QASM 转成更适合 `uniqc simulate` 的流程。”
- “帮我写一个最小 QAOA MaxCut 例子。”
- “帮我把这个线路先用 dummy 跑通，再提交到 OriginQ 真机。”
- “帮我根据 backend cache 选择一组适合 Bell/GHZ 线路的 qubit。”
- “帮我把这个 PyTorch 训练循环接上 `QuantumLayer`。”

## 安装此 skill

先把仓库放到本地，再把它链接或复制到你的 skill 目录。

```bash
git clone https://github.com/IAI-USTC-Quantum/quantum-computing.skill.git
mkdir -p ~/.Agents/skills
ln -s /path/to/quantum-computing.skill ~/.Agents/skills/quantum-computing
```

如果你已经有自己的共享 skills 目录，就安装到那个目录里。

安装完成后，Agent 就可以从 `SKILL.md` 和 `references/` 里读取更具体的操作规则、主题说明和排障步骤。

## 仓库内容

- `SKILL.md`：主入口，包含触发条件、操作规则和导航
- `references/`：按主题整理的使用说明与排障参考
- `examples/`：可复用的示例代码
- `scripts/`：环境检查和辅助脚本

## 通过 ClawHub 安装（推荐）

```bash
# 访问 https://clawhub.ai/agony5757/quantum-computing 获取安装命令
```

ClawHub 支持直接从云端一键安装或克隆本 skill。

## 通过 SkillHub 发布

本 skill 已发布至 [SkillHub](https://www.skillhub.cn/skills/quantum-computing)，一个面向 AI Agent 的 Skill 市场，支持从云端直接安装。

## 许可证

Apache 2.0 许可证
