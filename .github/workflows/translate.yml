#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
繁体中文转简体中文转换工具
支持 .txt 和 .pdf 文件的单个/批量转换。
用法: python converter.py [input_file_or_dir] [output_file_or_dir]
- 如果输入/输出都是文件：转换单个文件。
- 如果输入/输出有目录：批量转换到输出目录。
"""

from opencc import OpenCC
import sys
import os
import argparse
from pathlib import Path

# 可选：PDF 处理
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("警告：未安装 pdfplumber，无法处理 PDF 文件。运行 'pip install pdfplumber' 安装。")

def convert_text(content):
    """转换文本为简体中文"""
    converter = OpenCC('t2s')  # t2s: 繁体转简体
    return converter.convert(content)

def convert_txt_file(input_path, output_path):
    """转换 .txt 文件"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        converted = convert_text(content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted)
        print(f"✓ TXT 转换完成: {input_path} → {output_path}")
    except Exception as e:
        print(f"✗ TXT 转换失败 {input_path}: {e}")

def convert_pdf_file(input_path, output_path):
    """转换 .pdf 文件（提取文本后转换）"""
    if not PDF_SUPPORT:
        print(f"✗ PDF 支持未启用: {input_path}")
        return
    try:
        with pdfplumber.open(input_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        converted = convert_text(full_text)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted)  # 输出为 .txt
        print(f"✓ PDF 转换完成: {input_path} → {output_path}")
    except Exception as e:
        print(f"✗ PDF 转换失败 {input_path}: {e}")

def process_file(input_path, output_base):
    """处理单个文件，output_base 可以是文件或目录路径"""
    input_path = Path(input_path)
    if input_path.suffix.lower() not in {".txt", ".pdf"}:
        print(f"✗ 不支持的文件类型: {input_path}")
        return

    if Path(output_base).suffix:  # 如果 output_base 有扩展名，视为单个文件输出
        output_path = Path(output_base)
        output_path.parent.mkdir(exist_ok=True)  # 只创建父目录
    else:  # 视为输出目录
        output_dir = Path(output_base)
        output_dir.mkdir(exist_ok=True)
        output_filename = input_path.stem + "_simplified" + input_path.suffix
        if input_path.suffix == ".pdf":
            output_filename = input_path.stem + "_simplified.txt"
        output_path = output_dir / output_filename

    if input_path.suffix.lower() == ".txt":
        convert_txt_file(input_path, output_path)
    elif input_path.suffix.lower() == ".pdf":
        convert_pdf_file(input_path, output_path)
    else:
        print(f"✗ 不支持的文件类型: {input_path}")

def batch_process(input_dir, output_dir):
    """批量处理目录"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    supported_exts = {".txt", ".pdf"}
    files = [f for f in input_dir.rglob("*") if f.is_file() and f.suffix.lower() in supported_exts]
    
    if not files:
        print("未找到支持的文件 (.txt 或 .pdf)")
        return
    
    print(f"发现 {len(files)} 个文件，开始批量转换...")
    for file_path in files:
        process_file(file_path, output_dir)
    print("批量转换完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="繁体转简体中文转换工具")
    parser.add_argument("input", help="输入文件或目录路径")
    parser.add_argument("output", nargs="?", default="output", help="输出文件或目录 (默认: output)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"错误：输入路径不存在 {args.input}")
        sys.exit(1)
    
    if input_path.is_file():
        process_file(input_path, args.output)  # 直接处理单个文件，output 可以是文件或目录
    elif input_path.is_dir():
        batch_process(input_path, args.output)
    else:
        print(f"错误：无效路径 {args.input}")
        sys.exit(1)
