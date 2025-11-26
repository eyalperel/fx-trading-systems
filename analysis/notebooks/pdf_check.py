from pypdf import PdfReader
import glob, os, sys
pdfs = glob.glob(os.path.join(r'C:\Trading\Ehlers', '*.pdf'))
if not pdfs:
    print('No PDFs found in C:\Trading\Ehlers')
    sys.exit(1)
fn = pdfs[0]
r = PdfReader(fn)
text = r.pages[0].extract_text() or ""
print('file:', os.path.basename(fn))
print('snippet:', text[:800].replace('\n',' '))
