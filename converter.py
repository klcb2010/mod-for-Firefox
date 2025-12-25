#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
繁体中文 / 英文 → 简体中文
- 英文翻译：优先 Argos（离线），Argos 输出原文时 fallback Google Translate
- 仅翻译 XML <string>TEXT</string> 的 TEXT
- 繁体中文统一转简体
"""

import sys
import re
import subprocess
from pathlib import Path
from opencc import OpenCC

cc = OpenCC("t2s")

# ---------- Google Translate（可选 fallback） ----------
try:
    from googletrans import Translator
    translator = Translator()
    HAS_GOOGLE = True
except Exception:
    HAS_GOOGLE = False
    translator = None
    print("提示：未安装 googletrans，Google fallback 已禁用")

# ---------- 英文翻译函数 ----------
def translate_with_argos(text: str) -> str:
    """使用 Argos 翻译英文"""
    try:
        result = subprocess.run(
            ["argos-translate-cli", "--from-lang", "en", "--to-lang", "zh", text],
            capture_output=True,
            text=True,
            check=True
        )
        zh = result.stdout.strip()
        if zh == text and HAS_GOOGLE:
            # fallback Google
            try:
                zh = translator.translate(text, src="en", dest="zh-cn").text
            except Exception:
                zh = text
        return zh
    except Exception:
        if HAS_GOOGLE:
            try:
                zh = translator.translate(text, src="en", dest="zh-cn").text
                return zh
            except Exception:
                return text
        return text

def is_ascii_english(text: str) -> bool:
    """只要含字母且 ASCII，就认为是英文"""
    return any(c.isalpha() for c in text) and all(ord(c) < 128 for c in text)

def convert_xml(content: str) -> str:
    """翻译 XML 中的文本"""
    def repl(m):
        inner = m.group(1)
        if is_ascii_english(inner):
            zh = translate_with_argos(inner)
            zh = cc.convert(zh)
            return f">{zh}</string>"
        return m.group(0)
    return re.sub(r">([^<>]+)</string>", repl, content)

# ---------- 文件处理 ----------
def process_file(inp: Path, out: Path):
    text = inp.read_text(encoding="utf-8")

    if inp.suffix.lower() == ".xml" or text.lstrip().startswith("<?xml"):
        text = convert_xml(text)

    text = cc.convert(text)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Translated: {inp} → {out}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python converter.py input output")
        sys.exit(1)

    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])

    if inp.is_file():
        process_file(inp, out)
    else:
        out.mkdir(parents=True, exist_ok=True)
        for f in inp.rglob("*.xml"):
            process_file(f, out / f.name)

if __name__ == "__main__":
    main()
