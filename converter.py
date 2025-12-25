#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
繁体中文 / 英文 → 简体中文
- 英文翻译：Argos Translate（离线，稳定）
- 仅翻译 XML 中 >English</string>
"""

import sys
import re
import subprocess
from pathlib import Path
from opencc import OpenCC

cc = OpenCC("t2s")

# ---------- 英文翻译（Argos） ----------

def translate_en_to_zh(text: str) -> str:
    try:
        p = subprocess.run(
            ["argos-translate-cli", "--from-lang", "en", "--to-lang", "zh", text],
            capture_output=True,
            text=True,
            check=True
        )
        return p.stdout.strip()
    except Exception:
        return text

def is_english(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9 .,_\-]+", text.strip()))

def convert_xml_special(content: str) -> str:
    def repl(m):
        inner = m.group(1)
        if is_english(inner):
            zh = translate_en_to_zh(inner)
            return f">{cc.convert(zh)}</string>"
        return m.group(0)

    return re.sub(r">([^<>]+)</string>", repl, content)

# ---------- 文件处理 ----------

def process_file(inp: Path, out: Path):
    text = inp.read_text(encoding="utf-8")
    if inp.suffix.lower() == ".xml":
        text = convert_xml_special(text)
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
