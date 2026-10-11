# 二维圆柱绕流：Q 准则与脱涡频率

对应体积无限已发表文章《OpenFOAM圆柱绕流：Q准则涡识别与脱涡频率分析》。本目录保存该文章使用的独立圆柱绕流算例设置，不包含已计算的网格和流场。

## 计算设置

- 环境：OpenFOAM v2606，`icoFoam`。
- 圆柱直径 0.1 m，入口速度 1 m/s，运动黏度 0.001 m²/s，雷诺数 100。
- 二维约束，展向厚度 0.01 m。
- 终止时间 30 s，时间步长 0.0025 s，流场保存间隔 0.05 s。
- `system/controlDict` 中的 `forceCoeffs` 每步输出力系数，探针同时记录速度与压力。

## 运行

先加载 OpenFOAM v2606 环境，再在本目录运行：

```sh
sh Allrun
```

`Allrun` 依次生成网格、检查网格和求解。已有网格时会停止，避免覆盖现有计算；重新计算请使用另一份干净副本。

## 后处理

频谱脚本需要 Python 3 和 NumPy。计算结束后运行：

```sh
sh Allpost
```

Q 准则和涡量使用 OpenFOAM 自带功能计算，写入最后一个保存时刻。力系数来自求解时的自带 `forceCoeffs`。Python 脚本分析 10～30 s 的升力信号，去均值、乘汉宁窗，计算单边 FFT，并按窗函数权重和归一化幅值。结果输出到 `analysis/`。

力系数文件默认采用本算例的 `postProcessing/forces/0/coefficient.dat`，时间、阻力和升力分别取第 1、2、5 列；变更输出格式后需核对列号。

```sh
python3 scripts/analyze_fft.py --start 10 --end 30
```

在 ParaView 中打开此目录，读取最后时刻的 `U`、`Q` 和 `vorticity` 可继续绘制云图。频率归一化的参考直径和速度与本算例一致。
