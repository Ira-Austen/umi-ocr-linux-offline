#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 Umi-OCR Linux 独立便携运行环境配置 Qt/PySide2 路径及系统兼容性补丁
"""

import os
import sys
import glob
import shutil

def patch_all(umi_dir):
    umi_dir = os.path.abspath(umi_dir)
    data_dir = os.path.join(umi_dir, "UmiOCR-data")
    embed_dir = os.path.join(data_dir, ".embeddable")
    
    print(f"[patch_runtime] 正在处理: {umi_dir}")

    # 1. 写入 .embeddable/activate.sh
    activate_sh = os.path.join(embed_dir, "activate.sh")
    activate_content = """#!/bin/bash
EMBED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONHOME="$EMBED_DIR"
export PATH="$EMBED_DIR/bin:$PATH"

PYSIDE_QT="$EMBED_DIR/lib/python3.10/site-packages/PySide2/Qt"
if [ -d "$PYSIDE_QT" ]; then
    export QT_QPA_PLATFORM_PLUGIN_PATH="$PYSIDE_QT/plugins/platforms"
    export QT_PLUGIN_PATH="$PYSIDE_QT/plugins"
    export LD_LIBRARY_PATH="$PYSIDE_QT/lib:$EMBED_DIR/lib:$LD_LIBRARY_PATH"
else
    export LD_LIBRARY_PATH="$EMBED_DIR/lib:$LD_LIBRARY_PATH"
fi
"""
    with open(activate_sh, "w", encoding="utf-8") as f:
        f.write(activate_content)
    os.chmod(activate_sh, 0o755)
    print(" -> activate.sh 已更新")

    # 2. 写入 .embeddable/bin/qt.conf
    bin_dir = os.path.join(embed_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    qt_conf = os.path.join(bin_dir, "qt.conf")
    qt_conf_content = """[Paths]
Prefix = ../lib/python3.10/site-packages/PySide2/Qt
Plugins = plugins
Imports = qml
Qml2Imports = qml
"""
    with open(qt_conf, "w", encoding="utf-8") as f:
        f.write(qt_conf_content)
    print(" -> qt.conf 已写入")

    # 3. 增强 main_linux.py 内部的 Qt 路径自动注册
    main_py = os.path.join(data_dir, "main_linux.py")
    if os.path.exists(main_py):
        with open(main_py, "r", encoding="utf-8") as f:
            code = f.read()
        
        inject_code = """
    # 自动定位 PySide2 Qt 平台插件与运行库
    pyside_dir = os.path.join(cwd, ".embeddable/lib/python3.10/site-packages/PySide2")
    if os.path.exists(pyside_dir):
        qt_dir = os.path.join(pyside_dir, "Qt")
        platforms_dir = os.path.join(qt_dir, "plugins", "platforms")
        plugins_dir = os.path.join(qt_dir, "plugins")
        lib_dir = os.path.join(qt_dir, "lib")
        embed_lib = os.path.join(cwd, ".embeddable/lib")
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_dir
        os.environ["QT_PLUGIN_PATH"] = plugins_dir
        curr_ld = os.environ.get("LD_LIBRARY_PATH", "")
        extra_paths = [lib_dir, embed_lib]
        for p in extra_paths:
            if p not in curr_ld:
                curr_ld = f"{p}:{curr_ld}" if curr_ld else p
        os.environ["LD_LIBRARY_PATH"] = curr_ld
        try:
            from PySide2.QtCore import QCoreApplication
            QCoreApplication.addLibraryPath(plugins_dir)
            QCoreApplication.addLibraryPath(platforms_dir)
        except Exception:
            pass
"""
        if 'os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]' not in code:
            code = code.replace("os.chdir(cwd)", "os.chdir(cwd)" + inject_code)
            with open(main_py, "w", encoding="utf-8") as f:
                f.write(code)
            print(" -> main_linux.py 已注入 Qt 动态定位代码")

    # 4. 将系统 xcb / xkb 核心库打包进 .embeddable/lib 和 PySide2/Qt/lib 实现真正零依赖离线运行
    pyside_qt_lib = os.path.join(embed_dir, "lib/python3.10/site-packages/PySide2/Qt/lib")
    embed_lib = os.path.join(embed_dir, "lib")
    os.makedirs(embed_lib, exist_ok=True)
    if os.path.exists(pyside_qt_lib):
        target_dirs = [embed_lib, pyside_qt_lib]
    else:
        target_dirs = [embed_lib]

    lib_patterns = [
        "/usr/lib/x86_64-linux-gnu/libxcb-*.so*",
        "/usr/lib/x86_64-linux-gnu/libxkbcommon*.so*",
    ]
    bundled_count = 0
    for pat in lib_patterns:
        for f in glob.glob(pat):
            fname = os.path.basename(f)
            for tdir in target_dirs:
                dest = os.path.join(tdir, fname)
                if not os.path.exists(dest):
                    try:
                        if os.path.islink(f):
                            linkto = os.readlink(f)
                            os.symlink(linkto, dest)
                        else:
                            shutil.copy2(f, dest)
                        bundled_count += 1
                    except Exception:
                        pass
    print(f" -> 已自动打包 {bundled_count} 个 XCB/XKB 核心图形运行库进离线包")

    # 5. 增强 umi-ocr.sh
    umi_sh = os.path.join(umi_dir, "umi-ocr.sh")
    umi_sh_content = """#!/bin/bash
cd $(dirname ${BASH_SOURCE[0]})
current_dir=$(pwd)
export UMI_APP_PATH=$(realpath ${BASH_SOURCE[0]})

if [ -f "UmiOCR-data/.embeddable/activate.sh" ]; then
    cd UmiOCR-data/.embeddable
    source activate.sh
    cd $current_dir
    echo "Use the Python embeddable environment."
elif [ -f "UmiOCR-data/.venv/bin/activate" ]; then
    source UmiOCR-data/.venv/bin/activate
    echo "Use the Python virtual environment."
else
    echo "Use the default Python environment."
fi

# 确保 Qt 平台插件路径在启动进程前已全局 export
EMBED_DIR="$current_dir/UmiOCR-data/.embeddable"
if [ -d "$EMBED_DIR/lib/python3.10/site-packages/PySide2/Qt" ]; then
    PYSIDE_QT="$EMBED_DIR/lib/python3.10/site-packages/PySide2/Qt"
    export QT_QPA_PLATFORM_PLUGIN_PATH="$PYSIDE_QT/plugins/platforms"
    export QT_PLUGIN_PATH="$PYSIDE_QT/plugins"
    export LD_LIBRARY_PATH="$PYSIDE_QT/lib:$EMBED_DIR/lib:$LD_LIBRARY_PATH"
fi

echo "pwd: $(pwd)"

if [ "$HEADLESS" == "true" ]; then
  echo "Use headless mode."
  if [ -e /tmp/.X99-lock ]; then
    rm -f /tmp/.X99-lock
  fi
  Xvfb :99 -screen 0 1024x768x16 & export DISPLAY=:99
else
  echo "Use GUI mode."
  if [ -z "$DISPLAY" ]; then
    echo "Error: \\$DISPLAY is not set."
    exit 1
  fi
fi

python3 UmiOCR-data/main_linux.py "$@"
"""
    with open(umi_sh, "w", encoding="utf-8") as f:
        f.write(umi_sh_content)
    os.chmod(umi_sh, 0o755)
    print(" -> umi-ocr.sh 已升级")
    print("[patch_runtime] 全部补丁处理完成！")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch_all(target)
