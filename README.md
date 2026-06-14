<div align="center">

# 馃崐 鏌戞浜ч噺棰勬祴绯荤粺

**Citrus Yield Prediction System**

鍩轰簬璁＄畻鏈鸿瑙変笌娣卞害瀛︿範鐨勬櫤鑳芥灉鍥骇閲忛娴嬩笌椋庨櫓棰勮绯荤粺

[![Live Demo](https://img.shields.io/badge/%F0%9F%8E%AF%20Live%20Demo-Click%20Here-orange?style=for-the-badge)](https://shiren23.github.io/citrus-yield-prediction/)
[![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-brightgreen?style=flat-square)](https://pages.github.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)](https://python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-8A2BE2?style=flat-square)](https://docs.ultralytics.com)

</div>

---

## 馃摉 鍦ㄧ嚎鏂囨。

> 鐐瑰嚮涓嬫柟閾炬帴鏌ョ湅娓叉煋鍚庣殑椤甸潰锛?
| 椤甸潰 | 閾炬帴 |
|:---:|:---:|
| 璁捐鏂囨。 | 馃憠 [鏌ョ湅](https://shiren23.github.io/citrus-yield-prediction/) |
| 鍗忎綔鎸囧崡 | 馃憠 [鏌ョ湅](https://shiren23.github.io/citrus-yield-prediction/contributing.html) |

---

## 馃搨 椤圭洰鏂囦欢

| 鏂囦欢/鐩綍 | 璇存槑 |
|------|------|
| [`index.html`](index.html) | 鍙鍖栬璁℃枃妗ｏ紙鍦ㄧ嚎娓叉煋椤甸潰锛?|
| [`contributing.html`](contributing.html) | 鍗忎綔鎸囧崡锛堝湪绾挎覆鏌撻〉闈級 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 鍗忎綔鎸囧崡锛圡arkdown 婧愭枃浠讹級 |
| [`2026-05-14-citrus-yield-prediction-design.md`](2026-05-14-citrus-yield-prediction-design.md) | 瀹屾暣璁捐鏂囨。锛圡arkdown 婧愭枃浠讹級 |
| [`app.py`](app.py) | **Gradio Web 涓诲簲鐢ㄥ叆鍙?*锛堟敮鎸佹ā鍨嬬儹鍒囨崲锛?|
| [`cli.py`](cli.py) | **鍛戒护琛屽伐鍏?*锛堝揩閫熼娴嬶紝鏃犻渶鍚姩Web锛?|
| [`evaluate.py`](evaluate.py) | **绯荤粺鑷瘎娴嬭剼鏈?* |
| [`validate_models.py`](validate_models.py) | **妯″瀷楠岃瘉鑴氭湰** |
| [`requirements.txt`](requirements.txt) | Python 渚濊禆娓呭崟 |
| `core/` | 鏍稿績绠楁硶妯″潡锛堟娴?棰勬祴/棰勮/閰嶇疆锛?|
| `data/` | 鏁版嵁灞傦紙SQLite 鏁版嵁搴撳皝瑁咃級 |
| `models/` | 妯″瀷璁粌鑴氭湰 + 璁粌濂界殑鏉冮噸 |
| `models/citdet_best.pt` | **鎴愮啛鏋滃疄妫€娴嬫ā鍨?*锛圕itDet 寰皟锛宮AP@50=0.745锛?|
| `models/flowers_best.pt` | **鑺辨湹妫€娴嬫ā鍨?*锛圧oboflow 寰皟锛宮AP@50=0.608锛?|
| `dataset/` | 璁粌鏁版嵁闆嗕笌鍑嗗宸ュ叿 |
| `sample_data/` | 绀轰緥鍥剧墖 |
| [`DATASETS.md`](DATASETS.md) | 鏁版嵁闆嗗紩鐢ㄤ笌璇存槑 |

---

## 馃彈锔?绯荤粺姒傝堪

### 椤圭洰鑳屾櫙

闈㈠悜 **閲嶅簡鍦板尯鏌戞绉嶆鍦烘櫙**锛堝鑺傝剱姗欍€佸繝鍘挎煈姗樼瓑锛夛紝绯荤粺鎺ュ彈鏋滄爲鍥剧墖鎴栬棰戣緭鍏ワ紝閫氳繃 YOLOv8 鐩爣妫€娴嬭瘑鍒姳鏈靛拰鏋滃疄锛岀粨鍚堢敓闀块樁娈佃繘琛屼骇閲忛娴嬶紝骞舵彁渚涗綆浜ч闄╅璀︺€?
### 鎶€鏈爤

| 灞傛 | 鎶€鏈?| 璇存槑 |
|------|------|------|
| 鐩爣妫€娴?| **YOLOv8n** (Ultralytics) | 杞婚噺绾э紝閫傚悎瀹炴椂妫€娴?|
| 娣卞害瀛︿範妗嗘灦 | **PyTorch** | YOLOv8 鍘熺敓鏀寔 |
| Web 鐣岄潰 | **Gradio** | 蹇€熸瀯寤?ML 搴旂敤 UI |
| 鏁版嵁搴?| **SQLite** | 杞婚噺宓屽叆寮忥紝鏃犻渶棰濆鏈嶅姟 |
| 鍙鍖?| **Matplotlib / Plotly** | 鍘嗗彶瓒嬪娍鍥捐〃 |
| 瑙嗛澶勭悊 | **OpenCV** | 瑙嗛甯ф彁鍙栦笌閲囨牱妫€娴?|

### 鏍稿績鍔熻兘

1. **馃幆 鐩爣妫€娴嬪紩鎿?* 鈥?妫€娴嬭姳鏈?/ 骞兼灉 / 鎴愮啛鏋滃疄锛堟敮鎸佸浘鐗囧拰瑙嗛锛?2. **馃尡 鐢熼暱闃舵鍒ゆ柇** 鈥?鑺辨湡 鈫?骞兼灉鏈?鈫?鎴愮啛鏈?鑷姩璇嗗埆
3. **馃搱 浜ч噺棰勬祴绠楁硶** 鈥?涓嶅悓闃舵閲囩敤涓嶅悓淇绯绘暟
4. **鈿狅笍 椋庨櫓棰勮** 鈥?涓庡巻鍙插悓鏈熸暟鎹姣旓紝涓夌骇棰勮
5. **馃搳 鍘嗗彶鏁版嵁绠＄悊** 鈥?SQLite 瀛樺偍锛屾敮鎸?CSV 瀵煎叆/瀵煎嚭
6. **馃彙 鏋滃洯绠＄悊** 鈥?鍒涘缓銆佸垹闄ゆ灉鍥紝鍒嗙被绠＄悊妫€娴嬫暟鎹?7. **馃枼锔?鍛戒护琛屽伐鍏?* 鈥?鏃犻渶鍚姩Web鐣岄潰鍗冲彲蹇€熼娴?8. **馃攧 妯″瀷鐑垏鎹?* 鈥?Web 鐣岄潰鏀寔瀹炴椂鍒囨崲妫€娴嬫ā鍨嬶紙鏋滃疄/鑺辨湹锛?
### 涓夊眰鏋舵瀯

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?           Gradio Web UI / CLI          鈹? 鈫?琛ㄧ幇灞?鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹? YOLOv8 鈹?浜ч噺棰勬祴 鈹?椋庨櫓棰勮 鈹?...     鈹? 鈫?涓氬姟灞?鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?     SQLite + CSV + 妯″瀷鏉冮噸            鈹? 鈫?鏁版嵁灞?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?```

---

## 馃殌 蹇€熷紑濮?
### 鐜瑕佹眰

- Python >= 3.9
- PyTorch >= 2.0
- 4GB+ 鍐呭瓨锛圕PU杩愯锛?
### 瀹夎渚濊禆

```bash
pip install -r requirements.txt
```

### 鍚姩Web鐣岄潰

```bash
python app.py
```

鍚姩鍚庤闂?`http://localhost:7860` 鍗冲彲浣跨敤Web鐣岄潰銆?
### 鍛戒护琛屽揩閫熼娴?
```bash
# 鍥剧墖棰勬祴
python cli.py --image sample_data/sample_00.jpg --variety 濂夎妭鑴愭 --trees 5

# 瑙嗛棰勬祴
python cli.py --video sample.mp4 --variety 蹇犲幙鏌戞 --trees 10

# 淇濆瓨缁撴灉涓篔SON
python cli.py --image sample_data/sample_00.jpg --output result.json --save-db

# 鏌ョ湅鎵€鏈夊弬鏁?python cli.py --help
```

### 绯荤粺鑷瘎娴?
```bash
python evaluate.py
```

---

## 馃獰 Windows 閮ㄧ讲鎸囧崡

### 鐜鍑嗗

| 椤圭洰 | 鏈€浣庤姹?| 鎺ㄨ崘閰嶇疆 |
|------|---------|---------|
| 鎿嶄綔绯荤粺 | Windows 10/11 | Windows 11 |
| Python | 3.9+ | 3.11 ~ 3.13 |
| 鍐呭瓨 | 8GB | 16GB |
| GPU | 鍙€夛紙CPU 鍙窇锛?| NVIDIA RTX 4060 鍙婁互涓?|
| 鏄惧瓨 | 鈥?| 8GB+ |
| 纭洏绌洪棿 | 10GB | 20GB+ |

### 姝ラ涓€锛氬畨瑁?Python

1. 璁块棶 [python.org](https://www.python.org/downloads/) 涓嬭浇 Python 3.11+
2. **瀹夎鏃跺姟蹇呭嬀閫?* `"Add Python to PATH"`
3. 鎵撳紑 PowerShell 楠岃瘉瀹夎锛?   ```powershell
   python --version
   # 搴旀樉绀?Python 3.11.x 鎴栨洿楂樼増鏈?   ```

### 姝ラ浜岋細鍏嬮殕椤圭洰

```powershell
# 浣跨敤 Git 鍏嬮殕锛堥渶鍏堝畨瑁?Git锛?git clone https://github.com/shiren23/citrus-yield-prediction.git
cd citrus-yield-prediction

# 鎴栦娇鐢?GitHub Desktop 涓嬭浇 ZIP 鍚庤В鍘?```

### 姝ラ涓夛細瀹夎渚濊禆

```powershell
# 鍒涘缓铏氭嫙鐜锛堟帹鑽愶級
python -m venv venv
venv\Scripts\activate

# 瀹夎鍩虹渚濊禆
pip install -r requirements.txt
```

> **CUDA 鍔犻€燂紙鍙€夛級**锛氬鏋滀綘鏈?NVIDIA 鏄惧崱锛屽缓璁畨瑁?CUDA 鐗?PyTorch 浠ヨ幏寰?10~15 鍊嶉€熷害鎻愬崌锛?> ```powershell
> pip uninstall torch torchvision -y
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
> ```
> 楠岃瘉 CUDA 鏄惁鍙敤锛?> ```powershell
> python -c "import torch; print(torch.cuda.is_available())"
> # 杈撳嚭 True 琛ㄧず GPU 鍙敤
> ```

### 姝ラ鍥涳細涓嬭浇棰勮缁冩ā鍨嬶紙鑷姩锛?
椤圭洰涓凡鍖呭惈鎴戜滑璁粌濂界殑妯″瀷锛?- `models/citdet_best.pt` 鈥?鎴愮啛鏋滃疄妫€娴?- `models/flowers_best.pt` 鈥?鑺辨湹妫€娴?
鑻ョ己澶?`yolov8n.pt`锛堝熀纭€棰勮缁冩ā鍨嬶級锛岄娆¤繍琛屾椂浼氳嚜鍔ㄤ粠 Ultralytics 涓嬭浇銆?
### 姝ラ浜旓細鍚姩绯荤粺

```powershell
# 鏂瑰紡 1锛氬惎鍔?Web 鐣岄潰
python app.py
# 娴忚鍣ㄨ闂?http://localhost:7860

# 鏂瑰紡 2锛氬懡浠よ蹇€熼娴?python cli.py --image sample_data/sample_00.jpg --variety 濂夎妭鑴愭 --trees 5
```

### 姝ラ鍏細妯″瀷鍒囨崲锛圵eb 鐣岄潰锛?
鎵撳紑 `http://localhost:7860` 鍚庯細
1. 杩涘叆 **馃摳 鍥剧墖棰勬祴** 鎴?**馃幀 瑙嗛棰勬祴** Tab
2. 鍦?**馃 妫€娴嬫ā鍨?* 涓嬫媺妗嗕腑閫夋嫨锛?   - `鎴愮啛鏋滃疄妫€娴?(CitDet寰皟)` 鈥?妫€娴嬫爲涓?鍦伴潰鐨勬煈姗樻灉瀹?   - `鑺辨湹妫€娴?(Roboflow寰皟)` 鈥?妫€娴嬬櫧鑹叉煈姗樿姳鏈?   - `閫氱敤棰勮缁?(YOLOv8n)` 鈥?閫氱敤 80 绫荤墿浣撴娴?3. 涓婁紶鍥剧墖锛岀偣鍑?**馃殌 寮€濮嬮娴?*

> 馃挕 鍒囨崲妯″瀷鏃朵細鑷姩閲婃斁鏃фā鍨嬫樉瀛樺苟鍔犺浇鏂版ā鍨嬶紝鏃犻渶閲嶅惎搴旂敤銆?
### 甯歌闂

| 闂 | 瑙ｅ喅鏂规 |
|------|---------|
| `pip install` 鎶ラ敊鏉冮檺涓嶈冻 | 浠ョ鐞嗗憳韬唤杩愯 PowerShell锛屾垨浣跨敤 `--user` 鍙傛暟 |
| `torch.cuda.is_available()` 涓?False | 妫€鏌?NVIDIA 椹卞姩鏄惁瀹夎锛屾垨鏀圭敤 CPU 杩愯锛堝皢 `--device 0` 鏀逛负 `--device cpu`锛?|
| 鍚姩鏃舵彁绀虹鍙?7860 琚崰鐢?| 鍏抽棴鍏朵粬 Gradio 搴旂敤锛屾垨淇敼 `app.py` 涓殑 `server_port` |
| 妯″瀷鍔犺浇缂撴參 | 棣栨鍚姩闇€瑕佽В鍘嬫ā鍨嬶紝绛夊緟 1~2 鍒嗛挓鍗冲彲 |

---

## 馃 绠楁硶璇存槑

### 鐢熼暱闃舵鍒ゆ柇

| 闃舵 | 鍒ゆ柇鏉′欢 |
|------|---------|
| **鑺辨湡** | 鑺辨湹鍗犳瘮 > 60% |
| **骞兼灉鏈?* | 骞兼灉鍗犳瘮 > 50% |
| **鎴愮啛鏈?* | 鎴愮啛鏋滃崰姣?> 50% |

### 浜ч噺棰勬祴鍏紡

| 闃舵 | 鍏紡 |
|------|------|
| 鑺辨湡 | `浜ч噺 = 鑺遍噺 脳 鍧愭灉鐜?脳 骞冲潎鍗曟灉閲峘 |
| 骞兼灉鏈?| `浜ч噺 = 骞兼灉鏁?脳 鎴愭椿鐜?脳 骞冲潎鍗曟灉閲峘 |
| 鎴愮啛鏈?| `浜ч噺 = 鏋滃疄鏁?脳 骞冲潎鍗曟灉閲?脳 (1-钀芥灉鐜?` |

### 椋庨櫓棰勮瑙勫垯

| 绛夌骇 | 鏉′欢 | 鏍囪瘑 |
|------|------|------|
| 涓ラ噸浣庝骇 | 褰撳墠 < 鍘嗗彶鍧囧€?脳 60% | 馃敶 |
| 浣庝骇椋庨櫓 | 褰撳墠 < 鍘嗗彶鍧囧€?脳 80% | 鈿狅笍 |
| 浜ч噺姝ｅ父 | 褰撳墠 鈮?鍘嗗彶鍧囧€?脳 80% | 鉁?|

---

## 馃崑 鏀寔鍝佺

| 鍝佺 | 骞冲潎鍗曟灉閲?| 鍧愭灉鐜?| 骞兼灉鎴愭椿鐜?|
|------|-----------|--------|-----------|
| 濂夎妭鑴愭 | 250g | 8% | 60% |
| 蹇犲幙鏌戞 | 200g | 10% | 65% |
| 涓囧窞绾㈡ | 150g | 12% | 70% |
| 閫氱敤鏌戞 | 200g | 10% | 65% |

---

## 馃幆 宸茶缁冩ā鍨?
鏈」鐩熀浜庡叕寮€鏁版嵁闆嗚缁冧簡涓や釜涓撶敤妫€娴嬫ā鍨嬶紝鍧囧彲鍦?Web 鐣岄潰涓疄鏃跺垏鎹細

### 妯″瀷涓€锛氭垚鐔熸灉瀹炴娴嬶紙CitDet 寰皟锛?
| 鎸囨爣 | 鏁板€?|
|------|------|
| 鏁版嵁闆?| CitDet锛?79 寮犺缁?楠岃瘉鍥撅級 |
| 璁粌璁惧 | NVIDIA RTX 4060 Laptop GPU |
| mAP@50 | **0.745** |
| mAP@50-95 | 0.368 |
| 绮剧‘鐜?(P) | 0.801 |
| 鍙洖鐜?(R) | 0.676 |
| 璁粌鑰楁椂 | ~6 鍒嗛挓锛?0 epochs锛?|
| 鏉冮噸鏂囦欢 | `models/citdet_best.pt` |

### 妯″瀷浜岋細鑺辨湹妫€娴嬶紙Roboflow 寰皟锛?
| 鎸囨爣 | 鏁板€?|
|------|------|
| 鏁版嵁闆?| orange flowers锛圧oboflow Universe, 226 寮犲浘锛?|
| 璁粌璁惧 | NVIDIA RTX 4060 Laptop GPU |
| mAP@50 | **0.608** |
| mAP@50-95 | 0.288 |
| 绮剧‘鐜?(P) | 0.553 |
| 鍙洖鐜?(R) | 0.660 |
| 璁粌鑰楁椂 | ~2.5 鍒嗛挓锛?0 epochs锛?|
| 鏉冮噸鏂囦欢 | `models/flowers_best.pt` |

### 璁粌鑷繁鐨勬ā鍨?
```bash
# 鎴愮啛鏋滃疄锛圕itDet锛?python dataset/convert_citdet.py
python models/train.py --data dataset_citdet/citdet.yaml --epochs 50 --batch 8 --device 0

# 鑺辨湹锛堥渶鍏堜粠 Roboflow 涓嬭浇鏁版嵁闆嗭級
python models/train.py --data "opensource_dataset/orange flowers.v2i.yolov8/data.yaml" --epochs 50 --batch 8 --device 0
```

---

## 馃帗 鏁版嵁闆嗗紩鐢?
鏈」鐩ā鍨嬭缁冨紩鐢ㄤ簡浠ヤ笅鍏紑鏁版嵁闆嗭細

### CitDet
> **CitDet: A Benchmark Dataset for Citrus Fruit Detection**  
> Jordan A. James, et al. IEEE Robotics and Automation Letters (RA-L), 2024.  
> [GitHub](https://github.com/robotic-vision-lab/CitDet-A-Benchmark-Dataset-For-Citrus-Fruit-Detection) | [arXiv](https://arxiv.org/abs/2309.05645) | [瀹樼綉](https://robotic-vision-lab.github.io/citdet)

### Orange Flowers (Roboflow Universe)
> **orange flowers Computer Vision Model**  
> by am. Roboflow Universe, CC BY 4.0.  
> [涓嬭浇椤甸潰](https://universe.roboflow.com/am-dczhc/orange-flowers-wdjqc/dataset/2)

璇﹁ [`DATASETS.md`](DATASETS.md) 鑾峰彇瀹屾暣寮曠敤鏍煎紡銆?
---

## 馃懃 鍒嗗伐寤鸿

| 瑙掕壊 | 璐熻矗鍐呭 | 瀵瑰簲鐩綍 |
|------|---------|---------|
| 鎴愬憳 A | 妯″瀷璁粌銆佸井璋冦€佹暟鎹泦鍑嗗 | `models/`, `dataset/` |
| 鎴愬憳 B | 鏍稿績绠楁硶銆佹暟鎹簱銆佸悗绔€昏緫 | `core/`, `data/` |
| 鎴愬憳 C | Gradio 鐣岄潰銆佸彲瑙嗗寲銆佹姤鍛婃挵鍐?| `app.py`, `docs/` |

---

## 馃搫 License

MIT License

---

<div align="center">

**[璁捐鏂囨。](https://shiren23.github.io/citrus-yield-prediction/)** 路 **[鍗忎綔鎸囧崡](https://shiren23.github.io/citrus-yield-prediction/contributing.html)**

</div>
