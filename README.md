# Umi-OCR Linux (统信 UOS / 信创 x86_64) 全功能离线包构建与自动化测试

本项目提供基于 **GitHub Actions** 的全自动化构建脚本，将 [Umi-OCR](https://github.com/hiroi-sora/Umi-OCR) 官方 Linux 发行版与 [umi-paddle-neoengine](https://github.com/chapterv/umi-paddle-neoengine) 二开新引擎（PP-OCRv6 + ONNX Runtime）深度整合，自动打包全套离线模型与便携式 Python 运行环境，专为**统信 UOS / 信创海光（x86_64）等纯离线环境**设计。

---

## ✨ 核心特性

- 📦 **全自包含离线包**：内置独立便携式 Python 3.11 及全套推理依赖，无需目标机安装 Python 或联网。
- 🚀 **PP-OCRv6 新代际引擎**：相比老旧 v3，大幅提升复杂手写、模糊扫描件与低质文档的识别准确率。
- 🧠 **预置离线模型**：内嵌 PP-OCRv6（Medium + Small）模型及方向纠偏、曲面去扭曲等工具模型。
- 🖥️ **统信 UOS / DDE 完美适配**：内置 `create-desktop-shortcut.sh` 脚本，解压后一键生成桌面与开始菜单图标，支持双击启动。
- 🛡️ **CI 自动化验证**：每次构建自动在虚拟无头环境中完成管道通信与推理测试，确保产物开箱即用。

---

## 🛠️ 构建方法

1. 点击仓库上方的 **Actions** 标签页；
2. 在左侧列表选择 **Build & Test Umi-OCR Linux Offline Package**；
3. 点击右侧 **Run workflow** 按钮启动构建；
4. 构建完成后（约 3~5 分钟），在当前 Run 详情页底部的 **Artifacts** 区域下载 `Umi-OCR-Linux-Offline-PPOCRv6.tar.gz`。

---

## 💻 统信 UOS / 紫光电脑部署指南

### 1. 解压与启动
```bash
# 解压到用户目录
tar -xzvf Umi-OCR-Linux-Offline-PPOCRv6.tar.gz
cd Umi-OCR

# 启动图形界面
./umi-ocr.sh
```

### 2. 创建桌面双击快捷方式
在 `Umi-OCR` 目录下运行：
```bash
./create-desktop-shortcut.sh
```
统信桌面与开始菜单中即会出现 **Umi-OCR 文字识别** 图标，之后直接双击图标即可启动。

### 3. 配置新引擎
首次打开软件后：
1. 进入 **【全局设置】→【文字识别】**；
2. 识别接口选择 **`PaddleOCR（新引擎 / Python）`**；
3. 推理引擎选择 **`ONNX Runtime CPU`**（默认推荐）；
4. 点击 **【应用修改】** 即可。

---

## 📄 公章与水印清洗辅助工具

仓库内附带 `scripts/clean_pdf_for_ocr.py`，用于在 OCR 前批量去除 PDF 中的红色公章与浅灰水印：

```bash
python3 scripts/clean_pdf_for_ocr.py <待识别文档.pdf> [输出图片目录]
```
清洗后的图片直接拖入 Umi-OCR 进行批量识别，可显著提升识别率。
