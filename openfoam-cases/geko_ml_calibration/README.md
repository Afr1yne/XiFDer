# GEKO：批量计算、误差评价与高斯过程选参

基于官方 tutorials/incompressible/simpleFoam/backwardFacingStep2D 扩展，保存本次新增的初始化、批量运行、误差评价和选参脚本。GEKO 模型及其 machineLearning 接口来自 OpenFOAM，模型源码未在此重新实现。

## 依赖与模板

加载 OpenFOAM v2606 环境，安装 Python 3、NumPy 和 MPI。此目录只有扩展脚本，需提供已准备好的台阶模板及参考数据。

模板需要生成网格，并含 0.orig、system、constant 等正常求解输入；边界名与 setup_geko_ml_case.sh 中的 inlet、outlet、upperWall、lowerWall、两个 Startup 壁面及 front、back 一致。后处理要求模板输出 Cx、wallShearStress、cp，以及四个速度剖面。直接复制原始教程还不能满足这些输出要求。

evaluate_geko_case.py 按原计算设置读取 postProcessing/sample/2000/ 下 x/H = 1、4、6、10 的文件，文件名为 x_by_h_01_p_U_turbulenceProperties:devReff.xy 等。该文件格式中第 1 列为 y、第 3 列为 Ux；原台阶高度为 0.0127 m、参考速度为 44.2 m/s。更改工况、采样名称或保存时间时，同步核对脚本。

参考目录需要 cf.exp.dat、cp.expnew.dat 和 profiles.exp.dat。对应 Driver 与 Seegmiller 后向台阶实验，使用原数据格式：压力文件通过 bottom wall 区域标题识别下壁数据，速度文件通过 x/H 分区。参考文件不随脚本打包。

## 工作流程

从本目录运行，假设 template 为已准备好的模板、reference 为参考数据目录。新计算目录必须不存在；初始化脚本会在新副本中重置初始条件、清理已有结果并重新分解网格。

    mkdir -p cases
    bash scripts/setup_geko_ml_case.sh template cases/doe_001 0.002 -0.002 8
    bash scripts/run_geko_cases_sequential.sh cases doe_001
    bash scripts/postprocess_geko_case.sh cases/doe_001 "$PWD/scripts/extract_reattachment.py"
    python3 scripts/evaluate_geko_case.py cases/doe_001 reference

setup 脚本启用 GEKO 的两个场接口 Ck、Comega，设置无量纲初始场及边界条件。run 脚本当前固定使用 8 个 MPI 进程，因此上例分解为 8 个子域。示例系数仅演示调用方式，不代表已验证的最优值。

postprocess 脚本重构最后一个时刻，读取下壁坐标、剪切应力和压力系数，输出 wall_data.dat、wall_cp.dat，并计算剪切应力过零位置。模型输出和下壁场必须实际存在。

## 汇总与选参

    python3 scripts/collect_geko_dataset.py cases reference "$PWD/scripts/evaluate_geko_case.py"
    python3 scripts/propose_geko_gp.py cases/training_data.csv

汇总器读取 baseline_GEKO 和 doe_ 开头的计算目录。评价器计算壁面摩擦系数、压力系数及速度剖面的均方根误差；x/H = 1、4、6 的速度剖面参与训练评分，x/H = 10 单独保留。壁面剪切应力按当前下壁法向约定转换为摩擦系数，移植前必须核对符号。

选参器以 Ck、Comega 为输入，使用 RBF 核和高斯过程预测误差，通过期望改进在固定网格上选择下一组系数。候选范围、输入尺度、筛选条件和误差归一化均在源码中明确给出。程序只建议下一组计算参数，不自动证明其效果。

上游源码位置：src/TurbulenceModels/turbulenceModels/RAS/GEKO/GEKO.C。上游版权及许可保持不变，本包不包含 GEKO 源码、实验数据、网格或求解结果。
