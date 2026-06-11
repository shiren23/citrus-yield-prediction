# 柑橘产量预测系统设计文档

## 概述

### 项目背景
基于计算机视觉的柑橘果园产量预测系统，面向重庆地区柑橘种植场景（奉节脐橙、忠县柑橘等）。系统接受果树图片或视频输入，通过目标检测识别花朵和果实，结合生长阶段进行产量预测，并提供低产风险预警。

### 目标
1. 实现柑橘花朵、幼果、成熟果实的自动检测
2. 支持不同生长阶段的产量预测（早期花量预测 → 幼果期修正 → 成熟期矫正）
3. 提供低产风险预警功能
4. 提供简洁易用的 Web 界面

### 约束
- 技术栈：Python 全栈（PyTorch + YOLOv8 + Gradio + SQLite）
- 团队规模：2-3人小组
- 目标水果：柑橘（重庆地区）
- 需有自主功能设计和算法实现，不能直接照搬开源代码

---

## 系统架构

### 总体架构（三层）

```
┌─────────────────────────────────────────────────┐
│                  Gradio Web UI                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 图片/视频 │ │ 产量报告  │ │ 历史趋势 & 预警  │ │
│  │  上传组件  │ │  展示组件  │ │   展示组件       │ │
│  └─────┬────┘ └─────▲────┘ └───────▲──────────┘ │
└────────┼────────────┼──────────────┼─────────────┘
         │            │              │
┌────────▼────────────┼──────────────┼─────────────┐
│              核心业务层 (Python)                    │
│  ┌───────────┐ ┌────────────┐ ┌───────────────┐  │
│  │ YOLOv8    │ │ 产量预测    │ │ 风险预警      │  │
│  │ 检测引擎  │→│ 计算模块    │→│ 判断模块      │  │
│  └───────────┘ └────────────┘ └───────────────┘  │
│  ┌───────────┐ ┌────────────┐                    │
│  │ 生长阶段  │ │ 历史数据    │                    │
│  │ 识别模块  │ │ 管理模块    │                    │
│  └───────────┘ └────────────┘                    │
└──────────────────────────────────────────────────┘
         │                           │
┌────────▼───────────────────────────▼─────────────┐
│           数据层 (SQLite + CSV)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 检测记录  │ │ 历史产量  │ │  模型权重文件     │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────────────────────────────────────┘
```

### 技术选型

| 层次 | 技术 | 说明 |
|------|------|------|
| 目标检测 | YOLOv8n (Ultralytics) | 轻量级，适合实时检测 |
| 深度学习框架 | PyTorch | YOLOv8 原生支持 |
| Web界面 | Gradio | 快速构建 ML 应用 UI |
| 数据库 | SQLite | 轻量嵌入式，无需额外服务 |
| 可视化 | Matplotlib / Plotly | 历史趋势图表 |
| 视频处理 | OpenCV | 视频帧提取 |

---

## 核心功能模块

### 模块1：目标检测引擎

**职责**：检测图片/视频帧中的柑橘花朵和果实

**检测类别**：
- `flower`：花朵（用于早期预测）
- `immature_fruit`：幼果（用于中期修正）
- `mature_fruit`：成熟果实（用于成熟期矫正）

**模型微调流程**：
1. 收集公开柑橘数据集 + 自采集图片
2. 使用 LabelImg 或 Roboflow 进行标注
3. 转换为 YOLO 格式
4. 基于 YOLOv8n 预训练权重 fine-tune（50-100 epochs）
5. 验证 mAP ≥ 0.7

**视频处理**：
- 使用 OpenCV 按帧提取
- 每隔 N 帧采样一次（避免冗余计算）
- 汇总多帧检测结果取均值

### 模块2：生长阶段判断

**职责**：根据检测结果自动判断当前生长阶段

| 阶段 | 判断条件 | 预测方式 |
|------|---------|---------|
| 花期 | flower 占比 > 60% | 花量 × 经验坐果率 × 平均果重 |
| 幼果期 | immature_fruit 占比 > 50% | 幼果数 × 成活率 × 平均果重 |
| 成熟期 | mature_fruit 占比 > 50% | 果实数 × 平均果重（矫正值） |

### 模块3：产量预测算法

**核心公式**：
```
yield_estimate = detected_count × correction_factor × avg_fruit_weight
```

**各阶段 correction_factor**：
- 花期：坐果率（约 5-15%，视品种和气候）
- 幼果期：落果后成活率（约 50-70%）
- 成熟期：接近 1.0（用于最终矫正）

**品种参数配置**（可扩展）：
```python
CITRUS_CONFIG = {
    "奉节脐橙": {"avg_weight_kg": 0.25, "flower_fruit_rate": 0.08, "immature_survival_rate": 0.60},
    "忠县柑橘": {"avg_weight_kg": 0.20, "flower_fruit_rate": 0.10, "immature_survival_rate": 0.65},
}
```

### 模块4：风险预警

**职责**：将当前检测数量与历史同期数据对比，发出预警

**预警规则**：
- 当前检测数量 < 历史同期均值 × 0.8 → ⚠️ 低产风险提示
- 当前检测数量 < 历史同期均值 × 0.6 → 🔴 严重低产预警
- 当前检测数量 ≥ 历史同期均值 × 0.8 → ✅ 产量正常

**无历史数据时**：基于品种平均值的合理范围给出参考建议

### 模块5：历史数据管理

**数据库表设计**：

```sql
-- 果园/树木基本信息
CREATE TABLE orchard_info (
    id INTEGER PRIMARY KEY,
    name TEXT,           -- 果园名称
    variety TEXT,        -- 柑橘品种
    tree_count INTEGER,  -- 树木数量
    location TEXT,       -- 地理位置
    created_at DATETIME
);

-- 检测记录
CREATE TABLE detection_records (
    id INTEGER PRIMARY KEY,
    orchard_id INTEGER,
    image_path TEXT,       -- 原始图片路径
    stage TEXT,            -- 生长阶段
    flower_count INTEGER,
    immature_count INTEGER,
    mature_count INTEGER,
    predicted_yield REAL,  -- 预测产量(kg)
    confidence REAL,       -- 置信度
    risk_level TEXT,       -- 风险等级
    detected_at DATETIME,
    FOREIGN KEY (orchard_id) REFERENCES orchard_info(id)
);

-- 历史实际产量
CREATE TABLE history_yield (
    id INTEGER PRIMARY KEY,
    orchard_id INTEGER,
    year INTEGER,
    season TEXT,          -- 采摘季节
    actual_yield REAL,    -- 实际产量(kg)
    recorded_at DATETIME,
    FOREIGN KEY (orchard_id) REFERENCES orchard_info(id)
);
```

---

## Gradio Web 界面

### Tab 1：产量预测（主页面）

- 图片/视频上传组件（支持拖拽）
- 果园编号下拉选择 + 拍摄日期选择器
- 检测结果可视化（标注后的图片，框出花朵/果实）
- 预测报告卡片（检测阶段、数量、预测产量、置信度、风险等级）
- 保存记录按钮

### Tab 2：历史趋势

- 折线图：按时间展示预测产量变化趋势
- 柱状图：不同年份同期对比
- 预警时间线：标注低产风险的时间点

### Tab 3：数据管理

- 导入/导出 CSV 历史数据
- 录入实际采摘产量（用于矫正预测模型）
- 查看/编辑检测记录表格

### Tab 4：关于/帮助

- 系统说明
- 使用教程
- 算法原理简介

---

## 项目目录结构

```
citrus-yield-prediction/
├── app.py                    # Gradio 主应用入口
├── requirements.txt          # Python 依赖
├── README.md
│
├── models/                   # 模型相关
│   ├── train.py              # YOLOv8 微调训练脚本
│   ├── predict.py            # 检测推理封装
│   ├── best.pt               # 微调后的模型权重
│   └── yolov8n.pt            # 基础预训练权重
│
├── core/                     # 核心业务逻辑
│   ├── detector.py           # 目标检测引擎
│   ├── yield_estimator.py    # 产量预测算法
│   ├── stage_classifier.py   # 生长阶段判断
│   ├── risk_alert.py         # 风险预警模块
│   └── config.py             # 参数配置（果重、坐果率等）
│
├── data/                     # 数据层
│   ├── database.py           # SQLite 操作封装
│   ├── citrus.db             # SQLite 数据库
│   └── sample_data/          # 示例图片/视频
│
├── dataset/                  # 训练数据集
│   ├── images/
│   │   ├── train/
│   │   └── val/
│   └── labels/
│       ├── train/
│       └── val/
│
└── docs/                     # 文档
    └── report/               # 实践报告
```

---

## 分工建议

| 角色 | 负责内容 | 对应目录 |
|------|---------|---------|
| 成员A | 模型训练、微调、数据集准备 | `models/`, `dataset/` |
| 成员B | 核心算法、数据库、后端逻辑 | `core/`, `data/` |
| 成员C | Gradio 界面、可视化、报告撰写 | `app.py`, `docs/` |

---

## 依赖清单 (requirements.txt)

```
ultralytics>=8.0
gradio>=4.0
torch>=2.0
torchvision
opencv-python
matplotlib
plotly
pandas
numpy
Pillow
```

---

## 风险与应对

| 风险 | 应对措施 |
|------|---------|
| 柑橘数据集不足 | 使用数据增强 + 公开数据集组合 + 优先保证核心功能可用 |
| 模型精度不够 | 适当增加训练轮次，调整 anchor，使用更大模型（YOLOv8s） |
| 视频处理太慢 | 降低采样帧率，使用 YOLOv8n（最快版本） |
| 历史数据缺乏 | 提供导入模板和示例数据，支持无历史数据模式 |
