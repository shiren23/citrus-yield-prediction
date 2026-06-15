# 柑橘花朵检测模型优化方案

## 一、当前瓶颈分析

| 项目 | 现状 | 影响 |
|------|------|------|
| 训练数据量 | 仅 `opensource_dataset/orange flowers.v2i.yolov8` 约 226 张（train 198 + valid 20 + test 8） | 数据量过小，模型泛化能力差，容易漏检/误检 |
| 模型规模 | 当前 `flowers_best.pt` 基于 YOLOv8n | 速度快但特征提取能力弱，对密集小花朵不敏感 |
| 输入分辨率 | 默认 640×640 | 花朵目标小，低分辨率会损失细节 |
| 数据增强 | 仅依赖 Ultralytics 默认增强 | 对果园场景（光照变化、遮挡、角度）覆盖不足 |
| 标注质量 | 未经过清洗 | 可能存在框过大、漏标、错标等问题 |

> 注意：`dataset/images/train` 与 `dataset/images/val` 当前为空，只有标注文件。继续训练前需要先补齐图片，或直接使用 `opensource_dataset/orange flowers.v2i.yolov8/` 下的原始数据。

## 二、优化方向（按收益排序）

### 1. 扩充花朵数据集（最重要）

- **同场景实拍补充**：在目标果园不同时间、角度、光照下拍摄花朵照片，标注后加入训练集。
- **开源数据补充**：
  - [Roboflow 搜索 "citrus flower" / "orange flower"](https://universe.roboflow.com/search)
  - 通用花卉数据集可先做预训练，再在本项目数据上微调。
- **推荐数据量**：至少 800~1500 张训练图，验证集不少于 150 张。

### 2. 使用更大的模型

在硬件允许的情况下，将 `yolov8n` 替换为 `yolov8s` 或 `yolov8m`：

| 模型 | 速度 | 精度 | 推荐 GPU 显存 |
|------|------|------|---------------|
| YOLOv8n | 最快 | 较低 | 4GB |
| YOLOv8s | 快 | 中 | 6GB |
| YOLOv8m | 中等 | 较高 | 8GB |
| YOLOv8l | 慢 | 高 | 12GB+ |

CPU 训练建议仍用 YOLOv8n/s；有 NVIDIA 独显可尝试 YOLOv8m。

### 3. 提高输入分辨率

将 `imgsz` 从 640 提升到 **1280**（或至少 960）：

- 花朵在图中通常较小，高分辨率能保留更多细节。
- 代价：训练/推理速度变慢、显存占用增加。

### 4. 数据增强策略

Ultralytics YOLOv8 已内置 Mosaic、MixUp、CopyPaste 等。可在训练时进一步加强：

```python
mosaic=1.0,      # 马赛克增强
mixup=0.2,       # 混合增强（可适当提升）
copy_paste=0.2,  # 复制粘贴增强
hsv_h=0.02,      # 色调抖动
hsv_s=0.7,       # 饱和度抖动
hsv_v=0.4,       # 亮度抖动
degrees=10.0,    # 随机旋转
translate=0.1,   # 平移
scale=0.5,       # 缩放
fliplr=0.5,      # 水平翻转
```

对果园场景，特别推荐：
- **亮度/对比度抖动**：模拟晴天/阴天/逆光。
- **高斯噪声/模糊**：模拟手机拍摄抖动、压缩伪影。
- **随机裁剪与缩放**：模拟不同拍摄距离。

### 5. 基于现有模型继续训练（迁移学习）

不要从头训练，而是从当前 `models/flowers_best.pt` 继续微调：

```python
from ultralytics import YOLO
model = YOLO('models/flowers_best.pt')  # 加载已有权重
model.train(data='.../data.yaml', epochs=50, imgsz=1280, ...)
```

这样能在少量新数据上快速收敛，同时保留已学到的花朵特征。

### 6. 调整置信度与 NMS 阈值

即使模型精度提升，后处理参数也会显著影响使用体验：

- `conf=0.20`：适当降低置信度，减少漏检。
- `iou=0.45`：对密集花朵，避免 NMS 过度抑制。

可在 `core/config.py` 中调整：

```python
CONFIDENCE_THRESHOLDS = {
    "flower": 0.20,
    ...
}
```

### 7. 标注质量检查

使用 Ultralytics 验证模式或可视化脚本检查：

```bash
yolo detect val model=models/flowers_best.pt data=opensource_dataset/orange\ flowers.v2i.yolov8/data.yaml
```

重点检查：
- 是否有大量漏标花朵？
- 边界框是否贴合花朵边缘？
- 是否存在一个框包含多朵花的情况？

## 三、推荐训练流程

### 步骤 1：确认数据

确保 `opensource_dataset/orange flowers.v2i.yolov8/` 下包含：

```
train/images/*.jpg
train/labels/*.txt
valid/images/*.jpg
valid/labels/*.txt
test/images/*.jpg
test/labels/*.txt
data.yaml
```

### 步骤 2：运行花朵专用训练脚本

```bash
python scripts/train_flower.py --epochs 100 --imgsz 1280 --model-size s --device 0
```

参数说明：
- `--device 0`：使用第一块 NVIDIA GPU；CPU 训练用 `--device cpu`。
- `--imgsz 1280`：高分辨率；显存不足可改为 960 或 640。
- `--model-size s`：YOLOv8s；显存小可改 `n`。

脚本会自动：
1. 加载 `models/flowers_best.pt` 作为起点。
2. 在花朵数据集上继续训练。
3. 训练结束后将最佳模型覆盖保存到 `models/flowers_best.pt`（旧模型自动备份到 `models/flowers_best.pt.bak`）。
4. 打印验证指标 mAP@50、mAP@50-95。

### 步骤 3：验证效果

```bash
python validate_models.py
```

或单独验证花朵模型：

```bash
yolo detect val model=models/flowers_best.pt data="opensource_dataset/orange flowers.v2i.yolov8/data.yaml" imgsz=1280
```

### 步骤 4：测试实际推理

在 Web 界面上传几张果园花朵照片，观察：
- 漏检是否减少
- 误检是否减少
- 密集花朵是否都能框出

## 四、如果继续收集数据后的训练

1. 将新图片和 YOLO 格式标注放入 `dataset/flower_data/train/` 与 `dataset/flower_data/valid/`。
2. 创建 `dataset/flower_data/data.yaml`：

```yaml
path: F:\文档\25-26\A果园产量预测\dataset\flower_data
train: train/images
val: valid/images
nc: 1
names: ['flower']
```

3. 用 `scripts/train_flower.py --data dataset/flower_data/data.yaml` 训练。

## 五、预期指标

以当前 226 张图、YOLOv8n 为基准，合理优化后：

| 优化项 | 预期 mAP@50 提升 |
|--------|------------------|
| 数据量 226 → 800+ | +15~25% |
| YOLOv8n → YOLOv8s | +3~5% |
| imgsz 640 → 1280 | +3~8% |
| 数据增强调优 | +2~5% |
| 从 flowers_best.pt 微调 | 收敛更快，小数据提升更明显 |

> 注：花朵检测本身比果实检测更难（目标小、密集、易与叶片混淆），实际 mAP@50 达到 0.70~0.80 已属不错。

## 六、常见问题

**Q：电脑只有 CPU，训练很慢怎么办？**
A：
- 仍可用 CPU 训练，但建议减小 `--imgsz 640`、 `--batch 4`、 `--epochs 50`。
- 优先扩充数据 + 使用 `yolov8n`。
- 若需快速验证，可先用 20~30 个 epoch 做实验。

**Q：训练时显存不足（CUDA out of memory）？**
A：
- 降低 `--imgsz` 到 960 或 640。
- 降低 `--batch` 到 4 或 2。
- 换用更小的模型 `--model-size n`。

**Q：模型精度提升了，但 Web 界面还是漏检？**
A：
- 检查 `core/config.py` 中 `CONFIDENCE_THRESHOLDS["flower"]` 是否过高。
- 检查上传图片分辨率是否过低、花朵是否过小。
- 检查是否使用了旧的 `flowers_best.pt`，确认训练后已替换。
