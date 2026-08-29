import fitz  # PyMuPDF
import cv2
import numpy as np
import os
import sys

def clean_page_image(cv_img, remove_stamp=True, remove_watermark=True):
    """
    清洗图片中的红色公章与浅色水印
    """
    if remove_stamp:
        # BGR 顺序中 index 2 是 R 通道 (红色像素高亮为白，黑色字体保留为暗)
        r_channel = cv_img[:, :, 2]
        gray = r_channel
        
        # HSV 辅助过滤深色/暗红印章残影
        hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 43, 46])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([156, 43, 46])
        upper_red2 = np.array([180, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 | mask2
        
        gray = gray.copy()
        gray[red_mask > 0] = 255
    else:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    if remove_watermark:
        # 去除浅灰水印：将高亮浅色噪点置为纯白
        _, gray = cv2.threshold(gray, 190, 255, cv2.THRESH_TOZERO_INV)
        gray[gray == 0] = 255
        
        # 对比度归一化，增强正文笔画
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    return gray

def process_pdf(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    print(f"正在处理: {pdf_path} (共 {len(doc)} 页)...")
    for i, page in enumerate(doc):
        # 3.0 缩放倍率 ≈ 216 DPI，兼顾识别清晰度与处理速度
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        if pix.n == 4:  # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:  # RGB
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        cleaned = clean_page_image(img, remove_stamp=True, remove_watermark=True)
        out_path = os.path.join(output_dir, f"{base_name}_page_{i+1:03d}.png")
        cv2.imwrite(out_path, cleaned)
        
    print(f"✅ 处理完成，清洗后图像已保存到: {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python clean_pdf_for_ocr.py <input.pdf> [output_folder]")
    else:
        pdf_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else "./cleaned_pages"
        process_pdf(pdf_file, out_dir)
