#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版文本转换工具（支持自动英文 → 简体中文）

功能：
1. 繁体中文 → 简体中文
2. 英文 → 简体中文（自动机器翻译，仅针对 Android strings.xml 的 <string> 内容）
   - 智能避开占位符（如 %s, %1$d, {name} 等）
   - 支持 >Move 这种待翻译标记
支持 .txt、.xml、.json、.pdf 等，单个或批量

用法同之前：
    python converter.py strings.xml values-zh-rCN/strings.xml
    python converter.py app/src/main/res input_res
"""

import sys
import re
from pathlib import Path

# 繁体转简体
from opencc import OpenCC
t2s = OpenCC('t2s')

# 自动英文翻译（离线）
try:
    import argostranslate.package
    import argostranslate.translate
    from argostranslate.translate import Language

    # 首次会自动下载 en → zh 包
    from_code = "en"
    to_code = "zh"
    
    # 更新包索引（只需第一次）
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code,
            available_packages
        ),
        None
    )
    if package_to_install is not None:
        argostranslate.package.install_from_path(package_to_install.download())

    AUTO_TRANSLATE_AVAILABLE = True
    print("成功加载 Argos Translate（英文 → 中文）")
except Exception as e:
    AUTO_TRANSLATE_AVAILABLE = False
    print(f"警告：Argos Translate 未可用，将仅做繁体→简体（错误: {e}）")
    print("    可运行 pip install argostranslate 启用自动翻译")

# PDF 支持（可选）
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("提示：未安装 pdfplumber，PDF 将被跳过（pip install pdfplumber）")

def has_placeholder(text: str) -> bool:
    """判断是否包含常见占位符，避免误翻译"""
    patterns = [
        r'%[0-9]*[sd]',      # %s, %1$s, %d 等
        r'\{[^}]+}',         # {name}, {count}
        r'@string/',         # @string/app_name
        r'@android:',        # Android 资源引用
        r'\\n|\\t|\\\\',     # 转义字符
        r'https?://',        # URL
    ]
    return any(re.search(p, text) for p in patterns)

def auto_en_to_zh(text: str) -> str:
    """使用 Argos Translate 自动翻译英文 → 中文"""
    if not AUTO_TRANSLATE_AVAILABLE:
        return text
    
    stripped = text.strip()
    # 处理 >Move 标记
    prefix = ">"
    if stripped.startswith(">"):
        prefix = ">"
        stripped = stripped[1:]
    
    if not stripped:
        return text
    
    # 如果包含占位符，不翻译
    if has_placeholder(stripped):
        return text
    
    # 只翻译纯英文或基本标点的短语（避免翻译代码）
    if not re.search(r'[a-zA-Z]', stripped):
        return text  # 没有英文，不翻译
    
    try:
        translated = argostranslate.translate.translate(stripped, from_code, to_code)
        return prefix + translated
    except:
        return text  # 出错回退原文本

def translate_xml_strings(content: str) -> str:
    """专门处理 Android strings.xml 的 <string> 标签内容"""
    def replace(match):
        name = match.group(1)
        value = match.group(2).strip()
        
        # 先尝试英文 → 中文（自动）
        translated = auto_en_to_zh(value)
        
        # 再繁体 → 简体（以防有繁体）
        translated = t2s.convert(translated)
        
        # 如果翻译后和原文本一样，说明没变化（可能是已翻译或不适合翻译）
        if translated == value:
            translated = t2s.convert(value)  # 至少保证繁体转简体
        
        return f'<string name="{name}">{translated}</string>'
    
    # 匹配简单 <string name="...">内容</string>，忽略换行和属性顺序
    pattern = r'<string\s+name="([^"]+)"\s*>(.*?)</string>'
    return re.sub(pattern, replace, content, flags=re.DOTALL | re.IGNORECASE)

def convert_txt_or_xml(input_path: Path, output_path: Path):
    try:
        content = input_path.read_text(encoding="utf-8")
        
        if input_path.suffix.lower() == ".xml" and "strings" in input_path.name.lower():
            converted = translate_xml_strings(content)
        else:
            # 其他文本文件只做繁体 → 简体
            converted = t2s.convert(content)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(converted, encoding="utf-8")
        print(f"Success: {input_path} → {output_path}")
    except Exception as e:
        print(f"Failed: {input_path} | 错误: {e}")

def convert_pdf(input_path: Path, output_path: Path):
    if not PDF_SUPPORT:
        print(f"Skip PDF（无 pdfplumber）: {input_path}")
        return
    try:
        full_text = ""
        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        converted = t2s.convert(full_text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(converted, encoding="utf-8")
        print(f"Success PDF → TXT: {input_path} → {output_path}")
    except Exception as e:
        print(f"Failed PDF: {input_path} | 错误: {e}")

# 以下 process_single_file、batch_process、main 函数和之前完全一样，无需改动
def process_single_file(input_path: Path, output_arg: str):
    if '.' in Path(output_arg).name:
        output_path = Path(output_arg)
    else:
        output_dir = Path(output_arg)
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = ".txt" if input_path.suffix.lower() != ".pdf" else ".txt"
        output_path = output_dir / (input_path.stem + "_translated" + suffix)
    
    if input_path.suffix.lower() in {".txt", ".xml", ".json", ".html", ".md"}:
        convert_txt_or_xml(input_path, output_path)
    elif input_path.suffix.lower() == ".pdf":
        convert_pdf(input_path, output_path.with_suffix(".txt"))
    else:
        print(f"Skip 不支持类型: {input_path}")

def batch_process(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    supported = {".txt", ".xml", ".json", ".html", ".md", ".pdf"}
    files = [p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in supported]
    if not files:
        print("Warning: 未找到支持的文件")
        return
    print(f"Success: 发现 {len(files)} 个文件，开始处理...")
    for f in files:
        process_single_file(f, str(output_dir))
    print("All Done: 处理完成！")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    input_arg = sys.argv[1]
    output_arg = sys.argv[2] if len(sys.argv) >= 3 else "output"
    input_path = Path(input_arg)
    if not input_path.exists():
        print(f"Error: 输入不存在: {input_arg}")
        sys.exit(1)
    if input_path.is_file():
        process_single_file(input_path, output_arg)
    else:
        batch_process(input_path, Path(output_arg))

if __name__ == "__main__":
    main()
