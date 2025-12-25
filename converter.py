#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
繁体中文 / 英文 → 简体中文 转换工具

特性：
1. 全文：繁体 → 简体（OpenCC）
2. XML 特例：仅翻译 >English</string> 中的英文
3. googletrans 缺失时自动降级，不报错
"""

import sys
import re
from pathlib import Path
from opencc import OpenCC

# ---------- OpenCC ----------
cc = OpenCC("t2s")

# ---------- Google Translate（可选） ----------
try:
    from googletrans import Translator
    translator = Translator()
    HAS_TRANSLATOR = True
except Exception:
    translator = None
    HAS_TRANSLATOR = False
    print("提示：未安装 googletrans，英文翻译功能已自动禁用")

# ---------- PDF 支持（可选） ----------
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# ---------- 工具函数 ----------

def is_english(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9 .,_\-]+", text.strip()))

def translate_en_to_zh(text: str) -> str:
    if not HAS_TRANSLATOR:
        return text
    try:
        return translator.translate(text, src="en", dest="zh-cn").text
    except Exception:
        return text

def convert_basic(text: str) -> str:
    return cc.convert(text)

def convert_xml_special(content: str) -> str:
    def repl(match):
        inner = match.group(1)
        if is_english(inner):
            zh = translate_en_to_zh(inner)
            return f">{cc.convert(zh)}</string>"
        return match.group(0)

    return re.sub(r">([^<>]+)</string>", repl, content)

# ---------- 文件处理 ----------

def convert_text_file(input_path: Path, output_path: Path):
    content = input_path.read_text(encoding="utf-8")

    if input_path.suffix.lower() == ".xml":
        content = convert_xml_special(content)

    content = convert_basic(content)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Success: {input_path} → {output_path}")

def convert_pdf(input_path: Path, output_path: Path):
    if not PDF_SUPPORT:
        print(f"Skip PDF（未安装 pdfplumber）: {input_path}")
        return

    text = ""
    with pdfplumber.open(input_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(convert_basic(text), encoding="utf-8")
    print(f"Success PDF → TXT: {input_path} → {output_path}")

# ---------- 主流程 ----------

def process_single(input_path: Path, output_arg: str):
    if "." in Path(output_arg).name:
        output_path = Path(output_arg)
    else:
        output_dir = Path(output_arg)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_simplified.txt"

    if input_path.suffix.lower() in {".txt", ".xml", ".json", ".html", ".md"}:
        convert_text_file(input_path, output_path)
    elif input_path.suffix.lower() == ".pdf":
        convert_pdf(input_path, output_path.with_suffix(".txt"))
    else:
        print(f"Skip 不支持的文件类型: {input_path}")

def batch_process(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    for f in input_dir.rglob("*"):
        if f.is_file():
            process_single(f, str(output_dir))

def main():
    if len(sys.argv) < 2:
        print("用法: python converter.py input [output]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_arg = sys.argv[2] if len(sys.argv) > 2 else "output"

    if input_path.is_file():
        process_single(input_path, output_arg)
    else:
        batch_process(input_path, Path(output_arg))

if __name__ == "__main__":
    main()
