# XiFDer

体积无限公众号文章对应的 OpenFOAM 自建算例与计算扩展，统一放在 `openfoam-cases` 中。

## 当前项目

- `cylinder_vortex_shedding`：独立二维圆柱算例设置，包含力系数输出、Q 与涡量后处理调用、升力 FFT 分析。
- `cylinder_splitter_plate`：裸圆柱与后置分流板两组输入设置，包含壁面受力输出、升阻力系数换算及时间窗口统计。
- `bai_gosman_wall_interaction`：液滴撞壁的黏附、反弹与飞溅三组完整输入，使用 v2606 内置 BaiGosman 模型，提供独立及批量运行脚本。
- `geko_ml_calibration`：基于官方台阶案例的新增初始化、批量运行、实验误差评价、数据汇总和高斯过程选参脚本。
- `pybfoam_cavity_initialization`：基于官方 cavity 的 NumPy 初始速度写入、OpenFOAM 场梯度运算与数据输出脚本。

两个圆柱项目与液滴撞壁项目包含完整计算设置；其他两个目录提供扩展脚本，依赖各自 README 中列出的上游算例、绑定或参考数据。

Q、涡量、壁面受力、力系数、GEKO 模型、BaiGosman 撞壁模型和有限体积梯度使用 OpenFOAM 自带实现；分流板项目的系数换算和时间统计由所附 Python 脚本完成。新增工作及上游来源在各项目中分别说明。

仓库不包含生成网格、求解结果、图片视频、绘图代码或私人凭据。新增内容按方法与复现价值筛选；保留原有版权声明，不重新指定第三方源码许可证。
