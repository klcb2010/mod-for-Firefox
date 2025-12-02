#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
繁体中文 → 简体中文 转换工具
支持 .txt、.xml、.pdf 等文本类文件的单个或批量转换
用法：
    python converter.py input.txt output.txt
    python converter.py requirements.txt translated.txt
    python converter.py strings.xml values-zh-rCN/strings.xml
    python converter.py input_dir output_dir
"""

from opencc import OpenCC
import sys
from pathlib import Path

# 可选 PDF 支持
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("提示：未安装 pdfplumber，PDF 文件将被跳过（pip install pdfplumber 可启用）")


def convert_text(text: str) -> str:
    """繁体 → 简体"""
    converter = OpenCC('t2s')          # 繁体转简体
    # converter = OpenCC('tw2sp')      # 台湾惯用 → 大陆简体（可选）
    return converter.convert(text)


def convert_txt_or_xml(input_path: Path, output_path: Path):
    """处理普通文本文件（包括 .txt .xml .json 等）"""
    try:
        content = input_path.read_text(encoding="utf-8")
        converted = convert_text(content)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(converted, encoding="utf-8")
        print(f"Success: {input_path} → {output_path}")
    except Exception as e:
        print(f"Failed: {input_path} | 错误: {e}")


def convert_pdf(input_path: Path, output_path: Path):
    """PDF → 提取文字后转简体 → 输出为 .txt"""
    if not PDF_SUPPORT:
        print(f"Skip PDF（未安装 pdfplumber）: {input_path}")
        return
    try:
        full_text = ""
        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        converted = convert_text(full_text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(converted, encoding="utf-8")
        print(f"Success PDF → TXT: {input_path} → {output_path}")
    except Exception as e:
        print(f"Failed PDF: {input_path} | 错误: {e}")


def process_single_file(input_path: Path, output_arg: str):
    """核心逻辑：判断 output_arg 是文件路径还是目录"""
    # 关键修复：只要输出参数的文件名里包含 . 就当作文件处理
    if '.' in Path(output_arg).name:
        # 用户明确指定了输出文件名（如 translated_output.txt）
        output_path = Path(output_arg)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    # 只创建父目录
    else:
        # 用户只给了目录名（如 output、translated_dir）
        output_dir = Path(output_arg)
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = ".txt" if input_path.suffix.lower() != ".pdf" else ".txt"
        output_path = output_dir / (input_path.stem + "_simplified" + suffix)

    # 根据文件类型执行转换
    if input_path.suffix.lower() in {".txt", ".xml", ".json", ".html", ".md"}:
        convert_txt_or_xml(input_path, output_path)
    elif input_path.suffix.lower() == ".pdf":
        convert_pdf(input_path, output_path.with_suffix(".txt"))
    else:
        print(f"Skip 不支持的文件类型: {input_path}")


def batch_process(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    supported = {".txt", ".xml", ".json", ".html", ".md", ".pdf"}

    files = [
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in supported
    ]

    if not files:
        print("Warning: 目录中未找到支持的文件")
    print(f"Success: 发现 {len(files)} 个文件，开始批量转换...")
    for f in files:
        process_single_file(f, str(output_dir))
    print("All Done: 批量转换完成！")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_arg = sys.argv[1]
    output_arg = sys.argv[2] if len(sys.argv) >= 3 else "output"

    input_path = Path(input_arg)

    if not input_path.exists():
        print(f"Error: 输入路径不存在: {input_arg}") ; sys.exit(1)

    if input_path.is_file():
        process_single_file(input_path, output_arg)
    else:
        batch_process(input_path, Path(output_arg))


if __name__ == "__main__":
    main()
