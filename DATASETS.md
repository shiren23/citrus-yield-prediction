# 数据集引用与说明

本项目在模型训练与测试过程中使用了以下公开数据集。

---

## CitDet：柑橘果实检测基准数据集

> **CitDet: A Benchmark Dataset for Citrus Fruit Detection**

本项目引用了 **CitDet** 数据集用于柑橘果实目标检测模型的训练与验证。

### 数据集简介

CitDet 是由美国德州大学阿灵顿分校 Robotic Vision Lab 发布的柑橘果实检测基准数据集，专为果园环境中受黄龙病（HLB）影响的柑橘树设计。该数据集包含高分辨率图像及高质量的边界框标注，对推动柑橘果实检测、产量估算及自动化采摘研究具有重要价值。

| 项目 | 详情 |
|------|------|
| **发布机构** | Robotic Vision Lab, University of Texas at Arlington |
| **论文期刊** | IEEE Robotics and Automation Letters (RA-L), 2024 |
| **图像数量** | 579 张高分辨率果园图像 |
| **标注数量** | 32,000+ 个边界框 |
| **标注类别** | 树上果 (orange_T)、地上果 (orange_G) |
| **标注格式** | COCO JSON |
| **应用场景** | 果实检测、产量估算、果实掉落分析、HLB 影响评估 |

### 官方链接

- **GitHub 仓库**：https://github.com/robotic-vision-lab/CitDet-A-Benchmark-Dataset-For-Citrus-Fruit-Detection
- **数据集官网**：https://robotic-vision-lab.github.io/citdet
- **论文 arXiv**：https://arxiv.org/abs/2309.05645
- **数据下载**：https://dataverse.tdl.org/dataset.xhtml?persistentId=doi:10.18738/T8/UAJLWG

### 引用格式（BibTeX）

```bibtex
@article{james2024citdet,
  title={CitDet: A Benchmark Dataset for Citrus Fruit Detection},
  author={James, Jordan A and Manching, Heather K and Mattia, Matthew R 
          and Bowman, Kim D and Hulse-Kemp, Amanda M and Beksi, William J},
  journal={IEEE Robotics and Automation Letters (RA-L)},
  volume={9},
  number={12},
  pages={10788--10795},
  year={2024}
}

@data{mavmatrix/dataset.2024.05.005,
  title={{CitDet}},
  author={James, Jordan A and Manching, Heather K and Mattia, Matthew R 
          and Bowman, Kim D and Hulse-Kemp, Amanda M and Beksi, William J},
  publisher={MavMatrix},
  version={V1},
  url={https://doi.org/10.32855/dataset.2024.05.005},
  doi={10.32855/dataset.2024.05.005},
  year={2024}
}
```

### 在本项目中的使用方式

1. 下载 CitDet 数据集（COCO JSON 格式）
2. 将 COCO 格式转换为 YOLO 格式（可使用 `dataset/convert_coco_to_yolo.py`）
3. 将转换后的图片和标注放入 `dataset/images/` 和 `dataset/labels/` 目录
4. 运行训练脚本：
   ```bash
   python models/train.py --data dataset/citrus.yaml --epochs 100
   ```

---

## 其他参考数据集

| 数据集 | 链接 | 说明 |
|--------|------|------|
| dataset_fruits_detection | https://github.com/lightly-ai/dataset_fruits_detection | YOLOv8 格式通用水果检测数据集，含 Orange 类别 |
| Fruit detection for YOLOv8 | https://www.kaggle.com/datasets/cubeai/fruit-detection-for-yolov8 | Kaggle 水果检测数据集 |

---

> **声明**：本项目仅将上述数据集用于学术研究及模型训练验证，数据集的版权归原作者及发布机构所有。
