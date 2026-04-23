"""
Generate a dummy multi-page PDF fixture for pipeline testing from sample_contract.txt.
Run from the repo root: python scripts/create_dummy_pdf.py
"""
import textwrap
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "tests" / "samples" / "sample_contract.txt"
OUTPUT = ROOT / "tests" / "samples" / "sample.pdf"

def create_dummy():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4)
    
    try:
        with open(INPUT, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        text = "sample_contract.txt not found!"

    textobject = c.beginText()
    textobject.setTextOrigin(inch, 10.5 * inch)
    textobject.setFont("Helvetica", 11)
    # Give it a light line spacing
    textobject.setLeading(14)
    
    # Word wrap lines for PDF compatability
    for line in text.split('\n'):
        wrapped_lines = textwrap.wrap(line, width=90) or [""]
        for wl in wrapped_lines:
            textobject.textLine(wl)
            
    c.drawText(textobject)
    c.save()
    print(f"Wrote {OUTPUT}")

if __name__ == "__main__":
    create_dummy()
