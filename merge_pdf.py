import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NumberObject, NameObject, ArrayObject, FloatObject


def find_pdfs_recursive(folder):
    """Ищем все PDF-файлы рекурсивно и сортируем их по имени"""
    return sorted(Path(folder).rglob("*.pdf"))

from reportlab.lib.pagesizes import A5  # Импортируем A5

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def create_toc_pdf(toc_entries, filename="toc.pdf"):
    """
    Создаёт оглавление в формате A5 с кириллическим шрифтом и переносом строк.
    """
    # Регистрируем TTF-шрифт
    pdfmetrics.registerFont(TTFont('DejaVu', './ttf/DejaVuSans.ttf'))

    c = canvas.Canvas(filename, pagesize=A5)
    width, height = A5
    margin = 15 * mm
    max_width = width - 2 * margin
    line_height = 14

    c.setFont("DejaVu", 16)
    c.drawString(margin, height - margin, "Оглавление")

    c.setFont("DejaVu", 10)
    y = height - margin - 25
    link_rects = []

    for title, page_num in toc_entries:
        text = title
        lines = []
        current_line = ""

        for word in text.split():
            trial = f"{current_line} {word}".strip()
            if pdfmetrics.stringWidth(trial, "DejaVu", 10) < max_width - 35:
                current_line = trial
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for j, line in enumerate(lines):
            is_last_line = (j == len(lines) - 1)
            if is_last_line:
                dots = '.' * max(5, int((max_width - pdfmetrics.stringWidth(line, "DejaVu", 10) - 15) / 3.5))
                display_line = f"{line} {dots} {page_num}"
            else:
                display_line = line

            c.drawString(margin, y, display_line)

            # Добавляем только для последней строки кликабельную ссылку
            if is_last_line:
                text_width = c.stringWidth(display_line, "DejaVu", 10)
                rect = (margin, y - 2, margin + text_width, y + 10)
                link_rects.append((rect, page_num - 1))

            y -= line_height
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont("DejaVu", 10)

    c.save()
    return filename, link_rects


def merge_pdfs_with_toc(toc_pdf_path, pdf_files, output_pdf_path, link_rects):
    writer = PdfWriter()

    # Вставляем страницу оглавления
    toc_reader = PdfReader(toc_pdf_path)
    writer.add_page(toc_reader.pages[0])

    # Вставляем остальные PDF-файлы по порядку
    for pdf_path in pdf_files:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    # Добавляем ссылки (аннотации) в оглавлении (только на первой странице)
    page0 = writer.pages[0]

    for rect, dest_page_idx in link_rects:
        x1, y1, x2, y2 = rect
        annotation = DictionaryObject()
        annotation.update({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject([FloatObject(x1), FloatObject(y1), FloatObject(x2), FloatObject(y2)]),
            NameObject("/Border"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),
            NameObject("/Dest"): writer.pages[dest_page_idx + 1].indirect_reference,
            NameObject("/C"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(1)]),  # синий цвет ссылки
        })
        if "/Annots" in page0:
            page0["/Annots"].append(annotation)
        else:
            page0[NameObject("/Annots")] = ArrayObject([annotation])

    with open(output_pdf_path, "wb") as f_out:
        writer.write(f_out)

    print(f"Готово! Итоговый PDF с оглавлением: {output_pdf_path}")


def main():
    chapters_folder = "./chapters"  # Поменяй на свою папку с PDF главами

    pdf_files = find_pdfs_recursive(chapters_folder)
    if not pdf_files:
        print("PDF-файлы не найдены.")
        return

    toc_entries = []
    page_counter = 1  # Нумерация страниц, начинается после оглавления

    for pdf_path in pdf_files:
        stem = pdf_path.stem
        title = stem.replace("_", " ")  # Можно настроить по своему вкусу
        toc_entries.append((title, page_counter))

        reader = PdfReader(pdf_path)
        page_counter += len(reader.pages)

    toc_pdf, link_rects = create_toc_pdf(toc_entries, "toc.pdf")

    output_pdf = "final_book_with_toc.pdf"
    merge_pdfs_with_toc(toc_pdf, pdf_files, output_pdf, link_rects)


if __name__ == "__main__":
    main()
