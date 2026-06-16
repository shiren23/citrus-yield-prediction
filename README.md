<div align="center">

# 🍊 柑橘产量预测系统

**Citrus Yield Prediction System**

基于计算机视觉与深度学习的智能果园产量预测与风险预警系统

[![Live Demo](https://img.shields.io/badge/%F0%9F%8E%AF%20Live%20Demo-Click%20Here-orange?style=for-the-badge)](https://shiren23.github.io/citrus-yield-prediction/)
[![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-brightgreen?style=flat-square)](https://pages.github.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)](https://python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-8A2BE2?style=flat-square)](https://docs.ultralytics.com)

</div>

---

## 📖 在线文档

> 点击下方链接查看渲染后的页面：

| 页面 | 链接 |
|:---:|:---:|
| 设计文档 | 👉 [查看](https://shiren23.github.io/citrus-yield-prediction/) |
| 协作指南 | 👉 [查看](https://shiren23.github.io/citrus-yield-prediction/contributing.html) |

---

## 📂 项目文件

| 文件/目录 | 说明 |
|------|------|
| [`index.html`](index.html) | 可视化设计文档（在线渲染页面） |
| [`contributing.html`](contributing.html) | 协作指南（在线渲染页面） |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 协作指南（Markdown 源文件） |
| [`2026-05-14-citrus-yield-prediction-design.md`](2026-05-14-citrus-yield-prediction-design.md) | 完整设计文档（Markdown 源文件） |
| [`app.py`](app.py) | **Gradio Web 主应用入口**（支持模型热切换） |
| [`cli.py`](cli.py) | **命令行工具**（快速预测，无需启动Web） |
| [`evaluate.py`](evaluate.py) | **系统自评测脚本** |
| [`validate_models.py`](validate_models.py) | **模型验证脚本** |
| [`requirements.txt`](requirements.txt) | Python 依赖清单 |
| `core/` | 核心算法模块（检测/预测/预警/配置） |
| `data/` | 数据层（SQLite 数据库封装） |
| `models/` | 模型训练脚本 + 训练好的权重 |
| `models/citdet_best.pt` | **成熟果实检测模型**（CitDet 微调，mAP@50=0.745） |
| `models/flowers_best.pt` | **花朵检测模型**（Roboflow 微调，mAP@50=0.608） |
| `dataset/` | 训练数据集与准备工具 |
| `sample_data/` | 示例图片 |
| [`DATASETS.md`](DATASETS.md) | 数据集引用与说明 |

---

## 🏗️ 系统概述

### 项目背景

面向 **重庆地区柑橘种植场景**（奉节脐橙、忠县柑橘等），系统接受果树图片或视频输入，通过 YOLOv8 目标检测识别花朵和果实，结合生长阶段进行产量预测，并提供低产风险预警。

### 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 目标检测 | **YOLOv8n** (Ultralytics) | 轻量级，适合实时检测 |
| 深度学习框架 | **PyTorch** | YOLOv8 原生支持 |
| Web 界面 | **Gradio** | 快速构建 ML 应用 UI |
| 数据库 | **SQLite** | 轻量嵌入式，无需额外服务 |
| 可视化 | **Matplotlib / Plotly** | 历史趋势图表 |
| 视频处理 | **OpenCV** | 视频帧提取与采样检测 |

### 核心功能

1. **🎯 目标检测引擎** — 检测花朵 / 幼果 / 成熟果实（支持图片和视频）
2. **🌱 生长阶段判断** — 花期 → 幼果期 → 成熟期 自动识别
3. **📈 产量预测算法** — 不同阶段采用不同修正系数
4. **⚠️ 风险预警** — 与历史同期数据对比，三级预警
5. **📊 历史数据管理** — SQLite 存储，支持 CSV 导入/导出
6. **🏡 果园管理** — 创建、删除果园，分类管理检测数据
7. **🖥️ 命令行工具** — 无需启动Web界面即可快速预测
8. **🔄 模型热切换** — Web 界面支持实时切换检测模型（果实/花朵）

### 三层架构

```
┌─────────────────────────────────────────┐
│            Gradio Web UI / CLI          │  ← 表现层
├─────────────────────────────────────────┤
│  YOLOv8 │ 产量预测 │ 风险预警 │ ...     │  ← 业务层
├─────────────────────────────────────────┤
│      SQLite + CSV + 模型权重            │  ← 数据层
└─────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python >= 3.9
- PyTorch >= 2.0
- 4GB+ 内存（CPU运行）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动Web界面

```bash
python app.py
```

启动后访问 `http://localhost:7860` 即可使用Web界面。

### 命令行快速预测

```bash
# 图片预测
python cli.py --image sample_data/sample_00.jpg --variety 奉节脐橙 --trees 5

# 视频预测
python cli.py --video sample.mp4 --variety 忠县柑橘 --trees 10

# 保存结果为JSON
python cli.py --image sample_data/sample_00.jpg --output result.json --save-db

# 查看所有参数
python cli.py --help
```

### 系统自评测

```bash
python evaluate.py
```

---

## 🪟 Windows 部署指南

### 环境准备

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10/11 | Windows 11 |
| Python | 3.9+ | 3.11 ~ 3.13 |
| 内存 | 8GB | 16GB |
| GPU | 可选（CPU 可跑） | NVIDIA RTX 4060 及以上 |
| 显存 | — | 8GB+ |
| 硬盘空间 | 10GB | 20GB+ |

### 步骤一：安装 Python

1. 访问 [python.org](https://www.python.org/downloads/) 下载 Python 3.11+
2. **安装时务必勾选** `"Add Python to PATH"`
3. 打开 PowerShell 验证安装：
   ```powershell
   python --version
   # 应显示 Python 3.11.x 或更高版本
   ```

### 步骤二：克隆项目

```powershell
# 使用 Git 克隆（需先安装 Git）
git clone https://github.com/shiren23/citrus-yield-prediction.git
cd citrus-yield-prediction

# 或使用 GitHub Desktop 下载 ZIP 后解压
```

### 步骤三：安装依赖

```powershell
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装基础依赖
pip install -r requirements.txt
```

> **CUDA 加速（可选）**：如果你有 NVIDIA 显卡，建议安装 CUDA 版 PyTorch 以获得 10~15 倍速度提升：
> ```powershell
> pip uninstall torch torchvision -y
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
> ```
> 验证 CUDA 是否可用：
> ```powershell
> python -c "import torch; print(torch.cuda.is_available())"
> # 输出 True 表示 GPU 可用
> ```

### 步骤四：下载预训练模型（自动）

项目中已包含我们训练好的模型：
- `models/citdet_best.pt` — 成熟果实检测
- `models/flowers_best.pt` — 花朵检测

若缺失 `yolov8n.pt`（基础预训练模型），首次运行时会自动从 Ultralytics 下载。

### 步骤五：启动系统

```powershell
# 方式 1：启动 Web 界面
python app.py
# 浏览器访问 http://localhost:7860

# 方式 2：命令行快速预测
python cli.py --image sample_data/sample_00.jpg --variety 奉节脐橙 --trees 5
```

### 步骤六：模型切换（Web 界面）

打开 `http://localhost:7860` 后：
1. 进入 **📸 图片预测** 或 **🎬 视频预测** Tab
2. 在 **🧠 检测模型** 下拉框中选择：
   - `成熟果实检测 (CitDet微调)` — 检测树上/地面的柑橘果实
   - `花朵检测 (Roboflow微调)` — 检测白色柑橘花朵
   - `通用预训练 (YOLOv8n)` — 通用 80 类物体检测
3. 上传图片，点击 **🚀 开始预测**

> 💡 切换模型时会自动释放旧模型显存并加载新模型，无需重启应用。

### 常见问题

| 问题 | 解决方案 |
|------|---------|
| `pip install` 报错权限不足 | 以管理员身份运行 PowerShell，或使用 `--user` 参数 |
| `torch.cuda.is_available()` 为 False | 检查 NVIDIA 驱动是否安装，或改用 CPU 运行（将 `--device 0` 改为 `--device cpu`） |
| 启动时提示端口 7860 被占用 | 关闭其他 Gradio 应用，或修改 `app.py` 中的 `server_port` |
| 模型加载缓慢 | 首次启动需要解压模型，等待 1~2 分钟即可 |

---

## 🧠 算法说明

### 生长阶段判断

| 阶段 | 判断条件 |
|------|---------|
| **花期** | 花朵占比 > 60% |
| **幼果期** | 幼果占比 > 50% |
| **成熟期** | 成熟果占比 > 50% |

### 产量预测公式

| 阶段 | 公式 |
|------|------|
| 花期 | `产量 = 花量 × 坐果率 × 平均单果重` |
| 幼果期 | `产量 = 幼果数 × 成活率 × 平均单果重` |
| 成熟期 | `产量 = 果实数 × 平均单果重 × (1-落果率)` |

### 风险预警规则

| 等级 | 条件 | 标识 |
|------|------|------|
| 严重低产 | 当前 < 历史均值 × 60% | 🔴 |
| 低产风险 | 当前 < 历史均值 × 80% | ⚠️ |
| 产量正常 | 当前 ≥ 历史均值 × 80% | ✅ |

---

## 🍋 支持品种

| 品种 | 平均单果重 | 坐果率 | 幼果成活率 |
|------|-----------|--------|-----------|
| 奉节脐橙 | 250g | 8% | 60% |
| 忠县柑橘 | 200g | 10% | 65% |
| 万州红桔 | 150g | 12% | 70% |
| 通用柑橘 | 200g | 10% | 65% |

---

## 🎯 已训练模型

本项目基于公开数据集训练了两个专用检测模型，均可在 Web 界面中实时切换：

### 模型一：成熟果实检测（CitDet 微调）

| 指标 | 数值 |
|------|------|
| 数据集 | CitDet（579 张训练/验证图） |
| 训练设备 | NVIDIA RTX 4060 Laptop GPU |
| mAP@50 | **0.745** |
| mAP@50-95 | 0.368 |
| 精确率 (P) | 0.801 |
| 召回率 (R) | 0.676 |
| 训练耗时 | ~6 分钟（50 epochs） |
| 权重文件 | `models/citdet_best.pt` |

### 模型二：花朵检测（Roboflow 微调）

| 指标 | 数值 |
|------|------|
| 数据集 | orange flowers（Roboflow Universe, 226 张图） |
| 训练设备 | NVIDIA RTX 4060 Laptop GPU |
| mAP@50 | **0.608** |
| mAP@50-95 | 0.288 |
| 精确率 (P) | 0.553 |
| 召回率 (R) | 0.660 |
| 训练耗时 | ~2.5 分钟（50 epochs） |
| 权重文件 | `models/flowers_best.pt` |

### 训练自己的模型

```bash
# 成熟果实（CitDet）
python dataset/convert_citdet.py
python models/train.py --data dataset_citdet/citdet.yaml --epochs 50 --batch 8 --device 0

# 花朵（需先从 Roboflow 下载数据集）
python models/train.py --data "opensource_dataset/orange flowers.v2i.yolov8/data.yaml" --epochs 50 --batch 8 --device 0
```

---

## 🎓 数据集引用

本项目模型训练引用了以下公开数据集：

### CitDet
> **CitDet: A Benchmark Dataset for Citrus Fruit Detection**  
> Jordan A. James, et al. IEEE Robotics and Automation Letters (RA-L), 2024.  
> [GitHub](https://github.com/robotic-vision-lab/CitDet-A-Benchmark-Dataset-For-Citrus-Fruit-Detection) | [arXiv](https://arxiv.org/abs/2309.05645) | [官网](https://robotic-vision-lab.github.io/citdet)

### Orange Flowers (Roboflow Universe)
> **orange flowers Computer Vision Model**  
> by am. Roboflow Universe, CC BY 4.0.  
> [下载页面](https://universe.roboflow.com/am-dczhc/orange-flowers-wdjqc/dataset/2)

详见 [`DATASETS.md`](DATASETS.md) 获取完整引用格式。

---

## 👥 分工建议

| 角色 | 负责内容 | 对应目录 |
|------|---------|---------|
| 成员 A | 模型训练、微调、数据集准备 | `models/`, `dataset/` |
| 成员 B | 核心算法、数据库、后端逻辑 | `core/`, `data/` |
| 成员 C | Gradio 界面、可视化、报告撰写 | `app.py`, `docs/` |

---

## 📄 License

MIT License

---

<div align="center">

**[设计文档](https://shiren23.github.io/citrus-yield-prediction/)** · **[协作指南](https://shiren23.github.io/citrus-yield-prediction/contributing.html)**

</div>
