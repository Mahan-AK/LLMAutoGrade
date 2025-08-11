#!/usr/bin/env python3

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
import re
import logging
import concurrent.futures
from pathlib import Path
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple
from prompts import submission_extract_and_parse_instruction, grading_instruction
from utils import calculate_gemini_cost

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("submissions_processing.log")
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Process, parse and grade student submission files using Gemini models.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--submissions_dir',
        type=Path,
        required=True,
        help='Path to the submissions directory containing preprocessed student submission folders'
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
    
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of submissions to process in parallel (0 for auto)'
    )
    
    parser.add_argument(
        '--retry_count',
        type=int,
        default=3,
        help='Number of retries for API calls'
    )
    
    parser.add_argument(
        '--regrade',
        action='store_true',
        help='Only regrade submissions without parsing them again'
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



def configure_gemini(api_key: str):
    """Configure Gemini API."""
    logger.info("Configuring Gemini API...")
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        raise

def read_solution_info(solution_dir: Path) -> tuple[Path, str]:
    """Read solution paths from processed_solution_info.json."""
    info_file = solution_dir / "processed_solution_info.json"
    if not info_file.exists():
        raise ValueError(f"Solution info file not found: {info_file}")
    
    try:
        with open(info_file, 'r', encoding='utf-8') as f:
            info_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in solution info file: {str(e)}")
        raise ValueError(f"Invalid solution info file: {str(e)}")
    
    # Get paths from info file
    if 'parsed_solution_path' not in info_data or 'structure_hint_path' not in info_data:
        raise ValueError(f"Missing required keys in solution info file")
    
    solution_path = Path(info_data['parsed_solution_path'])
    hint_path = Path(info_data['structure_hint_path'])
    
    # Validate paths exist
    if not solution_path.exists():
        raise ValueError(f"Parsed solution file not found: {solution_path}")
    if not hint_path.exists():
        raise ValueError(f"Structure hint file not found: {hint_path}")
    
    # Read structural hint and escape curly braces
    try:
        with open(hint_path, 'r', encoding='utf-8') as f:
            structural_hint = f.read().replace('{', '{{').replace('}', '}}')
    except Exception as e:
        logger.error(f"Error reading structural hint file: {str(e)}")
        raise
    
    return solution_path, structural_hint

def read_preprocess_info(submission_dir: Path) -> Optional[Dict[str, Any]]:
    """Read preprocessing information from preprocess_info.json."""
    info_file = submission_dir / "processed" / "preprocess_info.json"
    if not info_file.exists():
        logger.warning(f"Preprocessing info file not found: {info_file}")
        return None
    
    try:
        with open(info_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in preprocessing info file: {str(e)}")
        return None

def parse_student_details(submission_dir: Path) -> Dict[str, str]:
    """Parse student details from submission directory name."""
    dir_name = submission_dir.name
    
    try:
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
    except Exception as e:
        logger.warning(f"Error parsing student details from {dir_name}: {str(e)}")
        return {
            'last_name': dir_name,
            'first_name': "",
            'student_id': "unknown",
            'matriculation_number': "unknown"
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
        logger.error(f"Failed to parse JSON from report: {str(e)}")
        logger.debug(f"JSON string: {json_str}")
        # Return a minimal valid JSON as fallback
        return {
            "error": "Failed to parse grading results",
            "raw_json_str": json_str
        }

def api_call_with_retry(func, *args, max_retries=3, retry_delay=5, **kwargs):
    """Execute an API call with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"API call failed (attempt {attempt+1}/{max_retries+1}): {str(e)}")
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"API call failed after {max_retries+1} attempts: {str(e)}")
                raise

def upload_files_from_preprocessed(submission_dir: Path) -> Tuple[List, Optional[Dict]]:
    """Upload textual and visual files from preprocessed submission."""
    processed_dir = submission_dir / "processed"
    textual_dir = processed_dir / "textual"
    visual_dir = processed_dir / "visual"
    
    # Read preprocessing info
    preprocess_info = read_preprocess_info(submission_dir)
    if not preprocess_info:
        logger.error(f"No preprocessing info found for {submission_dir.name}")
        return [], None
    
    uploaded_files = []
    
    try:
        # Upload textual files
        if textual_dir.exists():
            textual_files = list(textual_dir.iterdir())
            logger.info(f"Uploading {len(textual_files)} textual files...")
            for file_path in textual_files:
                if file_path.is_file():
                    uploaded_file = genai.upload_file(str(file_path))
                    uploaded_files.append(uploaded_file)
                    logger.debug(f"Uploaded textual file: {file_path.name}")
        
        # Upload visual files
        if visual_dir.exists():
            visual_files = list(visual_dir.iterdir())
            logger.info(f"Uploading {len(visual_files)} visual files...")
            # Upload images in batches to avoid memory issues
            batch_size = 10  # Process 10 images at a time
            for i in range(0, len(visual_files), batch_size):
                batch = visual_files[i:i+batch_size]
                for file_path in batch:
                    if file_path.is_file():
                        uploaded_file = genai.upload_file(str(file_path))
                        uploaded_files.append(uploaded_file)
                        logger.debug(f"Uploaded visual file: {file_path.name}")
                logger.info(f"Uploaded batch of {len(batch)} visual files")
        
        logger.info(f"Successfully uploaded {len(uploaded_files)} files total")
        return uploaded_files, preprocess_info
        
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        return [], preprocess_info

def parse_submission(submission_dir: Path, model, retry_count: int = 3) -> Optional[str]:
    """Parse a single submission using Gemini model with preprocessed files."""
    logger.info(f"Processing submission from: {submission_dir.name}")
    
    # Check if submission has been preprocessed
    processed_dir = submission_dir / "processed"
    if not processed_dir.exists():
        # Create a report directory if it doesn't exist
        report_dir = submission_dir.parent / "#invalid_submissions"
        report_dir.mkdir(exist_ok=True)
        
        # Create a report for this submission
        report_path = report_dir / f"{submission_dir.name}_not_preprocessed.txt"
        with open(report_path, 'w') as f:
            f.write(f"Submission: {submission_dir.name}\n")
            f.write(f"Status: NOT PREPROCESSED - Run preprocessing script first\n")
            f.write(f"Expected directory: {processed_dir}\n")
        
        logger.error(f"SUBMISSION NOT PREPROCESSED: {submission_dir.name} - Run preprocessing script first")
        return None
    
    # Upload files from preprocessed directories
    logger.info("Uploading preprocessed files...")
    uploaded_files, preprocess_info = upload_files_from_preprocessed(submission_dir)
    
    if not uploaded_files:
        logger.warning(f"No files were uploaded for {submission_dir.name}")
        return None
    
    # Generate content with all context
    logger.info("Parsing submission with Gemini...")
    
    # Create context about the submission structure
    context_info = f"""
Submission Structure Information:
- Submission Name: {submission_dir.name}
- Total Original Files: {preprocess_info['summary']['total_original_files'] if preprocess_info else 'Unknown'}
- Textual Files: {preprocess_info['summary']['textual_outputs'] if preprocess_info else 'Unknown'}
- Visual Files: {preprocess_info['summary']['visual_outputs'] if preprocess_info else 'Unknown'}

The following files have been uploaded for analysis:
"""
    
    if preprocess_info:
        context_info += "\nTextual files:\n"
        for file_path in preprocess_info.get('textual_files', []):
            context_info += f"- {file_path}\n"
        
        context_info += "\nVisual files:\n"
        for file_path in preprocess_info.get('visual_files', []):
            context_info += f"- {file_path}\n"
    
    inputs = [submission_extract_and_parse_instruction, context_info] + uploaded_files
    
    start_time = time.time()
    try:
        response = api_call_with_retry(
            model.generate_content, 
            inputs, 
            max_retries=retry_count
        )
        elapsed = time.time() - start_time
        logger.info(f"Parsing completed in {elapsed:.2f} seconds")
        
        # Check if response text is empty
        if not response.text or response.text.strip() == "":
            logger.warning("Empty response received from Gemini model!")
            return "Error: Empty response from Gemini model. Please check the submission files."
        
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
                'processing_time_seconds': elapsed,
                'files_processed': len(uploaded_files)
            }
            
            metadata_path = submission_dir / "grading_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Cost metadata saved to: {metadata_path}")
        
        return response.text
    except Exception as e:
        logger.error(f"Error parsing submission: {str(e)}")
        return None

def grade_submission(submission_dir: Path, solution_dir: Path, model, retry_count: int = 3) -> Optional[str]:
    """Grade a submission using Gemini model."""
    # Read the parsed submission
    submission_file = submission_dir / "parsed_submission.md"
    if not submission_file.exists():
        logger.warning(f"Parsed submission file not found: {submission_file}")
        return None
    
    logger.info(f"Grading submission from: {submission_dir.name}")
    
    try:
        # Get solution file path and structural hint
        solution_file, structural_hint = read_solution_info(solution_dir)
        
        # Format the grading instruction with the structural hint
        formatted_grading_instruction = grading_instruction.replace("{structural_hint}", structural_hint)
        
        # Upload files using Gemini API
        logger.info("Uploading files for grading...")
        submission_data = genai.upload_file(str(submission_file))
        solution_data = genai.upload_file(str(solution_file))
        
        # Generate grading report using uploaded files
        logger.info("Generating grading report...")
        inputs = [
            formatted_grading_instruction,
            "\n\nModel Solution:\n",
            solution_data,
            "\n\nStudent Submission:\n",
            submission_data
        ]
        
        start_time = time.time()
        response = api_call_with_retry(
            model.generate_content, 
            inputs, 
            max_retries=retry_count
        )
        elapsed = time.time() - start_time
        logger.info(f"Grading completed in {elapsed:.2f} seconds")
        
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
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in metadata file: {metadata_path}")
            
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
            logger.info(f"Grading metrics saved to: {metadata_path}")
        
        # Extract student details and grading results
        student_details = parse_student_details(submission_dir)
        
        try:
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
            logger.info(f"Grading results saved to: {results_path}")
        except Exception as e:
            logger.error(f"Error extracting or saving grading results: {str(e)}")
            
        return response.text
    except Exception as e:
        logger.error(f"Error grading submission: {str(e)}")
        return None

def process_single_submission(submission_dir: Path, solution_dir: Path, model, retry_count: int, regrade: bool = False):
    """Process a single submission directory."""
    logger.info(f"\nProcessing submission in: {submission_dir}")
    
    parsing_status = "skipped"
    grading_status = "skipped"
    parsing_reason = ""
    grading_reason = ""
    
    # Check if parsed submission already exists
    parsed_submission_path = submission_dir / "parsed_submission.md"
    grading_result_path = submission_dir / "grading_result.json"
    
    try:
        # Handle parsing
        if parsed_submission_path.exists() and not regrade:
            logger.info(f"Skipping parsing for {submission_dir.name} - parsed_submission.md already exists")
            parsing_status = "skipped"
            parsing_reason = "parsed_submission.md already exists"
        else:
            # Parse the submission
            parsed_text = parse_submission(submission_dir, model, retry_count)
            
            if parsed_text:
                # Save the parsed result
                with open(parsed_submission_path, "w", encoding="utf-8") as f:
                    f.write(parsed_text)
                logger.info(f"Parsed submission saved to: {parsed_submission_path}")
                parsing_status = "success"
            else:
                logger.error(f"Failed to parse submission: {submission_dir.name}")
                parsing_status = "failed"
                parsing_reason = "Failed to parse submission"
                return {"parsing": parsing_status, "grading": "skipped", "parsing_reason": parsing_reason, "grading_reason": "Parsing failed"}
        
        # Handle grading - only if parsing was successful or already exists
        if not parsed_submission_path.exists():
            logger.error(f"Cannot grade submission: parsed submission file not found: {parsed_submission_path}")
            grading_status = "failed"
            grading_reason = "No parsed submission file"
            return {"parsing": parsing_status, "grading": grading_status, "parsing_reason": parsing_reason, "grading_reason": grading_reason}
        
        if grading_result_path.exists():
            logger.info(f"Skipping grading for {submission_dir.name} - grading_result.json already exists")
            grading_status = "skipped"
            grading_reason = "grading_result.json already exists"
        else:
            # Grade the submission
            grading_report = grade_submission(submission_dir, solution_dir, model, retry_count)
            
            if grading_report:
                # Save the grading report
                output_path = submission_dir / "grading_report.md"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(grading_report)
                logger.info(f"Grading report saved to: {output_path}")
                grading_status = "success"
            else:
                logger.error(f"Failed to grade submission: {submission_dir.name}")
                grading_status = "failed"
                grading_reason = "Failed to grade submission"
        
        return {"parsing": parsing_status, "grading": grading_status, "parsing_reason": parsing_reason, "grading_reason": grading_reason}
        
    except Exception as e:
        import traceback
        logger.error(f"Error processing submission {submission_dir.name}: {str(e)}")
        logger.debug("Traceback:")
        logger.debug(traceback.format_exc())
        error_reason = f"Exception: {str(e)}"
        return {"parsing": "failed" if parsing_status != "success" else parsing_status, 
                "grading": "failed" if grading_status != "success" else grading_status,
                "parsing_reason": error_reason if parsing_status != "success" else parsing_reason,
                "grading_reason": error_reason if grading_status != "success" else grading_reason}

def get_submission_dirs(submissions_dir: Path) -> List[Path]:
    """Get list of submission directories."""
    submission_dirs = []
    
    for item in submissions_dir.iterdir():
        if item.is_dir() and not item.name.startswith('#'):
            submission_dirs.append(item)
    
    return submission_dirs

def generate_invalid_submissions_summary(submissions_dir: Path):
    """Generate a summary of all invalid submissions."""
    report_dir = submissions_dir / "#invalid_submissions"
    if not report_dir.exists():
        return
    
    summary_path = report_dir / "invalid_submissions_summary.txt"
    with open(summary_path, 'w') as f:
        f.write("=== INVALID SUBMISSIONS SUMMARY ===\n\n")
        
        # Get all report files
        report_files = list(report_dir.glob("*_invalid.txt")) + list(report_dir.glob("*_not_preprocessed.txt"))
        f.write(f"Total invalid submissions: {len(report_files)}\n\n")
        
        # Sort by submission name
        report_files.sort()
        
        for report_file in report_files:
            submission_name = report_file.stem.replace('_invalid', '').replace('_not_preprocessed', '')
            f.write(f"Submission: {submission_name}\n")
            f.write(f"Report: {report_file.name}\n")
            f.write("-" * 50 + "\n")

def generate_processing_report(submissions_dir: Path, results: Dict[str, Dict[str, str]]):
    """Generate a comprehensive parsing and grading report."""
    report_dir = submissions_dir / "#processing_reports"
    report_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for report
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"processing_report_{timestamp}.txt"
    
    # Categorize results
    parsing_success = []
    parsing_skipped = []
    parsing_failed = []
    grading_success = []
    grading_skipped = []
    grading_failed = []
    
    for submission_name, result in results.items():
        # Categorize parsing results
        if result["parsing"] == "success":
            parsing_success.append(submission_name)
        elif result["parsing"] == "skipped":
            parsing_skipped.append((submission_name, result.get("parsing_reason", "Unknown")))
        else:
            parsing_failed.append((submission_name, result.get("parsing_reason", "Unknown")))
        
        # Categorize grading results
        if result["grading"] == "success":
            grading_success.append(submission_name)
        elif result["grading"] == "skipped":
            grading_skipped.append((submission_name, result.get("grading_reason", "Unknown")))
        else:
            grading_failed.append((submission_name, result.get("grading_reason", "Unknown")))
    
    # Write comprehensive report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE PROCESSING REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Submissions Processed: {len(results)}\n\n")
        
        # Parsing Summary
        f.write("PARSING SUMMARY:\n")
        f.write("-" * 40 + "\n")
        f.write(f"✓ Successful: {len(parsing_success)}\n")
        f.write(f"⏭ Skipped: {len(parsing_skipped)}\n")
        f.write(f"✗ Failed: {len(parsing_failed)}\n\n")
        
        # Grading Summary
        f.write("GRADING SUMMARY:\n")
        f.write("-" * 40 + "\n")
        f.write(f"✓ Successful: {len(grading_success)}\n")
        f.write(f"⏭ Skipped: {len(grading_skipped)}\n")
        f.write(f"✗ Failed: {len(grading_failed)}\n\n")
        
        # Detailed Results
        f.write("=" * 80 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        # Parsing Details
        f.write("PARSING RESULTS:\n")
        f.write("-" * 50 + "\n")
        
        if parsing_success:
            f.write("✓ SUCCESSFUL PARSING:\n")
            for name in sorted(parsing_success):
                f.write(f"  • {name}\n")
            f.write("\n")
        
        if parsing_skipped:
            f.write("⏭ SKIPPED PARSING:\n")
            for name, reason in sorted(parsing_skipped):
                f.write(f"  • {name} - {reason}\n")
            f.write("\n")
        
        if parsing_failed:
            f.write("✗ FAILED PARSING:\n")
            for name, reason in sorted(parsing_failed):
                f.write(f"  • {name} - {reason}\n")
            f.write("\n")
        
        # Grading Details
        f.write("GRADING RESULTS:\n")
        f.write("-" * 50 + "\n")
        
        if grading_success:
            f.write("✓ SUCCESSFUL GRADING:\n")
            for name in sorted(grading_success):
                f.write(f"  • {name}\n")
            f.write("\n")
        
        if grading_skipped:
            f.write("⏭ SKIPPED GRADING:\n")
            for name, reason in sorted(grading_skipped):
                f.write(f"  • {name} - {reason}\n")
            f.write("\n")
        
        if grading_failed:
            f.write("✗ FAILED GRADING:\n")
            for name, reason in sorted(grading_failed):
                f.write(f"  • {name} - {reason}\n")
            f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"Comprehensive processing report saved to: {report_path}")
    return report_path

def process_submissions(args):
    """Process all submissions in the submissions directory."""
    logger.info("========== Starting Submissions Processing ==========")
    
    # Configure Gemini
    configure_gemini(args.api_key)
    
    # Initialize model
    logger.info("Initializing Gemini model...")
    model_name = 'gemini-2.5-pro-preview-05-06' if args.model_type == 'pro' else 'gemini-2.5-flash-preview-04-17'
    model = genai.GenerativeModel(model_name)
    logger.info(f"Gemini {args.model_type} model initialized.")
    
    # Get list of submission directories
    submission_dirs = get_submission_dirs(args.submissions_dir)
    logger.info(f"Found {len(submission_dirs)} submissions to process")
    
    # Set up parallel processing
    num_workers = args.parallel
    if num_workers <= 0:
        # Auto-determine based on CPU count, but cap at 4 to avoid API rate limits
        num_workers = min(4, os.cpu_count() or 1)
    
    # Dictionary to store detailed results for reporting
    results = {}
    
    # Process submissions sequentially or in parallel
    if num_workers == 1:
        logger.info("Processing submissions sequentially")
        successful = 0
        for submission_dir in submission_dirs:
            result = process_single_submission(submission_dir, args.solution_dir, model, args.retry_count, args.regrade)
            results[submission_dir.name] = result
            if result["grading"] == "success":
                successful += 1
    else:
        logger.info(f"Processing submissions in parallel with {num_workers} workers")
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(
                    process_single_submission, 
                    submission_dir, 
                    args.solution_dir, 
                    model,
                    args.retry_count,
                    args.regrade
                ): submission_dir
                for submission_dir in submission_dirs
            }
            
            successful = 0
            for future in concurrent.futures.as_completed(futures):
                submission_dir = futures[future]
                submission_name = submission_dir.name
                try:
                    result = future.result()
                    results[submission_name] = result
                    if result["grading"] == "success":
                        successful += 1
                except Exception as e:
                    logger.error(f"Error in thread processing {submission_name}: {str(e)}")
                    results[submission_name] = {
                        "parsing": "failed",
                        "grading": "failed", 
                        "parsing_reason": f"Thread exception: {str(e)}",
                        "grading_reason": f"Thread exception: {str(e)}"
                    }
    
    # Report summary
    logger.info("\n========== Submissions Processing Summary ==========")
    logger.info(f"Total submissions: {len(submission_dirs)}")
    logger.info(f"Successfully processed: {successful}")
    logger.info(f"Failed: {len(submission_dirs) - successful}")
    
    # Generate invalid submissions summary
    generate_invalid_submissions_summary(args.submissions_dir)
    
    # Generate comprehensive processing report
    generate_processing_report(args.submissions_dir, results)
    
    logger.info("========== Submissions Processing Complete ==========")

def main():
    args = parse_arguments()
    process_submissions(args)

if __name__ == "__main__":
    main()