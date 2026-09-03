#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Umi-OCR 宿主环境自检脚本：验证 Qt 平台插件 xcb、UI 连接器与核心任务模块能否正常导入
"""

import os
import sys
import site

def test_host():
    # 确保在 UmiOCR-data 目录下
    site.addsitedir("./py_src/imports")
    
    from PySide2.QtCore import QCoreApplication
    from PySide2.QtGui import QGuiApplication
    print("Qt library paths:", QCoreApplication.libraryPaths())
    print("QT_QPA_PLATFORM_PLUGIN_PATH:", os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"))
    
    app = QGuiApplication(sys.argv)
    
    # 导入核心界面连接器与输出模块，验证所有补丁函数存在且无符号缺失
    from py_src.tag_pages.tag_pages_connector import TagPageConnector
    from py_src.tag_pages.BatchOCR import BatchOCR
    from py_src.mission.mission_ocr import MissionOCR
    from py_src.ocr.output.output_pdf_layered import OutputPdfLayered
    from py_src.ocr.output.tools import capture_ocr_trace
    
    print("✅ [Pass] QGuiApplication xcb 插件及全部核心模块导入自检成功！")

if __name__ == "__main__":
    test_host()
