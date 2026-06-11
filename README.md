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
| [`app.py`](app.py) | **Gradio Web 主应用入口** |
| [`evaluate.py`](evaluate.py) | **系统自评测脚本** |
| [`requirements.txt`](requirements.txt) | Python 依赖清单 |
| `core/` | 核心算法模块（检测/预测/预警/配置） |
| `data/` | 数据层（SQLite 数据库封装） |
| `models/` | 模型训练脚本 |
| `dataset/` | 训练数据集与准备工具 |

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
| 视频处理 | **OpenCV** | 视频帧提取 |

### 核心功能

1. **目标检测引擎** — 检测花朵 / 幼果 / 成熟果实
2. **生长阶段判断** — 花期 → 幼果期 → 成熟期 自动识别
3. **产量预测算法** — 不同阶段采用不同修正系数
4. **风险预警** — 与历史同期数据对比，三级预警
5. **历史数据管理** — SQLite 存储，支持 CSV 导入/导出

### 三层架构

```
┌─────────────────────────────────────────┐
│            Gradio Web UI                │  ← 表现层
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

### 启动系统

```bash
python app.py
```

启动后访问 `http://localhost:7860` 即可使用Web界面。

### 系统自评测

```bash
python evaluate.py
```

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

## 🎓 训练自定义模型

1. 准备标注数据集（YOLO格式）
2. 运行数据集准备脚本：
   ```bash
   python dataset/prepare_data.py
   ```
3. 训练模型：
   ```bash
   python models/train.py --data dataset/citrus.yaml --epochs 100 --device cpu
   ```

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
