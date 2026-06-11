# 协作指南

本文档说明如何参与柑橘产量预测系统的开发、提交文件和做记录。

---

## 1. 前置准备

```bash
# 克隆仓库到本地
git clone https://github.com/shiren23/citrus-yield-prediction.git
cd citrus-yield-prediction
```

如果已克隆过，每次开始工作前先同步最新代码：

```bash
git pull
```

---

## 2. 分支规范

不要直接在 `main` 分支上开发，请按功能创建分支：

| 分支命名 | 示例 | 说明 |
|----------|------|------|
| `feat/功能名` | `feat/yolov8-detection` | 新功能开发 |
| `fix/修复内容` | `fix/detection-bug` | 修复问题 |
| `docs/文档内容` | `docs/training-log` | 文档更新 |
| `exp/实验名` | `exp/yolov8s-comparison` | 实验性尝试 |

操作流程：

```bash
# 创建并切换到新分支
git checkout -b feat/yolov8-detection

# 开发完成后，推送分支到远程
git push -u origin feat/yolov8-detection
```

---

## 3. 提交文件流程

### 3.1 日常工作流

```bash
# ① 先拉取最新代码
git pull

# ② 切换到你的功能分支（没有就新建）
git checkout -b feat/你的功能名

# ③ 添加你要提交的文件（推荐逐个添加，避免误提交）
git add models/train.py core/detector.py

# ④ 提交，写清楚做了什么
git commit -m "feat: 完成YOLOv8检测引擎封装"

# ⑤ 推送到远程
git push -u origin feat/你的功能名
```

### 3.2 提交信息格式

```
类型: 简短描述
```

常用类型：

| 类型 | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 实现花朵检测功能` |
| `fix` | 修复 | `fix: 修复视频帧采样丢帧问题` |
| `docs` | 文档 | `docs: 添加模型训练说明` |
| `test` | 测试 | `test: 添加检测引擎单元测试` |
| `chore` | 杂项 | `chore: 更新依赖版本` |

### 3.3 合并到主分支

功能开发完成并测试通过后，在 GitHub 页面上创建 **Pull Request**：

1. 打开仓库页面 https://github.com/shiren23/citrus-yield-prediction
2. 点击 **Pull requests → New pull request**
3. 选择你的分支 → `main`
4. 填写 PR 标题和描述（说明改了什么、为什么改）
5. 通知团队成员 Review
6. Review 通过后点击 **Merge pull request**

---

## 4. 各成员负责目录

请优先在自己负责的目录下工作：

| 成员 | 主要目录 | 主要文件 |
|------|---------|---------|
| 成员 A — 模型 | `models/`, `dataset/` | `train.py`, `predict.py`, 训练数据 |
| 成员 B — 算法 | `core/`, `data/` | `detector.py`, `yield_estimator.py`, `database.py` |
| 成员 C — 界面 | 根目录, `docs/` | `app.py`, 文档, 报告 |

如需修改他人目录下的文件，请先沟通再操作。

---

## 5. 记录规范

### 5.1 开发日志

在 `docs/` 目录下按日期记录开发进展，文件命名格式：

```
docs/
├── dev-log-2026-05-14.md      # 开发日志
├── dev-log-2026-05-15.md
└── ...
```

模板：

```markdown
# 开发日志 2026-05-14

## 今日完成
- 完成XXX功能的开发
- 修复了XXX问题

## 遇到的问题
- 问题描述及解决方案

## 明日计划
- 待办事项
```

### 5.2 模型训练记录

每次训练请在 `docs/training-logs/` 下记录：

```
docs/training-logs/
├── train-001-yolov8n-50ep.md
└── ...
```

至少包含以下信息：

```markdown
# 训练记录 #001

- 日期：2026-05-14
- 模型：YOLOv8n
- 数据集：xxx张图片（train/val 划分）
- 训练参数：50 epochs, batch=16, imgsz=640
- 结果：mAP@0.5 = 0.xx
- 备注：xxx
```

---

## 6. 注意事项

- **提交前先 `git pull`**，避免冲突
- **不要提交大文件**（模型权重 > 100MB 用 Git LFS 或网盘分享）
- **不要提交敏感信息**（密钥、密码、私有数据）
- **不要直接 push 到 `main`**，走 PR 流程
- 有问题在 GitHub Issues 或群里沟通
