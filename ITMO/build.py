#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

def get_section_files():
    """Get all .tex files from sections directory in sorted order."""
    sections_dir = Path('./sections')
    if not sections_dir.exists():
        print("⚠️ Warning: sections directory not found")
        return []
    
    files = list(sections_dir.glob('*.tex'))
    files.sort(key=lambda x: [int(n) for n in re.findall(r'\d+', x.name)])
    return files

def update_main_tex(section_files):
    """Update main.tex with the current list of section files."""
    main_tex = Path('main.tex')
    if not main_tex.exists():
        print("❌ Error: main.tex not found")
        return False

    content = main_tex.read_text(encoding='utf-8')

    # Маркеры начала и конца
    sections_marker_start = "% Input all section files"
    sections_marker_end = "% End of sections"

    pattern = re.escape(sections_marker_start) + r".*?" + re.escape(sections_marker_end)

    if not re.search(pattern, content, re.DOTALL):
        print("❌ Error: Could not find section markers in main.tex")
        return False

    # Формируем блок с \input
    section_lines = [f"\\input{{{str(f).replace('\\', '/')}}}" for f in section_files]
    new_block = sections_marker_start + "\n" + "\n".join(section_lines) + "\n" + sections_marker_end

    # 👇 Замена через функцию, чтобы избежать проблем с \
    new_content = re.sub(pattern, lambda m: new_block, content, flags=re.DOTALL)

    main_tex.write_text(new_content, encoding='utf-8')
    print("✅ main.tex обновлён!")
    return True

def compile_document():
    """Compile the LaTeX document using pdflatex."""
    try:
        print("✅ main.tex успешно скомпилирован!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка компиляции: {e}")
        return False
    except FileNotFoundError:
        print("❌ pdflatex не найден. Установи TeX Live или MiKTeX.")
        return False

def main():
    section_files = get_section_files()
    if not section_files:
        print("⚠️ Нет .tex файлов в папке sections.")
        return

    if not update_main_tex(section_files):
        print("❌ Не удалось обновить main.tex")
        return

    if compile_document():
        print("🎉 Сборка завершена!")
    else:
        print("❌ Сборка не удалась.")

if __name__ == '__main__':
    main()
