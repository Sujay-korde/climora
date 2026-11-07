import subprocess
from pathlib import Path

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
html_path = Path(r"c:\Users\lenovo\climora\CLIMORA_PROJECT_REPORT.html")

with open(html_path, "r", encoding="utf-8") as f:
    full_html = f.read()

# Split by page-break
segments = full_html.split('<div class="page-break"></div>')
print(f"Total defined segments: {len(segments)}")

head = full_html.split("<body>")[0] + "<body>"
tail = "</body></html>"

for idx, seg in enumerate(segments, 1):
    test_html = head + seg + tail
    test_html_file = Path(f"c:/tmp/seg_{idx}.html")
    test_pdf_file = Path(f"c:/tmp/seg_{idx}.pdf")
    with open(test_html_file, "w", encoding="utf-8") as f:
        f.write(test_html)
    
    cmd = [
        edge_path,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={test_pdf_file}",
        str(test_html_file)
    ]
    subprocess.run(cmd, capture_output=True)
    if test_pdf_file.exists():
        with open(test_pdf_file, "rb") as pf:
            content = pf.read()
        import re
        p_count = len(re.findall(rb'/Type\s*/Page\b', content))
        print(f"Segment {idx} produced: {p_count} page(s)")
