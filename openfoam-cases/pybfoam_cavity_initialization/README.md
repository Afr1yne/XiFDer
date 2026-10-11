# pybFoam：Python 初始场写入与场运算

基于官方 tutorials/incompressible/icoFoam/cavity/cavity，新增 Python 初始化与求解后场运算。官方算例本体和 pybFoam 绑定不重复打包。

## 依赖

OpenFOAM v2606、与该版本兼容的 pybFoam、Python 3 和 NumPy。Python 必须能加载 pybFoam 的二进制模块；使用安装绑定时对应的解释器及 OpenFOAM 环境。

## 初始化与计算

从本目录运行，先加载 OpenFOAM 环境。将教程复制到一个不存在的新目录，例如：

    mkdir -p cases
    cp -a "$FOAM_TUTORIALS/incompressible/icoFoam/cavity/cavity" cases/python_cavity
    python3 scripts/01_prepare.py cases/python_cavity
    icoFoam -case cases/python_cavity

初始化脚本读取网格生成字典，生成网格，取得速度内场的 NumPy 视图，然后写入解析速度分布，并修正边界条件。方形域边长在脚本中固定为 0.1 m；使用其他几何时需修改此参数。

速度分布为 Ux = sin(πx/L) cos(πy/L)、Uy = −cos(πx/L) sin(πy/L)、Uz = 0。本脚本保留教程边界条件，会修改工作副本的初始速度场，不用于已有计算结果的原目录。

## 场运算

    python3 scripts/02_postprocess.py cases/python_cavity

脚本读取最后一个正时间的速度场，调用 OpenFOAM 的 fvc.grad 并写出 grad(U)。由速度梯度计算平面外涡量，导出 pythonResults/vorticity_z.csv；同时在离 x = 0.05 m 最近的单元中心列提取速度剖面，写出 pythonResults/vertical_midline_Ux.csv。该剖面使用单元中心采样，不是对 x = 0.05 m 截面的插值。

仓库整理保留原脚本的初始化、梯度与涡量计算、剖面提取，移除绘图依赖与图片输出，并将已有涡量计算结果改为 CSV 输出。此目录提供实际场操作示例，求解器及梯度离散运算来自 OpenFOAM。
