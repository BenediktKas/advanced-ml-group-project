"""
Generate a dummy multi-page PDF fixture for pipeline testing.
Run from the repo root: python scripts/create_dummy_pdf.py
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

OUTPUT = Path(__file__).resolve().parent.parent / "tests" / "samples" / "sample.pdf"


def create_dummy():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4)
    for i in range(3):
        c.drawString(100, 800, "Header: Advanced ML Group Project - Confidential")
        c.drawString(100, 750, f"This is the content of page {i+1}.")
        c.drawString(100, 730, "It contains some sample contract clauses.")
        if i == 0:
            c.drawString(100, 700, "1. Clause A: The contractor must do things.")
        elif i == 1:
            c.drawString(100, 700, "2. Clause B: The contractor gets paid.")
        elif i == 2:
            c.drawString(100, 700, "3. Clause C: Liability is capped.")
        c.drawString(100, 50, f"Footer: Page {i+1} of 3")
        c.showPage()
    c.save()
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    create_dummy()
