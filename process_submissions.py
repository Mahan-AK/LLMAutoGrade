#!/usr/bin/env python3

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
import re
from pathlib import Path
import google.generativeai as genai
from PyPDF2 import PdfReader
from typing import List, Dict, Any
from prompts import submission_extract_and_parse_instruction, grading_instruction
from utils import calculate_gemini_cost

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Process, parse and grade student submission PDF files using Gemini models.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--submissions_dir',
        type=Path,
        required=True,
        help='Path to the submissions directory containing student submission folders'
    )
    
    parser.add_argument(
        '--solution_dir',
        type=Path,
        required=True,
        help='Path to the solution directory containing processed_solution_info.json'
    )
    
    parser.add_argument(
        '--api_key',
        required=True,
        help='Gemini API key'
    )

    parser.add_argument(
        '--model_type',
        choices=['pro', 'flash'],
        default='pro',
        help='Type of Gemini model to use (pro or flash)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.submissions_dir.exists():
        parser.error(f"Submissions directory not found: {args.submissions_dir}")
    if not args.solution_dir.exists():
        parser.error(f"Solution directory not found: {args.solution_dir}")
    if not args.api_key:
        parser.error(f"API key not provided")
    
    return args

def get_pdf_page_count(pdf_path: Path) -> int:
    """Get the number of pages in a PDF file."""
    with open(pdf_path, 'rb') as file:
        pdf = PdfReader(file)
        return len(pdf.pages)

def convert_pdf_to_images(pdf_path: Path, temp_dir: Path, num_pages: int) -> List[Path]:
    """Convert PDF pages to images and return list of image paths."""
    image_paths = []
    for i in range(1, num_pages + 1):
        output_prefix = temp_dir / "submission_page_tmp"
        subprocess.run([
            "pdftoppm",
            "-png",
            "-f", str(i),
            "-l", str(i),
            str(pdf_path),
            str(output_prefix)
        ], check=True)
        
        old_name = f"{output_prefix}-{i}.png"
        new_name = temp_dir / f"submission_page_{i}.png"
        os.rename(old_name, new_name)
        image_paths.append(new_name)
    
    return image_paths

def extract_text_from_pdf(pdf_path: Path, text_file: Path):
    """Extract text from PDF file."""
    subprocess.run(["pdftotext", str(pdf_path), str(text_file)], check=True)

def configure_gemini(api_key: str):
    """Configure Gemini API."""
    print("Configuring Gemini API...")
    genai.configure(api_key=api_key)
    print("Gemini API configured.")

def read_solution_info(solution_dir: Path) -> tuple[Path, str]:
    """Read solution paths from processed_solution_info.json."""
    info_file = solution_dir / "processed_solution_info.json"
    if not info_file.exists():
        raise ValueError(f"Solution info file not found: {info_file}")
    
    with open(info_file, 'r', encoding='utf-8') as f:
        info_data = json.load(f)
    
    # Get paths from info file
    solution_path = Path(info_data['parsed_solution_path'])
    hint_path = Path(info_data['structure_hint_path'])
    
    # Validate paths exist
    if not solution_path.exists():
        raise ValueError(f"Parsed solution file not found: {solution_path}")
    if not hint_path.exists():
        raise ValueError(f"Structure hint file not found: {hint_path}")
    
    # Read structural hint and escape curly braces
    with open(hint_path, 'r', encoding='utf-8') as f:
        structural_hint = f.read().replace('{', '{{').replace('}', '}}')
    
    return solution_path, structural_hint

def parse_student_details(submission_dir: Path) -> Dict[str, str]:
    """Parse student details from submission directory name."""
    dir_name = submission_dir.name
    
    # First split to get matriculation number, then split remaining to get name and student ID
    name_and_id, matriculation = dir_name.rsplit('_', 1)
    name_part, student_id = name_and_id.rsplit('_', 1)
    
    # Split the name part by underscore
    name_parts = name_part.split('_')
    
    # Handle cases where name might have multiple parts
    last_name = name_parts[0]
    first_name = '_'.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]
    
    return {
        'last_name': last_name,
        'first_name': first_name,
        'student_id': student_id,
        'matriculation_number': matriculation
    }

def extract_json_from_report(report: str) -> Dict[str, Any]:
    """Extract JSON data from the grading report."""
    # Find the last JSON block in the report
    json_blocks = re.findall(r'```json\s*(.*?)\s*```', report, re.DOTALL)
    if not json_blocks:
        raise ValueError("No JSON data found in the grading report")
    
    # Get the last JSON block
    json_str = json_blocks[-1]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from report: {str(e)}")

def parse_submission(submission_dir: Path, temp_dir: Path, model) -> str:
    """Parse a single submission using Gemini model."""
    # Find the PDF file in the submission directory
    pdf_files = list(submission_dir.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF file found in {submission_dir}")
    pdf_path = pdf_files[0]  # Take the first PDF file found
    
    print(f"Processing submission from: {submission_dir.name}")
    
    # Get page count
    num_pages = get_pdf_page_count(pdf_path)
    
    # Convert PDF to images
    print("Converting PDF to images...")
    image_paths = convert_pdf_to_images(pdf_path, temp_dir, num_pages)
    
    # Extract text
    text_file = temp_dir / "submission_text.txt"
    extract_text_from_pdf(pdf_path, text_file)
    
    # Upload files for Gemini
    print("Uploading files for parsing...")
    pdf_file = genai.upload_file(str(pdf_path))
    image_files = [genai.upload_file(str(img_path)) for img_path in image_paths]
    
    # Generate content with all context
    print("Parsing submission with Gemini...")
    inputs = [submission_extract_and_parse_instruction, pdf_file] + image_files
    
    start_time = time.time()
    response = model.generate_content(inputs)
    elapsed = time.time() - start_time
    print(f"Parsing completed in {elapsed:.2f} seconds")
    
    # Calculate cost using usage metadata
    if hasattr(response, 'usage_metadata'):
        prompt_tokens = response.usage_metadata.prompt_token_count
        completion_tokens = response.usage_metadata.candidates_token_count
        model_type = 'pro' if 'pro' in model.model_name else 'flash'
        cost = calculate_gemini_cost(model_type, prompt_tokens, completion_tokens)
        
        # Save cost metadata
        metadata = {}
        metadata['parsing'] = {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'cost_usd': cost,
            'model_type': model_type,
            'processing_time_seconds': elapsed
        }
        
        metadata_path = submission_dir / "grading_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Cost metadata saved to: {metadata_path}")
    
    # Check if response text is empty
    if not response.text or response.text.strip() == "":
        print("WARNING: Empty response received from Gemini model!")
    
    return response.text

def grade_submission(submission_dir: Path, solution_dir: Path, model) -> str:
    """Grade a submission using Gemini model."""
    # Read the parsed submission
    submission_file = submission_dir / "parsed_submission.md"
    if not submission_file.exists():
        raise ValueError(f"Parsed submission file not found: {submission_file}")
    
    print(f"Grading submission from: {submission_dir.name}")
    
    # Get solution file path and structural hint
    solution_file, structural_hint = read_solution_info(solution_dir)
    
    # Format the grading instruction with the structural hint
    formatted_grading_instruction = grading_instruction.replace("{structural_hint}", structural_hint)
    
    # Upload files using Gemini API
    print("Uploading files for grading...")
    submission_data = genai.upload_file(str(submission_file))
    solution_data = genai.upload_file(str(solution_file))
    
    # Generate grading report using uploaded files
    print("Generating grading report...")
    inputs = [
        formatted_grading_instruction,
        "\n\nModel Solution:\n",
        solution_data,
        "\n\nStudent Submission:\n",
        submission_data
    ]
    
    start_time = time.time()
    response = model.generate_content(inputs)
    elapsed = time.time() - start_time
    print(f"Grading completed in {elapsed:.2f} seconds")
    
    # Calculate cost using usage metadata
    if hasattr(response, 'usage_metadata'):
        prompt_tokens = response.usage_metadata.prompt_token_count
        completion_tokens = response.usage_metadata.candidates_token_count
        model_type = 'pro' if 'pro' in model.model_name else 'flash'
        cost = calculate_gemini_cost(model_type, prompt_tokens, completion_tokens)
        
        # Load existing metadata if it exists
        metadata_path = submission_dir / "grading_metadata.json"
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Add grading metrics
        metadata['grading'] = {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'cost_usd': cost,
            'model_type': model_type,
            'processing_time_seconds': elapsed
        }
        
        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Grading metrics saved to: {metadata_path}")
    
    # Extract student details and grading results
    student_details = parse_student_details(submission_dir)
    grading_results = extract_json_from_report(response.text)
    
    # Combine student details with grading results
    final_results = {
        'student_details': student_details,
        'grading_results': grading_results
    }
    
    # Save the combined results
    results_path = submission_dir / "grading_result.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2)
    print(f"Grading results saved to: {results_path}")
    
    return response.text

def process_submissions(args):
    """Process all submissions in the submissions directory."""
    print("========== Starting Submissions Processing ==========")
    
    # Configure Gemini
    configure_gemini(args.api_key)
    
    # Initialize model
    print("Initializing Gemini model...")
    model_name = 'gemini-2.5-pro-preview-05-06' if args.model_type == 'pro' else 'gemini-2.5-flash-preview-04-17'
    model = genai.GenerativeModel(model_name)
    print(f"Gemini {args.model_type} model initialized.")
    
    # Process each submission directory
    for item in args.submissions_dir.iterdir():
        # Handle orphaned PDF files
        if item.is_file() and item.suffix.lower() == '.pdf':
            print(f"\nFound orphaned PDF file: {item.name}")
            # Create folder name from PDF filename (without extension)
            folder_name = f"{item.stem}_None_None_None"
            new_dir = args.submissions_dir / folder_name
            os.makedirs(new_dir, exist_ok=True)
            
            # Move PDF to new directory
            new_pdf_path = new_dir / item.name
            shutil.move(str(item), str(new_pdf_path))
            print(f"Moved PDF to new directory: {new_dir}")
            submission_dir = new_dir
        elif item.is_dir():
            submission_dir = item
        else:
            continue
            
        print(f"\nProcessing submission in: {submission_dir}")
        
        # Create temporary directory for preprocessing files
        temp_dir = submission_dir / "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Parse the submission
            parsed_text = parse_submission(submission_dir, temp_dir, model)
            
            # Save the parsed result
            output_path = submission_dir / f"parsed_submission.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(parsed_text)
            print(f"Parsed submission saved to: {output_path}")
            
            # Grade the submission
            grading_report = grade_submission(submission_dir, args.solution_dir, model)
            
            # Save the grading report
            output_path = submission_dir / "grading_report.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(grading_report)
            print(f"Grading report saved to: {output_path}")
            
        except Exception as e:
            import traceback
            print(f"Error processing submission {submission_dir.name}: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
    print("\n========== Submissions Processing Complete ==========")

def main():
    args = parse_arguments()
    process_submissions(args)

if __name__ == "__main__":
    main()