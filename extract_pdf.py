"""Extract Vol. I chapters 1-14 from the user's own PDF into public/vol1.pdf.

Usage: python3 scripts/extract_pdf.py /path/to/feynman-lectures.pdf [out.pdf]
Needs PyMuPDF (pip install pymupdf). The page/figure positions in src/data were computed from the
1376-page edition (63,760,607 bytes); a different edition will misalign them.
"""
import sys
import fitz

FIRST, LAST = 10, 147  # 1-indexed PDF pages: chapter 1 start .. chapter 14 end

out_path = sys.argv[2] if len(sys.argv) > 2 else "public/vol1.pdf"
src = fitz.open(sys.argv[1])
if src.page_count != 1376:
    print(f"warning: expected the 1376-page edition, got {src.page_count} pages; positions may not line up")
out = fitz.open()
out.insert_pdf(src, from_page=FIRST - 1, to_page=LAST - 1)
out.save(out_path, garbage=4, deflate=True)
print(f"wrote {out_path} ({out.page_count} pages)")
