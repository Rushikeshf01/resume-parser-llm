import pymupdf
from multi_column import column_boxes
import pymupdf4llm

# file_path = "resumes/Deepak_Pilai.pdf"
# file_path = "resumes\Rushikesh_Falak_Resume_Final.pdf"
file_path = "resumes\Aayush_Johri.pdf"
# file_path = "resumes\Karma-CV.pdf"
doc = pymupdf.open(file_path)
for page in doc:
    bboxes = column_boxes(page, footer_margin=0,header_margin=0, no_image_text=False)
    for rect in bboxes:
        print(page.get_text(clip=rect, sort=True))
    print("-" * 80)

# md_text = pymupdf4llm.to_markdown(file_path)
# print(md_text)