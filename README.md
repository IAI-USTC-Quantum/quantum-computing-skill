# quantum-computing-skill

面向 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 的本地 skill 仓库。

这个仓库只负责 skill 本体，不负责充当上游源码镜像或完整 API 手册。

## 安装此 skill

先把仓库放到本地，再把它链接或复制到你的 skill 目录。

一种通用安装方式：

```bash
mkdir -p ~/.agents/skills
ln -s /path/to/quantum-computing-skill ~/.agents/skills/quantum-computing-skill
```

如果你已经有自己的共享 skills 目录，就安装到那个目录里。

这个 README 不展开 `unified-quantum` 本身的安装、`uniqc` CLI 的调用方式或各类 extras。那些决定应该由调用此 skill 的 agent 在交互过程中按环境自动处理，并在需要改动用户环境前与用户确认。

## 仓库职责

- `README.md`：给人看的入口，只介绍 skill 的安装方式和仓库职责
- `SKILL.md`：给 agent 看的主入口，负责触发条件、操作规则和导航
- `references/`：按主题存放细节；各功能主题自己的排错优先写在对应 reference，通用兜底排错放在 `references/troubleshooting.md`
- `examples/`：可复用示例
- `scripts/`：检查和辅助脚本

## 这个仓库不负责什么

- 不维护 `UnifiedQuantum` 上游源码
- 不提供完整 API 镜像文档
- 不承诺所有可选功能都在任何环境里默认可用

## 许可证

Apache 2.0 许可证
