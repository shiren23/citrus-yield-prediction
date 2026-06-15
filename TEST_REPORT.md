# 柑橘产量预测系统 - 测试报告

**测试时间**: 2026-06-15 12:21:41

## 一、单元测试

| 模块 | 测试项 | 结果 | 详情 |
|------|--------|------|------|
| Config | 品种配置读取 | ✅ PASS | avg_weight=0.25kg |
| Config | 默认品种回退 | ✅ PASS | fallback=通用柑橘 |
| Config | 品种列表 | ✅ PASS | 4个品种 |
| Config | 阈值配置检查 | ✅ PASS | severe=0.6, warning=0.8 |
| Stage | 花期判断 | ✅ PASS | stage=flowering, conf=0.842 |
| Stage | 幼果期判断 | ✅ PASS | stage=immature, conf=0.778 |
| Stage | 成熟期判断 | ✅ PASS | stage=mature, conf=0.800 |
| Stage | 空数据处理 | ✅ PASS | stage=unknown |
| Stage | 混合期判断 | ✅ PASS | stage=mixed |
| Stage | 边界-花期临界值 | ✅ PASS | 61% flower -> flowering |
| Stage | 边界-略低于花期阈值 | ✅ PASS | 59% flower -> mixed |
| Yield | 花期产量预测 | ✅ PASS | 预测=10.0kg, 期望=10.0kg |
| Yield | 幼果期产量预测 | ✅ PASS | 预测=15.0kg, 期望=15.0kg |
| Yield | 成熟期产量预测 | ✅ PASS | 预测=23.75kg, 期望=23.75kg |
| Yield | 多棵树产量扩展 | ✅ PASS | 10棵总产量=237.5kg |
| Yield | 市斤换算正确 | ✅ PASS | 237.5kg -> 475.0斤 |
| Yield | 混合期加权预测 | ✅ PASS | 预测=13.58kg, conf=0.65 |
| Yield | 零数据预测 | ✅ PASS | 预测=0.0kg |
| Yield | 品种切换(忠县柑橘) | ✅ PASS | 预测=10.0kg, 期望=10.0kg |
| Risk | 正常产量预警 | ✅ PASS | ratio=1.00 |
| Risk | 低产风险预警 | ✅ PASS | ratio=0.75 |
| Risk | 严重低产预警 | ✅ PASS | ratio=0.50 |
| Risk | 历史记录对比 | ✅ PASS | 历史均值=825.0 |
| Risk | 零数据触发严重预警 | ✅ PASS | level=severe, ratio=0.0 |
| Risk | 品种回退后正常预警 | ✅ PASS | fallback品种 -> normal |
| DB | 添加果园 | ✅ PASS | id=1 |
| DB | 查询果园 | ✅ PASS | name=测试果园 |
| DB | 添加检测记录 | ✅ PASS | id=1 |
| DB | 查询检测记录 | ✅ PASS | count=1 |
| DB | 历史数量查询 | ✅ PASS | flower=100 |
| DB | 添加历史产量 | ✅ PASS | id=1 |
| DB | 查询历史产量 | ✅ PASS | count=1 |
| DB | 产量趋势 | ✅ PASS | count=1 |
| DB | 更新果园信息 | ✅ PASS | tree_count=10 |
| DB | CSV导出 | ✅ PASS | length=212 |
| DB | 删除果园 | ✅ PASS | after_delete=None |
| DB | 清理测试数据 | ✅ PASS | 文件已删除 |
| Detector | 模型加载 | ✅ PASS | YOLOv8n loaded successfully |
| Detector | 图片检测 | ✅ PASS | counts={'flower': 3, 'fruit': 0, 'immature_fruit': 0, 'mature_fruit': 0, 'total': 3}, total=3 |
| Detector | 样本图片检测 | ✅ PASS | counts={'flower': 1, 'fruit': 0, 'immature_fruit': 0, 'mature_fruit': 0, 'total': 1} |
| Detector | 视频检测 | ✅ PASS | sampled=3, avg_counts={'flower': 4.0, 'fruit': 0.0, 'immature_fruit': 0.0, 'mature_fruit': 0.0, 'total': 4.0} |
| Integration | 端到端预测流程 | ✅ PASS | stage=flowering, yield=12.0kg, risk=warning |
| Integration | 阶段分类性能(1000次) | ✅ PASS | 耗时=2.5ms |
| Integration | 产量估算性能(1000次) | ✅ PASS | 耗时=1.4ms |
| App UI | 模块导入 | ✅ PASS | app.py 无语法错误 |
| App UI | UI创建 | ✅ PASS | Gradio Blocks 创建成功 |
| CLI | 模块导入 | ✅ PASS | cli.py 无语法错误 |
| CLI | predict_image函数 | ✅ PASS | trees=3 |

## 二、测试统计

- **总测试数**: 48
- **通过**: 48 ✅
- **失败**: 0 ❌
- **通过率**: 100.0%

## 三、性能指标

| 指标 | 结果 |
|------|------|
| 阶段分类(1000次) | 2.52 ms |
| 产量估算(1000次) | 1.44 ms |
| 端到端预测 | < 100 ms (不含模型推理) |

## 四、各模块覆盖率

| 模块 | 测试数 | 通过 | 失败 | 通过率 |
|------|--------|------|------|--------|
| App UI | 2 | 2 | 0 | 100% |
| CLI | 2 | 2 | 0 | 100% |
| Config | 4 | 4 | 0 | 100% |
| DB | 12 | 12 | 0 | 100% |
| Detector | 4 | 4 | 0 | 100% |
| Integration | 3 | 3 | 0 | 100% |
| Risk | 6 | 6 | 0 | 100% |
| Stage | 7 | 7 | 0 | 100% |
| Yield | 8 | 8 | 0 | 100% |

## 五、结论

✅ **全部测试通过**，系统功能完整，各模块运行正常。