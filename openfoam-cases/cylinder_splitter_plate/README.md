# 圆柱后置分流板：短时尾迹、受力及后处理

体积无限公众号文章对应的自建二维 OpenFOAM 算例。包含裸圆柱与圆柱—分流板两组设置，以及升阻力系数换算和时间统计脚本。

求解器、网格工具、壁面受力积分均使用 OpenFOAM 自带实现；本目录提供计算设置、运行组织及新增的 Python 数据分析。它不是官方 tutorials 中的原生案例。

## 文件结构

- `baseline/`：裸圆柱输入，含局部横向初始扰动。
- `splitter_plate/`：零厚度后置分流板输入，无横向初始扰动。
- `scripts/postprocess_forces.py`：读取受力记录、换算系数并计算时间窗口统计；与文章所附脚本一致，无绘图功能。
- `scripts/test_postprocess.py`：用人工构造的简单受力记录检查换算、时间积分与异常输入处理。
- `Allrun` / `Allpost`：运行和后处理入口。

## 环境与运行

对应版本为 OpenFOAM v2606（openfoam.com 分支），后处理需要 Python 3 和 NumPy 2.0 或更新版本。先加载本机 OpenFOAM 环境，随后在一个未运行过的项目副本中执行：

```sh
python3 -m pip install -r requirements.txt
chmod +x Allrun Allpost
./Allrun
./Allpost --start 1 --end 2
```

`Allrun` 为每组生成网格、检查网格并调用 `pimpleFoam`；裸圆柱在运行前还调用 `setFields`。检测到已有生成网格或受力结果时，脚本退出以保留现有内容。

只处理已有的受力文件时：

```sh
python3 scripts/postprocess_forces.py path/to/force.dat --start 1 --end 2
```

脚本向终端输出 JSON，可用标准输出重定向自行保存。

## 计算条件

| 项目 | 设置 |
|---|---|
| 求解器与流动模型 | pimpleFoam，二维不可压缩层流 |
| 圆柱直径 D | 0.02 m |
| 分流板长度 | 0.05 m（2.5D） |
| 来流速度 | 0.15 m/s |
| 运动黏度 | 2.0×10⁻⁵ m²/s |
| 雷诺数 | 150 |
| 展向厚度 | 0.005 m，前后 empty |
| 单组单元数 | 11600，由 blockMeshDict 重建 |
| 终止时间 | 2 s |
| 自适应时间步 | maxCo 0.5，maxDeltaT 0.002 s |

分流板从圆柱后驻点沿中心线向下游延伸，板两侧为无滑移壁面。其重合顶点与两侧壁面已写在 `splitter_plate/system/blockMeshDict` 中，不需要额外调用 `createBaffles`。

### 两组初始条件

裸圆柱的 `system/setFieldsDict` 在指定盒区域内令 U=(0.15, 0.03, 0) m/s，其余位置为 (0.15, 0, 0) m/s。分流板组初始横向速度为零。裸圆柱发布输入中的 `0/U` 保留均匀默认值，再由 `setFields` 重建这一局部扰动，避免提交可重建的逐单元初值列表。

两组初场不同，本文展示的是这些设置下的短时结果。解读载荷和尾迹差异时，应同时考虑几何和初始扰动。

## 壁面受力与后处理

`forces` 功能对象在 `system/controlDict` 中启用。裸圆柱积分 `cylinder`，分流板组积分 `cylinder splitterPlate`；后者是组合构型的总力。

脚本按本文版本的十列 `force.dat` 读取：

```text
time total_x total_y total_z pressure_x pressure_y pressure_z viscous_x viscous_y viscous_z
```

它检查列数、有限值、时间严格递增，以及总力是否等于压力作用力与黏性力之和。不能将其他列布局的文件直接代入。

参考密度为 1 kg/m³，参考速度为 0.15 m/s，参考面积为 D×展向厚度=0.0001 m²，力的归一化分母为 1.125×10⁻⁶ N。x 方向总力除以这一分母得到 Cd，y 方向得到 Cl。

时间统计默认取 1～2 s。脚本在线性插值补齐窗口端点后，用梯形积分计算 Cd 的时间平均；`Cl_half_peak_to_peak` 为窗口内 Cl 极差的一半，区别于均方根值。输出还包含 Cd、Cl 的取值范围。

如改动算例物性、速度、几何或受力方向，应同步检查脚本顶部的 `rho`、`u_ref`、`area_ref` 和所读取的力方向。

## 检查与文章结果

```sh
python3 scripts/test_postprocess.py
```

文章原计算在 1～2 s 窗口内的 Cd 时间平均值约为：裸圆柱 1.4262、组合构型 1.2232；Cl 半峰峰值约为 0.49925 和 2.2090×10⁻⁵。这些是原计算的历史结果，运行条件及受力范围见上文。

本次发布包在 OpenFOAM v2606 中检查网格重建、初场重建与求解器启动；后处理另用文章保留的原始受力记录及合成测试核对。发布前没有重新推进两组完整的 2 s 计算。

仓库不包含生成网格、计算结果、日志、图片视频或私人路径。保留输入文件原有的 OpenFOAM 文件头；OpenFOAM 本身的版权与许可归上游项目。
