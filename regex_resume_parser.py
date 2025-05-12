import os
import re
import json
import subprocess
import tempfile
from tempfile import TemporaryDirectory
from pikepdf import Pdf
from ocrmypdf import ocr
from pdf2image import convert_from_path
from paddleocr import PaddleOCR

class ApiDocumentProcessor:
    def __init__(self):
        self.temp_dir = TemporaryDirectory()
        self.image_dir = os.path.join(self.temp_dir.name, "images")
        os.makedirs(self.image_dir, exist_ok=True)
        print("Document processor started - temporary workspace created")

    def __del__(self):
        self.temp_dir.cleanup()
        print("Cleanup complete - temporary files removed")

    def _remove_interpolate_flag(self, input_pdf: str, output_pdf: str):
        """Remove /Interpolate flag from all image XObjects in the PDF."""
        with pikepdf.open(input_pdf) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                resources = page.get("/Resources")
                if not resources:
                    continue
                xobjects = resources.get("/XObject")
                if not xobjects:
                    continue
                for xobj_name, xobj in xobjects.items():
                    if xobj.get("/Subtype") == "/Image" and "/Interpolate" in xobj:
                        print(f"Page {page_number}: Removing /Interpolate from image {xobj_name}")
                        del xobj["/Interpolate"]
            pdf.save(output_pdf)
            print(f"Saved preprocessed PDF to {output_pdf}")

    def convert_to_pdfa(self, input_path: str) -> str:
        """Convert file to PDF/A with OCR using temporary files"""
        try:
            print("Starting PDF conversion - making document readable for computers")
            output_path = os.path.join(self.temp_dir.name, "processed.pdf")

            # Step 1: Remove /Interpolate flags
            preprocessed_pdf = os.path.join(self.temp_dir.name, "no_interpolate.pdf")
            self._remove_interpolate_flag(input_path, preprocessed_pdf)

            # Step 2: Convert to PDF/A-2B using Ghostscript
            temp_pdfa2b = os.path.join(self.temp_dir.name, "temp_pdfa2b.pdf")
            print("Converting document to PDF/A format")
            subprocess.run([
                'gs', '-dPDFA=2', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE',
                '-sProcessColorModel=DeviceRGB', '-sDEVICE=pdfwrite',
                '-dPDFACompatibilityPolicy=1', '-sColorConversionStrategy=RGB',
                '-dINTERPOLATE=false',
                '-dNumRenderingThreads=4',
                f'-sOutputFile={temp_pdfa2b}', preprocessed_pdf
            ], check=True, capture_output=True)

            # Step 3: Apply OCR to make it searchable
            print("Adding text recognition layer to document")
            ocrmypdf.ocr(
                temp_pdfa2b,
                output_path,
                force_ocr=True,
                output_type='pdfa',
                optimize=1
            )
            print("Document conversion completed successfully")
            return output_path

        except Exception as e:
            logger.error(f"Document conversion failed: {str(e)}")
            raise RuntimeError(f"PDF processing failed: {str(e)}")

    def pdf_to_images(self, pdf_path, dpi=300, output_folder='pdf_images'):
        """
        Convert a PDF into images (one per page) and save them in an output folder.
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        print("Converting PDF pages to images")
        images = convert_from_path(pdf_path, dpi=dpi)
        image_paths = []
        for i, image in enumerate(images, start=1):
            image_file = os.path.join(output_folder, f'page_{i}.png')
            image.save(image_file, 'PNG')
            image_paths.append(image_file)
            print(f"Created image for page {i}")
        
        print(f"PDF converted to {len(image_paths)} images")
        return image_paths

    def perform_ocr_on_images(self, image_paths, lang="en"):
        """
        Use PaddleOCR to extract text from each image.
        """
        print("Starting text recognition")
        ocr = PaddleOCR(use_angle_cls=True, lang=lang)
        results = {}
        for page_num, image_path in enumerate(image_paths, start=1):
            print(f"Reading text from page {page_num}")
            ocr_result = ocr.ocr(image_path, cls=True)
            if ocr_result and len(ocr_result) > 0 and isinstance(ocr_result[0], list):
                texts = [line[1][0] for line in ocr_result[0] if line[1][0].strip()]
                print(f"Found {len(texts)} text lines on page {page_num}")
            else:
                texts = []
                print(f"No text found on page {page_num}")
                
            results[page_num] = texts
        
        print("Text recognition complete")
        return results

    def organize_ocr_output(self, ocr_results):
        """
        Organize the OCR output into a single formatted string with page markers.
        """
        print("Organizing extracted text by page")
        organized_text = ""
        for page in sorted(ocr_results.keys()):
            organized_text += f"Page {page}:\n"
            for item in ocr_results[page]:
                # If the item is a list, join its elements; otherwise, convert to string
                if isinstance(item, list):
                    line = " ".join(map(str, item))
                else:
                    line = str(item)
                organized_text += line.strip() + "\n"
            organized_text += "\n"  # Extra newline between pages
        
        print("Text organization complete")
        return organized_text

    # 1) Define your regex patterns
    RESUME_PATTERNS = {
        "name": re.compile(
            r"^(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$", 
            re.MULTILINE
        ),
        "email": re.compile(
            r"(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,})"
        ),
        "phone": re.compile(
            r"(?P<phone>\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3}[-.\s]?\d{3,5})"
        ),
        "linkedin": re.compile(
            r"(?P<linkedin>https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+)"
        ),
        "github": re.compile(
            r"(?P<github>https?://(?:www\.)?github\.com/[A-Za-z0-9_-]+)"
        ),
        # Capture a Skills section: from “Skills” down to a blank line
        "skills": re.compile(
            r"(?s)(?:Skills|Technical Skills)\s*[:\-]?\s*(?P<skills>.+?)(?=\n\s*\n|\Z)"
        ),
        # Capture an Experience section: from “Experience” down to next header
        "experience": re.compile(
            r"(?s)(?:Experience|Work Experience)\s*[:\-]?\s*(?P<experience>.+?)(?=\n[A-Z][a-z]+:|\Z)"
        ),
        # Capture Education similarly
        "education": re.compile(
            r"(?s)(?:Education)\s*[:\-]?\s*(?P<education>.+?)(?=\n[A-Z][a-z]+:|\Z)"
        ),
        # Years of experience as a number
        "years_experience": re.compile(
            r"(?P<years>\d+)\s+years?\s+of\s+experience", re.IGNORECASE
        ),
    }

    def extract_resume_data(self, text: str) -> dict:
        """
        Run our suite of regexes on the raw OCR'd text and build a dict.
        """
        data = {}
        for key, pattern in self.RESUME_PATTERNS.items():
            match = pattern.search(text)
            if match:
                # If the pattern has a named group, pull that out
                if match.lastgroup:
                    data[key] = match.group(match.lastgroup).strip()
                else:
                    data[key] = match.group(0).strip()

        # Post-process: split skills into a list (by commas or bullets)
        if "skills" in data:
            raw = data["skills"]
            items = re.split(r"[,;\n•]", raw)
            data["skills"] = [i.strip() for i in items if i.strip()]

        return data

    def process_pdf(self, file_stream) -> dict:
        """Main processing pipeline for PDF files"""
        print("Starting document processing")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(file_stream.read())
            tmp_input.flush()
            print("Document saved to temporary file")
            
            try:
                # Convert to PDF/A with OCR
                print("Preparing document for analysis")
                processed_path = self.convert_to_pdfa(tmp_input.name)

                # First llm api ocr
                print("Breaking document into images for text extraction")
                image_files = self.pdf_to_images(processed_path)
                
                print("Reading text from document images")
                ocr_results = self.perform_ocr_on_images(image_files)
                context_text = self.organize_ocr_output(ocr_results)

                print("Extracting resume fields via regex…")
                resume_data = self.extract_resume_data(context_text)
                print("Resume parser output:", resume_data)

                # 3) Merge with your existing JSON output or return separately
                #    For example, add it under a top‐level "resume" key:
                json_result = {
                    "document_type": report_type,
                    "parsed_text": context_text,
                    "resume": resume_data
                }
                return json_result
                
            except Exception as e:
                logger.error(f"Document processing failed: {str(e)}")
                raise RuntimeError(f"Processing failed: {str(e)}")
            finally:
                print("Cleaning up temporary file")
                os.unlink(tmp_input.name)
