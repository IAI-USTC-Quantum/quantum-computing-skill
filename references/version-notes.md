# Version Notes

这份说明只记录**会影响使用和排障**的版本断点，不复写 UnifiedQuantum 的完整 changelog。

遇到这些情况时，优先查这里：

- 文档里的命令、导入路径、配置文件位置和本地安装对不上
- 某个功能在 skill 里提到，但用户环境里“没有这个命令 / 没有这个模块 / 没有这个 extra”
- 同一份示例在不同机器上，一个能跑、一个提示参数名或模块名不存在

## 先确认安装来源与版本

排错前不要假设用户装的是 PyPI 发布版。至少先回答三个问题：

- 当前用的是哪个解释器
- `unified-quantum` 显示的版本号是什么
- `uniqc` / `uniq` 模块实际从哪里导入

最小检查命令：

```bash
python3 -c "from importlib.metadata import version; import uniqc, sys; print('exe=', sys.executable); print('version=', version('unified-quantum')); print('module=', uniqc.__file__)"
```

如果用户使用的是项目虚拟环境、`uv tool` 或其他解释器，要改用对应解释器执行这条命令。

结果通常可以分成三类：

- **PyPI / wheel 安装**：模块路径位于 `site-packages`
- **源码 editable 安装但对齐 release tag**：模块路径指向某个源码目录，版本号通常是正式版本
- **源码 editable 安装且跟随主线**：模块路径指向源码目录，版本号可能带 `dev`，或与最近 release 行为不一致

如果已经确认用户直接在 `UnifiedQuantum` 源码 checkout 里工作，且还需要判断“当前代码大致落在哪个 tag 附近”，才额外使用：

```bash
git describe --tags --always
```

它只是辅助判断源码树和最近 tag 的相对位置，不能替代“当前解释器里实际导入了哪个版本”的检查。

## 主要版本断点

### `v0.0.4` 及之后：当前公开工作流基线

这是当前 skill 处理公开工作流时的主要参考断点。对使用影响最大的变化有：

- Python 包导入名从 `uniq` 切换为 `uniqc`
- CLI 二进制名从 `uniq` 切换为 `uniqc`
- 默认配置文件路径变为 `~/.uniqc/uniqc.yml`
- 任务缓存统一为 `~/.uniqc/cache/tasks.sqlite`

如果用户环境里出现这些现象，优先怀疑用户当前环境仍停留在 `v0.0.3` 及更早的旧命名空间：

- `uniqc` 命令不存在，但 `uniq` 存在
- `import uniqc` 失败，但 `import uniq` 成功
- 文档写的是 `~/.uniqc/uniqc.yml`，本机只有 `~/.uniq/uniq.yml`

### `v0.0.3` 及更早：旧命名空间

这条线仍可能在旧环境里出现。典型特征：

- Python 导入名仍是 `uniq`
- CLI 名仍是 `uniq`
- 配置路径是 `~/.uniq/uniq.yml`
- 旧文档或旧安装步骤里可能出现 `pip install . --no-cpp`

如果用户拿旧环境去跑当前 skill 的示例，最常见的问题就是命令名、导入名和配置路径全部对不上。

## 未发布但容易造成误判的变化

以下内容已经出现在当前主线源码中，但**不应自动视为所有用户环境都具备**。如果用户装的是 release 包却缺这些功能，先判断是否只是还没发版；如果用户是源码安装，再看他装的是 release tag 还是主线最新代码。

### `v0.0.4` 之后主线新增的 TorchQuantum 相关能力

当前主线已经出现这些新增内容：

- `torchquantum` extra
- `uniqc.algorithmics.training` 训练模块
- TorchQuantum simulator backend
- 一批新的 Torch / hybrid algorithm 示例

如果用户说“README / 技能里提到 TorchQuantum，但我的已发布版本里没有”，优先判断为**主线已实现但尚未正式发布**，不要先判定为安装损坏。

### `--no-cpp` 选项已从主线移除

当前主线已经移除了 `--no-cpp` 相关路径，并回到必须构建 C++ 扩展的方向。

如果用户参考的是较新的源码说明，却安装了较旧版本，或者反过来参考了旧文档却跟着当前主线走，容易在这里混淆。

## 使用建议

- 先识别当前环境是发布版、release tag 源码安装，还是主线源码安装
- 再把用户现象和这里的版本断点对照起来，不要一开始就假设“包坏了”或“skill 过时了”
- 只有当某个未发布能力明显影响排障时，才在回答里额外提一句“这可能是主线已有但尚未发布的变化”
- 如果未来新 release 再次改变公开工作流，只在这里补一条“影响使用的断点”，不要把上游所有 commits 都搬进来
