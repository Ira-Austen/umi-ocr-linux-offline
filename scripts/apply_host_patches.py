#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精准应用 umi-paddle-neoengine 的宿主增强补丁到 Umi-OCR 目录
注意：仅覆盖宿主 py_src 与 qt_res 模块，切勿覆盖 plugins/win_x64_PaddleOCR_Py/（插件源码本身已是最新版）
"""

import os
import sys
import shutil

PATCH_MAP = {
    # 宿主 py_src 核心模块
    "mission.py": "py_src/mission/mission.py",
    "mission_doc.py": "py_src/mission/mission_doc.py",
    "mission_ocr.py": "py_src/mission/mission_ocr.py",
    "BatchDOC.py": "py_src/tag_pages/BatchDOC.py",
    "BatchOCR.py": "py_src/tag_pages/BatchOCR.py",
    "line_preprocessing.py": "py_src/ocr/tbpu/parser_tools/line_preprocessing.py",
    "output_init.py": "py_src/ocr/output/__init__.py",
    "output_table_csv.py": "py_src/ocr/output/output_table_csv.py",
    "output_tools.py": "py_src/ocr/output/tools.py",
    "output_pdf_layered.py": "py_src/ocr/output/output_pdf_layered.py",
    "output_pdf_one_layer.py": "py_src/ocr/output/output_pdf_one_layer.py",
    "tbpu_init.py": "py_src/ocr/tbpu/__init__.py",
    "parser_table_grid.py": "py_src/ocr/tbpu/parser_table_grid.py",
    "table_grid.py": "py_src/ocr/tbpu/parser_tools/table_grid.py",
    # QML 界面组件
    "UtilsConfigDicts.qml": "qt_res/qml/Configs/UtilsConfigDicts.qml",
    "ConfigItemComp.qml": "qt_res/qml/Configs/ConfigItemComp.qml",
    "Configs.qml": "qt_res/qml/Configs/Configs.qml",
    "BatchDOCConfigs.qml": "qt_res/qml/TabPages/BatchDOC/BatchDOCConfigs.qml",
    "BatchOCRConfigs.qml": "qt_res/qml/TabPages/BatchOCR/BatchOCRConfigs.qml",
    "ResultsTableView.qml": "qt_res/qml/Widgets/ResultLayout/ResultsTableView.qml",
}

def apply_patches(patch_dir, umi_data_dir):
    patch_dir = os.path.abspath(patch_dir)
    umi_data_dir = os.path.abspath(umi_data_dir)
    print(f"[apply_host_patches] 补丁源目录: {patch_dir}")
    print(f"[apply_host_patches] 目标 UmiOCR-data 目录: {umi_data_dir}")

    applied_count = 0
    for src_name, rel_dst in PATCH_MAP.items():
        src_file = os.path.join(patch_dir, src_name)
        dst_file = os.path.join(umi_data_dir, rel_dst)
        if not os.path.exists(src_file):
            print(f"  [WARN] 补丁源文件缺失: {src_name}")
            continue
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        shutil.copy2(src_file, dst_file)
        applied_count += 1
        print(f"  -> 已覆盖: {src_name} => {rel_dst}")

    print(f"[apply_host_patches] 成功覆盖 {applied_count}/{len(PATCH_MAP)} 个宿主补丁文件。")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python apply_host_patches.py <patch_dir> <umi_data_dir>")
        sys.exit(1)
    apply_patches(sys.argv[1], sys.argv[2])
