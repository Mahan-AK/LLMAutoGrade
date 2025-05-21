#!/usr/bin/env python3

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path
import google.generativeai as genai
from PyPDF2 import PdfReader
from typing import List, Dict, Any
from prompts import solution_extract_instruction, solution_parse_instruction, solution_parse_format_desc, solution_parse_fix_mistakes_instruction

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Process and parse solution PDF files using Gemini models.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # All arguments are now optional with required=True, so they must be passed as --key value
    parser.add_argument(
        '--assignment_id',
        required=True,
        help='The ID of the assignment to process'
    )
    
    parser.add_argument(
        '--solution_pdf_path',
        type=Path,
        required=True,
        help='Path to the solution PDF file'
    )
    
    parser.add_argument(
        '--structure_hint_path',
        type=Path,
        required=True,
        help='Path to the structure hint file'
    )
    
    parser.add_argument(
        '--api_key',
        required=True,
        help='Gemini API key'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('Model_Solutions'),
        help='Base directory for output files'
    )
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not args.solution_pdf_path.exists():
        parser.error(f"Solution PDF file not found: {args.solution_pdf_path}")
    if not args.structure_hint_path.exists():
        parser.error(f"Structure hint file not found: {args.structure_hint_path}")
    if not args.api_key:
        parser.error(f"API key not provided")
    
    return args

def create_directories(assignment_dir: Path, pages_dir: Path):
    """Create necessary directories for processing."""
    os.makedirs(assignment_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)

def move_files(source_path: Path, dest_path: Path):
    """Move files to their destination."""
    shutil.move(str(source_path), str(dest_path))

def get_pdf_page_count(pdf_path: Path) -> int:
    """Get the number of pages in a PDF file."""
    with open(pdf_path, 'rb') as file:
        pdf = PdfReader(file)
        return len(pdf.pages)

def convert_pdf_to_images(pdf_path: Path, pages_dir: Path, num_pages: int):
    """Convert PDF pages to images."""
    for i in range(1, num_pages + 1):
        output_prefix = pages_dir / "model_solution_page_tmp"
        subprocess.run([
            "pdftoppm",
            "-png",
            "-f", str(i),
            "-l", str(i),
            str(pdf_path),
            str(output_prefix)
        ], check=True)
        
        old_name = f"{output_prefix}-{i}.png"
        new_name = pages_dir / f"model_solution_page_{i}.png"
        os.rename(old_name, new_name)

def extract_text_from_pdf(pdf_path: Path, text_file: Path):
    """Extract text from PDF file."""
    subprocess.run(["pdftotext", str(pdf_path), str(text_file)], check=True)

def create_json_output(assignment_id: str, assignment_dir: Path, pdf_basename: str, 
                      text_file: Path, structure_hint_basename: str, 
                      pages_dir: Path, num_pages: int):
    """Create JSON metadata file."""
    json_data = {
        "assignment_id": assignment_id,
        "solution_pdf_path": str(assignment_dir / pdf_basename),
        "solution_text_path": str(text_file),
        "structure_hint_path": str(assignment_dir / structure_hint_basename),
        "solution_images": [
            str(pages_dir / f"model_solution_page_{i}.png")
            for i in range(1, num_pages + 1)
        ]
    }
    
    json_file = assignment_dir / "processed_solution_info.json"
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)

def update_json_with_parsed_solution(assignment_dir: Path, parsed_solution_path: Path):
    """Update JSON metadata file with parsed solution path."""
    json_file = assignment_dir / "processed_solution_info.json"
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    
    json_data["parsed_solution_path"] = str(parsed_solution_path)
    
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)

def configure_gemini(api_key: str):
    """Configure Gemini API."""
    print("[1/7] Configuring Gemini API...")
    genai.configure(api_key=api_key)
    print("    Gemini API configured.")

def get_solution_metadata(solution_dir: Path) -> Dict[str, Any]:
    """Load the parsed solution info from JSON file."""
    print(f"[2/7] Loading solution metadata from {solution_dir / 'processed_solution_info.json'}...")
    json_path = solution_dir / "processed_solution_info.json"
    with open(json_path, 'r') as f:
        metadata = json.load(f)
    print("    Solution metadata loaded.")
    return metadata

def read_structure_hint(hint_path: Path) -> str:
    """Read the structure hint file."""
    print(f"[3/7] Reading structure hint from {hint_path}...")
    with open(hint_path, 'r') as f:
        hint = f.read()
    print("    Structure hint loaded.")
    return hint

def extract_markdown_from_pdf(pdf_path: Path, flash_model) -> str:
    """Extract markdown from the PDF file using Gemini Flash model."""
    print(f"[4/7] Uploading PDF file for extraction: {pdf_path} ...")
    pdf_file = genai.upload_file(str(pdf_path))
    print("    PDF file uploaded. Generating markdown from PDF using Gemini Flash model...")
    start_time = time.time()
    response = flash_model.generate_content(
        [
            solution_extract_instruction,
            pdf_file
        ]
    )
    elapsed = time.time() - start_time
    print(f"    Markdown extracted from PDF. (Generation took {elapsed:.2f} seconds)")
    print("    Usage metadata for PDF extraction:", getattr(response, "usage_metadata", None))
    return response.text

def enhance_markdown_with_images(
    markdown_path: Path,
    image_paths: List[str],
    structure_hint: str,
    pro_model
) -> str:
    """Enhance the markdown file using images and structure hint with Gemini Pro model."""
    print(f"[5/7] Uploading markdown file: {markdown_path} ...")
    markdown_file = genai.upload_file(str(markdown_path))
    print("    Markdown file uploaded.")

    print(f"[6/7] Uploading {len(image_paths)} image(s)...")
    image_files = []
    for idx, img_path in enumerate(image_paths):
        print(f"        Uploading image {idx+1}/{len(image_paths)}: {img_path}")
        image_files.append(genai.upload_file(img_path))
    print("    All images uploaded.")

    full_instruction = (
        solution_parse_instruction
        + "\n"
        + solution_parse_format_desc.format(structural_hint=structure_hint)
        + "\n"
        + solution_parse_fix_mistakes_instruction
    )

    print("    Generating enhanced markdown with Gemini Pro model...")
    inputs = [full_instruction, markdown_file] + image_files

    start_time = time.time()
    response = pro_model.generate_content(inputs)
    elapsed = time.time() - start_time
    print(f"    Enhanced markdown generated. (Generation took {elapsed:.2f} seconds)")
    print("    Usage metadata for markdown enhancement:", getattr(response, "usage_metadata", None))
    return response.text

def process_and_parse_solution(args):
    """Main function to process and parse a solution file."""
    print("========== Starting Solution Processing and Parsing ==========")
    
    # Create paths
    assignment_dir = args.output_dir / f"Assignment_{args.assignment_id}"
    pages_dir = assignment_dir / "pages"
    
    # Create directories
    create_directories(assignment_dir, pages_dir)
    
    # Move files
    pdf_basename = args.solution_pdf_path.name
    structure_hint_basename = args.structure_hint_path.name
    
    move_files(args.solution_pdf_path, assignment_dir / pdf_basename)
    move_files(args.structure_hint_path, assignment_dir / structure_hint_basename)
    
    # Process PDF
    pdf_path = assignment_dir / pdf_basename
    num_pages = get_pdf_page_count(pdf_path)
    
    # Convert PDF to images
    convert_pdf_to_images(pdf_path, pages_dir, num_pages)
    
    # Extract text
    text_file = assignment_dir / "solution_text.txt"
    extract_text_from_pdf(pdf_path, text_file)
    
    # Create JSON output
    create_json_output(
        args.assignment_id,
        assignment_dir,
        pdf_basename,
        text_file,
        structure_hint_basename,
        pages_dir,
        num_pages
    )
    
    print("========== Starting Solution Parsing ==========")
    
    # Configure Gemini
    configure_gemini(args.api_key)
    
    # Initialize models
    print("[*] Initializing Gemini models...")
    flash_model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
    pro_model = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')
    print("    Gemini models initialized.")

    # Load metadata and structure hint
    solution_info = get_solution_metadata(assignment_dir)
    structure_hint = read_structure_hint(Path(solution_info['structure_hint_path']))

    # Step 1: Extract markdown from PDF and save to file
    print("[3/7] Extracting markdown from PDF and saving to file...")
    markdown_text = extract_markdown_from_pdf(Path(solution_info['solution_pdf_path']), flash_model)
    markdown_path = assignment_dir / "extracted_solution_text.md"
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_text)
    print(f"    Markdown extracted and saved to {markdown_path}")

    # Step 2: Enhance markdown using images and structure hint
    print("Enhancing markdown with images and structure hint...")
    final_text = enhance_markdown_with_images(
        markdown_path,
        solution_info['solution_images'],
        structure_hint,
        pro_model
    )

    # Write the final result
    output_path = assignment_dir / f"parsed_solution_{args.assignment_id}.md"
    print(f"Writing final solution to {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    
    print(f"Solution written to {output_path}")
    print("========== Solution Processing and Parsing Complete ==========")

def main():
    args = parse_arguments()
    process_and_parse_solution(args)

if __name__ == "__main__":
    main() 