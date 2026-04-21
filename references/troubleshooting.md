# 通用排错参考

这份说明用于**各个功能主题自己的排错步骤仍不够时**的通用兜底排查。

优先顺序应当是：

1. 先看当前问题对应的功能 reference
2. 如果功能内排查仍解释不了，再回到这里做通用诊断

遇到这些情况时，优先查这里：

- 功能文档里的排错已经做过，但问题仍解释不通
- 文档里的命令、导入路径、配置文件位置和本地安装对不上
- 某个功能在 skill 里提到，但用户环境里“没有这个命令 / 没有这个模块 / 没有这个 extra”
- 同一份示例在不同机器上，一个能跑、一个提示参数名或模块名不存在

## 先确认问题是不是功能专属

这份文档不替代功能主题内的局部排错。常见入口：

- CLI / 命令参数 / shell 工作流：`references/cli-guide.md`
- 本地模拟 / dummy / simulation 依赖：`references/simulators.md`
- 云平台 / token / task cache / dummy 提交：`references/cloud-platforms.md`
- HEA / QAOA / UCCSD / VQE：`references/variational-algorithms.md`
- PyTorch 辅助工具：`references/pytorch-integration.md`

如果这些局部文档已经看过，仍然解释不了问题，再继续下面的通用步骤。

## 通用排查顺序

推荐顺序：

1. 先确认解释器、版本号、模块路径
2. 再确认是不是少装了对应 extra 或第三方依赖
3. 再确认用户看的文档和当前安装是否属于同一来源
4. 还不清楚时，再去看对应 release notes / changelog

## 先确认安装来源与版本

排错前不要假设用户装的是 PyPI 发布版。至少先回答三个问题：

- 当前用的是哪个解释器
- `unified-quantum` 显示的版本号是什么
- `uniqc` 或相关模块实际从哪里导入

最小检查命令：

```bash
python3 - <<'PY'
from importlib.metadata import version
import sys

print("exe=", sys.executable)

try:
    import uniqc
except ModuleNotFoundError:
    print("module= <uniqc not importable>")
else:
    print("module=", uniqc.__file__)

try:
    print("version=", version("unified-quantum"))
except Exception as exc:
    print("version_probe_failed=", repr(exc))
PY
```

如果用户使用的是项目虚拟环境、`uv tool` 或其他解释器，要改用对应解释器执行这条命令。

## 如何解读结果

结果通常可以分成三类：

- **PyPI / wheel 安装**：模块路径位于 `site-packages`
- **源码 editable 安装但对齐某个 release/tag**：模块路径指向源码目录，版本号通常仍是正式版本
- **源码 editable 安装且跟随主线**：模块路径指向源码目录，版本号可能带 `dev`，或者与已发布行为不一致

这里最重要的是：**以当前解释器真正导入到的包为准**，不要只看用户在哪个源码目录里开了终端，也不要只看仓库 README。

## 再确认依赖和入口是否对齐

很多“看起来像程序问题”的情况，其实只是解释器、CLI 入口或可选依赖没对齐。优先检查：

- 当前 shell 里的 `uniqc` 和你用来 `import uniqc` 的解释器是不是同一套环境
- 需要模拟、dummy、PyTorch、云平台适配器时，有没有装对应 extra
- 用户是不是把主线源码 README、历史笔记或旧示例，当成了当前安装版本的真实能力

如果需要快速做一次环境体检，可以运行：

```bash
bash scripts/setup_uniqc.sh
```

它更适合回答这些通用问题：

- `uniqc` 能不能启动
- `import uniqc` 是否成功
- 基础依赖是否缺失
- simulation / PyTorch / scikit-learn 等常见可选能力是否可用

## 何时再去看 release notes / changelog

只有在已经确认“当前解释器里装的到底是什么”之后，才去查对应的 release notes、tag 或 changelog。

如果已经确认用户直接在 `UnifiedQuantum` 源码 checkout 里工作，且还需要判断“当前代码大致落在哪个 tag 附近”，才额外使用：

```bash
git describe --tags --always
```

它只是辅助判断源码树和最近 tag 的相对位置，不能替代“当前解释器里实际导入了哪个版本”的检查。

## 常见排错思路

- 缺命令、缺导入、缺 extra 时，先确认是不是装错了解释器或少装了可选依赖
- `uniqc` 能运行但 `import uniqc` 失败，或反过来时，优先怀疑不是同一个环境
- 文档和本地行为不一致时，先确认用户看的到底是 release 文档、源码主线 README，还是别人的旧笔记
- 如果模块路径指向源码目录，不要立刻把 README 上写的能力当成“当前环境一定具备”
- 如果模块路径指向 `site-packages`，但用户拿的是主线源码说明，优先怀疑“文档比安装版本新”
- 不要先入为主地判定“包坏了”或“skill 过时了”；很多问题只是安装来源和参考文档不一致

## 给 skill 文档的写法约束

- 功能专属问题优先留在对应功能 reference 里，不要全都堆到这里
- 这里保留通用排错顺序、环境诊断、版本识别和文档对齐方法
- 需要解释功能差异时，优先引导去看与当前安装来源匹配的官方 release notes / changelog
- 不再维护手工版本断点表；只有当某个识别步骤本身会影响排障时，才写进 skill 文档
