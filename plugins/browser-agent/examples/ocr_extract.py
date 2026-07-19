#!/usr/bin/env python3
"""Example: OCR text extraction from images and PDFs."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.browser_agent import BrowserAgent


def main():
    # Auto-select best OCR backend
    agent = BrowserAgent(project_root=os.getcwd(), ocr_backend="auto")

    # Check available backends
    from src.agents.browser_agent.ocr_engine import OCREngine
    ocr = OCREngine()
    availability = ocr.is_available()
    print("OCR backend availability:")
    for backend, available in availability.items():
        status = "available" if available else "not installed"
        print(f"  {backend}: {status}")

    # Extract from image (if you have one)
    image_path = "/path/to/your/image.png"
    if os.path.exists(image_path):
        result = agent.execute({
            "type": "ocr",
            "file_path": image_path,
            "lang": "eng",
        })

        if result.success:
            print(f"\nExtracted text ({result.output.get('backend', 'unknown')}):")
            print(result.output["text"])
        else:
            print(f"Error: {result.errors}")
    else:
        print(f"\nSkipping image OCR (file not found: {image_path})")

    # Extract from PDF (if you have one)
    pdf_path = "/path/to/your/document.pdf"
    if os.path.exists(pdf_path):
        result = agent.execute({
            "type": "ocr",
            "file_path": pdf_path,
            "lang": "eng",
        })

        if result.success:
            pages = result.output.get("pages", [])
            print(f"\nPDF pages processed: {len(pages)}")
            for page in pages[:2]:
                print(f"  Page {page.get('page', '?')}: {page.get('text', '')[:100]}...")
        else:
            print(f"Error: {result.errors}")
    else:
        print(f"Skipping PDF OCR (file not found: {pdf_path})")

    agent.stop()


if __name__ == "__main__":
    main()
