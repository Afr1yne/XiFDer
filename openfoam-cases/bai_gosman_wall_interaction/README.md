# 液滴撞壁：黏附、反弹与飞溅

对应体积无限《液滴撞壁的黏附、反弹与飞溅：OpenFOAM案例》的全部三组输入。使用 OpenFOAM v2606（OpenCFD/Keysight 分支）的 `reactingParcelFoam` 与 `localInteraction` 中的 `BaiGosman` 撞壁模型。

## 三个 case

| 目录 | 预期分支 | 初始速度（m/s） | 液滴温度（K） | Tmelt（K） |
| --- | --- | --- | --- | --- |
| adhesion | 黏附 | (0 0 -2) | 300 | 273.15 |
| rebound | 反弹 | (0 0 -5) | 300 | 400 |
| splash | 飞溅 | (0 0 -10) | 300 | 273.15 |

三组共用 0.10 × 0.05 × 0.10 m 计算域和 20 × 10 × 20 网格（4000 个单元）。液滴直径 1 mm，注入位置 (0.050 0.025 0.09) m，0.01 s 开始注入，持续 0.03 s，`massTotal=0.003 kg`。计算至 0.12 s，每 0.002 s 写出。

三组均采用 `BaiGosman`，由撞壁判据计算后续行为。`rebound` 的 `Tmelt=400 K` 是用于测试该分支的参数，不表示 300 K 水滴的实际相态。注入速度与撞壁法向速度按不同物理时刻区分。

## 环境与模型

先加载已安装的 OpenFOAM v2606 环境，例如 `source /path/to/OpenFOAM-v2606/etc/bashrc`。运行前确认 `reactingParcelFoam`、`blockMesh` 和 `checkMesh` 在 PATH 中。

使用该版本内置的 BaiGosman 实现，无需额外编译本项目。较老版本或 OpenFOAM Foundation 分支不保证支持此字典。本项目提供自建计算设置，不包含求解器或撞壁模型源码。

模型的官方版本说明：[OpenFOAM v2606 solvers and physics](https://www.openfoam.com/news/main-news/openfoam-v2606/solvers-and-physics)。源码位于 `$FOAM_SRC/lagrangian/intermediate/submodels/Kinematic/PatchInteractionModel/LocalInteraction/`。

`thermophysicalProperties` 使用 `reactingMixture` 并声明液态 H2O，为热颗粒和 `SLGThermo` 提供物性。化学反应、相变、欧拉液膜与双向耦合均关闭。底面 `filmWalls` 使用 BaiGosman，其余边界 `sides` 使用 `escape`。

## 运行

在本目录运行：

```sh
# 全部三组
sh Allrun

# 或只运行指定组
sh Allrun rebound splash
```

也可以进入某个 case 后执行 `sh Allrun`。脚本依次调用 `blockMesh`、`checkMesh` 和 `reactingParcelFoam`。OpenFOAM 的 `runApplication` 会保留已有日志；重复运行时请使用一份新复制的输入目录，以免已有日志或 `startFrom latestTime` 影响重算。

## 设置与结果位置

- `0/`：初始连续相场。
- `constant/reactingCloud1Properties`：颗粒受力、注入、撞壁参数及统计输出。
- `constant/parcelInjectionProperties`：注入位置、初始速度、粒径和物性参数。
- `constant/thermophysicalProperties`、`foam.inp`、`foam.dat`：连续相与液体物性依赖；`foam.inp`、`foam.dat` 是输入，需保留。
- `system/blockMeshDict`：几何、网格及边界。
- 运行后 `<time>/lagrangian/reactingCloud1/`：颗粒位置、速度和直径等。
- `log.reactingParcelFoam`、`postProcessing/`：求解日志与撞壁/颗粒统计。

反弹组可在 0.06 s 检查向上的颗粒速度；飞溅组检查新增次生颗粒及粒径减小。撞壁事件计数可重复统计同一个计算颗粒，例如先反弹再逸出，应按边界和事件类型分析。`surfaceFilmModel none` 时，壁面沉积质量记录不等于已求得可解析的液膜厚度场。

## 文件来源与验证范围

三组初始场和物性/数值字典与推文对应的本地计算输入逐文件核对一致。运行脚本改为可移植路径，并增加 `checkMesh`；文件统一为 LF 换行。求解器、曳力和撞壁模型均来自 OpenFOAM，字典中保留原有文件头与来源信息，不重新指定第三方源码许可证。

本目录只提交复现输入和运行脚本。生成网格、非零时刻、并行目录、统计输出、日志、文章和图片视频均不上传。

整理版核验（2026-10-27）：在独立副本中从零运行三组 case，`checkMesh` 均返回 `Mesh OK`，`reactingParcelFoam` 均计算至 0.12 s 并正常 `End`。
