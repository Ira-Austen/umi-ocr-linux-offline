#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 Umi-OCR Linux 独立便携运行环境配置 Qt/PySide2 路径及系统兼容性补丁
"""

import os
import sys
import glob
import shutil
import urllib.request
import subprocess

# 严格使用与统信 UOS / Debian 10 (GLIBC 2.28) 匹配的底层 X11 图形库 (GLIBC <= 2.17)
# 避免直接复制 Ubuntu 22.04 高版本 glibc (2.33+) 的 libxkbcommon/libxcb 导致 dlopen 失败
DEBIAN10_XCB_PKGS = [
    "http://archive.debian.org/debian/pool/main/x/xcb-util-wm/libxcb-icccm4_0.4.1-1.1_amd64.deb",
    "http://archive.debian.org/debian/pool/main/x/xcb-util-image/libxcb-image0_0.4.0-1+b2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/x/xcb-util-keysyms/libxcb-keysyms1_0.4.0-1+b2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/x/xcb-util-renderutil/libxcb-render-util0_0.3.9-1+b1_amd64.deb",
    "http://archive.debian.org/debian/pool/main/x/xcb-util/libxcb-util1_0.4.0-1+b1_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-xinerama0_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-randr0_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-render0_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-shape0_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-shm0_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-sync1_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-xfixes0_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb-xkb1_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxcb/libxcb1_1.13.1-2_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxkbcommon/libxkbcommon-x11-0_0.8.2-1_amd64.deb",
    "http://archive.debian.org/debian/pool/main/libx/libxkbcommon/libxkbcommon0_0.8.2-1_amd64.deb",
]

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

    # 4. 下载并解压 Debian 10 Buster 核心 XCB / XKB 库 (GLIBC <= 2.17 兼容)
    pyside_qt_lib = os.path.join(embed_dir, "lib/python3.10/site-packages/PySide2/Qt/lib")
    embed_lib = os.path.join(embed_dir, "lib")
    os.makedirs(embed_lib, exist_ok=True)
    target_dirs = [embed_lib]
    if os.path.exists(pyside_qt_lib):
        target_dirs.append(pyside_qt_lib)

    temp_extract = os.path.join(umi_dir, ".tmp_deb_extract")
    os.makedirs(temp_extract, exist_ok=True)
    bundled_count = 0

    print(" -> 正在下载并注入 Debian 10 兼容版 X11/XCB 图形库 (GLIBC <= 2.17)...")
    for deb_url in DEBIAN10_XCB_PKGS:
        deb_name = deb_url.split("/")[-1]
        deb_file = os.path.join(temp_extract, deb_name)
        try:
            req = urllib.request.Request(deb_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp, open(deb_file, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            # 使用 dpkg-deb 解包
            subprocess.run(["dpkg-deb", "-x", deb_file, temp_extract], check=True)
        except Exception as e:
            print(f"    [WARN] 下载或解包 {deb_name} 失败: {e}")

    # 将解压出来的 .so 库复制到目标库目录
    src_lib_dir = os.path.join(temp_extract, "usr/lib/x86_64-linux-gnu")
    if os.path.exists(src_lib_dir):
        for entry in os.listdir(src_lib_dir):
            src_path = os.path.join(src_lib_dir, entry)
            for tdir in target_dirs:
                dst_path = os.path.join(tdir, entry)
                if not os.path.exists(dst_path):
                    try:
                        if os.path.islink(src_path):
                            linkto = os.readlink(src_path)
                            os.symlink(linkto, dst_path)
                        else:
                            shutil.copy2(src_path, dst_path)
                        bundled_count += 1
                    except Exception:
                        pass

    # 清理临时解包目录
    shutil.rmtree(temp_extract, ignore_errors=True)
    print(f" -> 已成功注入 {bundled_count} 个 Debian 10 原生兼容 XCB/XKB 核心图形运行库")

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
