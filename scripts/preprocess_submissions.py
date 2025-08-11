#!/usr/bin/env python3
"""
Preprocessing script for student submissions.
Handles various file formats and converts them into a standardized structure
with separate textual and visual data folders.
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import logging
import concurrent.futures
import signal
import time
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import mimetypes

# Required imports - script will fail if not available
import rarfile
import psutil
from PIL import Image
import PyPDF2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("preprocessing.log")
    ]
)
logger = logging.getLogger(__name__)

class SubmissionPreprocessor:
    """Handles preprocessing of various submission file formats."""
    
    # File type categorizations
    TEXTUAL_EXTENSIONS = {
        '.txt', '.py', '.md', '.json', '.csv', '.xml', '.yaml', '.yml',
        '.js', '.css', '.sql', '.r', '.m', '.c', '.cpp', '.h',
        '.java', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.tex'
    }
    
    VISUAL_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
        '.svg', '.webp', '.ico', '.eps'
    }
    
    MIXED_EXTENSIONS = {
        '.pdf', '.ipynb', '.html', '.pptx', '.ppt', '.docx', '.doc',
        '.odt', '.rtf'
    }
    
    ARCHIVE_EXTENSIONS = {
        '.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tar.bz2', '.gz'
    }
    
    # Files to skip or ignore
    SKIP_FILES = {
        '.DS_Store', 'Thumbs.db', 'desktop.ini', '__MACOSX'
    }
    
    SKIP_EXTENSIONS = {
        '.npy', '.npz', '.pkl', '.pickle', '.mat', '.rds', '.rdata',
        '.h5', '.hdf5', '.db', '.sqlite', '.sqlite3', '.exe', '.msi',
        '.dmg', '.app', '.dll', '.so', '.dylib', '.bin', '.dat',
        '.tmp', '.log', '.cache', '.bak', '.swp'
    }
    
    def __init__(self):
        """Initialize preprocessor with hardcoded optimal settings."""
        # Hardcoded limits optimized for LLM processing
        self.max_pdf_pages = 30
        self.max_image_resolution = 2048
        self.pdf_dpi = 96
        self.min_pdf_text_length = 50
        
        # Size limits per file type (in MB)
        self.size_limits = {
            'textual': 5,
            'visual': 10,
            'mixed': 75,
            'archive': 100
        }
        
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check if required external tools are available."""
        required_tools = {
            'pandoc': 'pandoc --version',
            'libreoffice': 'libreoffice --version',
            'pdftoppm': 'pdftoppm -h',
            'pdftotext': 'pdftotext -h',
            'jupyter': 'jupyter --version'
        }
        
        missing_tools = []
        for tool, check_cmd in required_tools.items():
            try:
                subprocess.run(check_cmd.split(), capture_output=True, check=True)
                logger.info(f"✓ {tool} is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
        
        if missing_tools:
            logger.error(f"Missing required tools: {missing_tools}")
            logger.error("Please install all required tools before running.")
            sys.exit(1)

    def should_process_file(self, file_path: Path) -> Tuple[bool, str, str]:
        """
        Check if a file should be processed and determine its category.
        Returns (should_process, category, skip_reason)
        """
        file_name = file_path.name
        extension = file_path.suffix.lower()
        
        # Skip system and hidden files
        if (file_name.startswith('._') or 
            file_name.startswith('.') and not file_name.startswith('..') or
            file_name in self.SKIP_FILES or
            '__MACOSX' in str(file_path)):
            return False, '', 'System/hidden file'
        
        # Skip explicitly unsupported extensions
        if extension in self.SKIP_EXTENSIONS:
            return False, '', 'Unsupported file type'
        
        # Skip empty files
        try:
            if file_path.stat().st_size == 0:
                return False, '', 'Empty file'
        except (OSError, FileNotFoundError):
            return False, '', 'Cannot access file'
        
        # Determine category
        if extension in self.TEXTUAL_EXTENSIONS:
            category = 'textual'
        elif extension in self.VISUAL_EXTENSIONS:
            category = 'visual'
        elif extension in self.MIXED_EXTENSIONS:
            category = 'mixed'
        elif extension in self.ARCHIVE_EXTENSIONS:
            category = 'archive'
        else:
            # Try to determine if unknown file is text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1024)
                    if len(content) > 0 and sum(c.isprintable() or c.isspace() for c in content) / len(content) > 0.8:
                        category = 'textual'
                    else:
                        return False, '', 'Unknown binary file type'
            except (UnicodeDecodeError, PermissionError):
                return False, '', 'Unknown binary file type'
        
        # Check size limits
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        limit_mb = self.size_limits.get(category, 100)
        
        if file_size_mb > limit_mb:
            return False, '', f'File too large ({file_size_mb:.1f}MB > {limit_mb}MB)'
        
        return True, category, ''

    def kill_hanging_processes(self):
        """Kill any hanging conversion processes."""
        try:
            # Kill hanging pandoc, jupyter, libreoffice, and pdftoppm processes
            hanging_processes = ['pandoc', 'jupyter', 'libreoffice', 'pdftoppm', 'pdftotext', 'wkhtmltopdf']
            
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] in hanging_processes:
                        if time.time() - proc_info['create_time'] > 600:  # 10 minutes
                            logger.warning(f"Killing hanging process: {proc_info['name']} (PID: {proc_info['pid']})")
                            proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"Error killing hanging processes: {e}")

    def has_extractable_text(self, pdf_path: Path) -> Tuple[bool, str]:
        """Check if a PDF has extractable text content. Returns (has_text, extracted_sample)."""
        try:
            # Use pdftotext to extract text from the PDF
            result = subprocess.run([
                'pdftotext', str(pdf_path), '-'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                extracted_text = result.stdout.strip()
                cleaned_text = ' '.join(extracted_text.split())
                
                # Check if we have meaningful text content
                if len(cleaned_text) >= self.min_pdf_text_length:
                    if sum(c.isalnum() or c.isspace() for c in cleaned_text) / len(cleaned_text) > 0.7:
                        return True, cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                
                return False, cleaned_text[:100] + "..." if len(cleaned_text) > 100 else cleaned_text
            else:
                logger.warning(f"pdftotext failed for {pdf_path.name}: {result.stderr}")
                return False, ""
                
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.warning(f"Error extracting text from {pdf_path.name}: {e}")
            return False, ""
    
    def extract_archives(self, file_path: Path, extract_dir: Path) -> List[Path]:
        """Extract archive files and return list of extracted files."""
        extracted_files = []
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif extension == '.rar':
                with rarfile.RarFile(file_path, 'r') as rar_ref:
                    rar_ref.extractall(extract_dir)
            elif extension in ['.tar', '.tar.gz', '.tar.bz2']:
                import tarfile
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
            elif extension == '.7z':
                # Use 7z command line tool
                subprocess.run(['7z', 'x', str(file_path), f'-o{extract_dir}'], 
                             check=True, capture_output=True)
            elif extension == '.gz' and not file_path.name.endswith('.tar.gz'):
                # Handle standalone .gz files
                import gzip
                output_file = extract_dir / file_path.stem
                with gzip.open(file_path, 'rb') as f_in:
                    with open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                extracted_files.append(output_file)
                return extracted_files
            
            # Find all extracted files
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    extracted_files.append(Path(root) / file)
            
            logger.info(f"Extracted {len(extracted_files)} files from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to extract {file_path}: {e}")
        
        return extracted_files
    
    def convert_to_pdf(self, file_path: Path, output_dir: Path) -> Tuple[Optional[Path], Optional[str]]:
        """Convert various file formats to PDF. Returns (pdf_path, error_message)."""
        extension = file_path.suffix.lower()
        
        # Create output filename
        if extension == '.pdf':
            output_path = output_dir / f"{file_path.stem}.pdf"
        else:
            # Remove the dot from extension for the suffix
            ext_suffix = extension[1:] if extension.startswith('.') else extension
            output_path = output_dir / f"{file_path.stem}_from_{ext_suffix}.pdf"
        
        try:
            if extension == '.ipynb':
                # Method 1: Direct conversion to PDF
                try:
                    subprocess.run([
                        'jupyter', 'nbconvert', '--to', 'pdf',
                        '--output-dir', str(output_dir),
                        '--output', file_path.stem,
                        str(file_path)
                    ], check=True, capture_output=True, text=True, timeout=300)
                    
                    if output_path.exists():
                        logger.info(f"Successfully converted {file_path.name} to PDF (direct)")
                        return output_path, None
                        
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    logger.warning(f"Direct PDF conversion failed for {file_path.name}: {e}")
                
                # Method 2: Fallback via HTML
                try:
                    html_path = output_dir / f"{file_path.stem}.html"
                    
                    # Convert to HTML
                    subprocess.run([
                        'jupyter', 'nbconvert', '--to', 'html',
                        '--output-dir', str(output_dir),
                        '--output', file_path.stem,
                        str(file_path)
                    ], check=True, capture_output=True, text=True, timeout=300)
                    
                    # Convert HTML to PDF
                    subprocess.run([
                        'pandoc', str(html_path), '-o', str(output_path),
                        '--pdf-engine=wkhtmltopdf'
                    ], check=True, capture_output=True, text=True, timeout=300)
                    
                    # Clean up HTML
                    html_path.unlink(missing_ok=True)
                    
                    if output_path.exists():
                        logger.info(f"Successfully converted {file_path.name} to PDF (via HTML)")
                        return output_path, None
                        
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    logger.warning(f"HTML fallback conversion failed for {file_path.name}: {e}")
                    # Clean up any partial files
                    if 'html_path' in locals():
                        html_path.unlink(missing_ok=True)
                
                # If both methods fail, it's a failed file
                return None, "Jupyter notebook conversion failed (both direct PDF and HTML→PDF methods failed)"
                
            elif extension in ['.docx', '.doc', '.odt', '.rtf', '.pptx', '.ppt']:
                # Use LibreOffice for conversion
                subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', str(output_dir), str(file_path)
                ], check=True, capture_output=True, timeout=300)
                
                # LibreOffice creates PDF with just the stem name, rename to expected format
                libreoffice_output = output_dir / f"{file_path.stem}.pdf"
                if libreoffice_output.exists() and libreoffice_output != output_path:
                    libreoffice_output.rename(output_path)
                
            elif extension == '.html':
                # Convert HTML to PDF using pandoc
                subprocess.run([
                    'pandoc', str(file_path), '-o', str(output_path),
                    '--pdf-engine=wkhtmltopdf'
                ], check=True, capture_output=True, timeout=300)
            
            elif extension == '.pdf':
                # Already a PDF, just copy it
                shutil.copy2(file_path, output_path)
            
            if output_path.exists():
                logger.info(f"Successfully converted {file_path.name} to PDF")
                return output_path, None
            else:
                return None, f"PDF conversion failed - output file not created for {extension} file"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            if isinstance(e, subprocess.TimeoutExpired):
                error_msg = f"Conversion timeout ({extension} → PDF)"
            else:
                error_msg = f"Conversion command failed ({extension} → PDF): {str(e)[:100]}"
            logger.error(f"{error_msg} for {file_path}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected conversion error ({extension} → PDF): {str(e)[:100]}"
            logger.error(f"{error_msg} for {file_path}")
            return None, error_msg
    
    def convert_to_images(self, file_path: Path, output_dir: Path) -> Tuple[List[Path], Optional[str]]:
        """Convert files to images for visual analysis. Returns (image_paths, error_message)."""
        extension = file_path.suffix.lower()
        image_paths = []
        
        try:
            if extension in self.VISUAL_EXTENSIONS:
                output_path = output_dir / file_path.name
                
                # Resize image if needed
                with Image.open(file_path) as img:
                    width, height = img.size
                    max_dim = max(width, height)
                    
                    if max_dim > self.max_image_resolution:
                        ratio = self.max_image_resolution / max_dim
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        resized_img.save(output_path, optimize=True, quality=85)
                        logger.info(f"Resized image {file_path.name} from {width}x{height} to {new_width}x{new_height}")
                    else:
                        shutil.copy2(file_path, output_path)
                
                image_paths.append(output_path)
                
            elif extension == '.pdf':
                # Get page count and limit
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    total_pages = len(pdf_reader.pages)
                    pages_to_process = min(total_pages, self.max_pdf_pages)
                
                if total_pages > self.max_pdf_pages:
                    logger.warning(f"PDF {file_path.name} has {total_pages} pages, limiting to first {self.max_pdf_pages}")
                
                # Convert PDF pages to images
                subprocess.run([
                    'pdftoppm', '-jpeg', '-r', str(self.pdf_dpi),
                    '-l', str(pages_to_process),
                    '-jpegopt', 'quality=85',
                    str(file_path), str(output_dir / 'page')
                ], check=True, capture_output=True, timeout=300)
                
                # Rename and resize generated images
                for img_file in sorted(output_dir.glob('page-*.jpg')):
                    page_num = img_file.stem.split('-')[-1]
                    new_name = output_dir / f"{file_path.stem}_page_{page_num}.jpg"
                    img_file.rename(new_name)
                    
                    # Resize if needed
                    with Image.open(new_name) as img:
                        width, height = img.size
                        max_dim = max(width, height)
                        
                        if max_dim > self.max_image_resolution:
                            ratio = self.max_image_resolution / max_dim
                            new_width = int(width * ratio)
                            new_height = int(height * ratio)
                            
                            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            resized_img.save(new_name, 'JPEG', optimize=True, quality=85)
                    
                    image_paths.append(new_name)
                    
            elif extension in self.MIXED_EXTENSIONS:
                # Convert to PDF first, then to images
                with tempfile.TemporaryDirectory() as temp_pdf_dir:
                    temp_pdf_dir_path = Path(temp_pdf_dir)
                    pdf_path, pdf_error = self.convert_to_pdf(file_path, temp_pdf_dir_path)
                    if pdf_path:
                        # Convert the temporary PDF to images in the visual directory
                        temp_images, img_error = self.convert_to_images(pdf_path, output_dir)
                        image_paths.extend(temp_images)
                    else:
                        return [], f"Image extraction failed: {pdf_error}"
            
            logger.info(f"Generated {len(image_paths)} images from {file_path.name}")
            return image_paths, None
            
        except Exception as e:
            error_msg = f"Image conversion failed ({extension}): {str(e)[:100]}"
            logger.error(f"{error_msg} for {file_path.name}")
            return [], error_msg
    
    def flatten_directory(self, source_dir: Path, target_dir: Path) -> List[Path]:
        """Recursively flatten directory structure and extract archives."""
        all_files = []
        
        for item in source_dir.rglob('*'):
            if item.is_file() and 'processed' not in item.parts:
                should_process, category, skip_reason = self.should_process_file(item)
                
                if not should_process:
                    if skip_reason not in ['System/hidden file', 'Empty file']:
                        logger.info(f"Skipping {item.name}: {skip_reason}")
                    continue
                
                if category == 'archive':
                    # Extract archive
                    extract_dir = target_dir / f"extracted_{item.stem}"
                    extract_dir.mkdir(exist_ok=True)
                    extracted_files = self.extract_archives(item, extract_dir)
                    
                    # Add extracted files
                    for extracted_file in extracted_files:
                        should_process_extracted, _, _ = self.should_process_file(extracted_file)
                        if should_process_extracted:
                            all_files.append(extracted_file)
                else:
                    # Copy file to target directory with unique name if needed
                    target_path = target_dir / item.name
                    counter = 1
                    while target_path.exists():
                        target_path = target_dir / f"{item.stem}_{counter}{item.suffix}"
                        counter += 1
                    
                    shutil.copy2(item, target_path)
                    all_files.append(target_path)
        
        return all_files
    
    def save_failed_files(self, submission_dir: Path, failed_files: List[Dict], submissions_root: Path):
        """Save failed files to a dedicated failed preprocessing folder."""
        if not failed_files:
            return
        
        failed_dir = submissions_root / "#failed_preprocessing"
        failed_dir.mkdir(exist_ok=True)
        
        submission_failed_dir = failed_dir / submission_dir.name
        submission_failed_dir.mkdir(exist_ok=True)
        
        copied_files = []
        for failed_file in failed_files:
            try:
                source_path = Path(failed_file['original_path'])
                if source_path.exists():
                    dest_path = submission_failed_dir / failed_file['filename']
                    counter = 1
                    while dest_path.exists():
                        stem = dest_path.stem
                        suffix = dest_path.suffix
                        dest_path = submission_failed_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.copy2(source_path, dest_path)
                    copied_files.append({
                        'original_file': failed_file['filename'],
                        'copied_to': str(dest_path.relative_to(submissions_root)),
                        'failure_reason': failed_file['failure_reason'],
                        'detailed_error': failed_file.get('detailed_error'),
                        'conversion_type': failed_file.get('conversion_type'),
                        'size_bytes': failed_file['size'],
                        'category': failed_file['category']
                    })
            except Exception as e:
                logger.error(f"Error saving failed file {failed_file['filename']}: {e}")
        
        if copied_files:
            report_path = submission_failed_dir / "failure_report.json"
            failure_report = {
                'submission_name': submission_dir.name,
                'processing_timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip(),
                'total_failed_files': len(copied_files),
                'failed_files': copied_files
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(failure_report, f, indent=2)
            
            logger.warning(f"Created failure report for {submission_dir.name}: {len(copied_files)} failed files")

    def process_submission_directory(self, submission_dir: Path) -> Tuple[bool, Optional[str]]:
        """Process a single submission directory. Returns (success, failure_reason)."""
        logger.info(f"Processing submission: {submission_dir.name}")
        
        # Skip if already processed
        processed_dir = submission_dir / "processed"
        if processed_dir.exists():
            logger.info(f"Skipping {submission_dir.name} - already processed")
            return True, None
        
        failed_files = []
        skipped_files = []
        scanned_pdfs = []  # Track PDFs that were processed as visual-only
        
        # Create temporary directory for flattening
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            
            # Flatten directory structure and extract archives
            all_files = self.flatten_directory(submission_dir, temp_dir)
            
            if not all_files:
                logger.warning(f"No files found in {submission_dir.name}")
                return False, "No processable files found"
            
            # Create processed subdirectories only after confirming we have files
            textual_dir = processed_dir / "textual"
            visual_dir = processed_dir / "visual"
            
            for dir_path in [processed_dir, textual_dir, visual_dir]:
                dir_path.mkdir(exist_ok=True)
            
            # Track processing results
            original_files = []
            textual_outputs = []
            visual_outputs = []
            
            # Categorize and process files
            for file_path in all_files:
                should_process, category, skip_reason = self.should_process_file(file_path)
                
                if not should_process:
                    skipped_files.append({
                        'filename': file_path.name,
                        'size': file_path.stat().st_size,
                        'reason': skip_reason
                    })
                    continue
                
                original_files.append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'category': category
                })
                
                if category == 'textual':
                    # Copy textual files directly
                    output_path = textual_dir / file_path.name
                    shutil.copy2(file_path, output_path)
                    textual_outputs.append(str(output_path.relative_to(submission_dir)))
                    
                elif category == 'visual':
                    # Copy visual files directly
                    output_path = visual_dir / file_path.name
                    shutil.copy2(file_path, output_path)
                    visual_outputs.append(str(output_path.relative_to(submission_dir)))
                    
                elif category == 'mixed':
                    # Handle PDFs specially - check for extractable text
                    if file_path.suffix.lower() == '.pdf':
                        has_text, text_sample = self.has_extractable_text(file_path)
                        
                        if has_text:
                            # Process for textual
                            pdf_file, pdf_error = self.convert_to_pdf(file_path, textual_dir)
                            if pdf_file:
                                textual_outputs.append(str(pdf_file.relative_to(submission_dir)))
                            else:
                                # PDF conversion failed, track this file
                                failed_files.append({
                                    'original_path': str(file_path),
                                    'filename': file_path.name,
                                    'size': file_path.stat().st_size,
                                    'category': category,
                                    'failure_reason': f'PDF conversion failed: {pdf_error}',
                                    'conversion_type': 'PDF'
                                })
                        else:
                            # Scanned PDF - skip textual processing
                            scanned_pdfs.append({
                                'filename': file_path.name,
                                'size': file_path.stat().st_size,
                                'text_sample': text_sample[:100] if text_sample else "No text found"
                            })
                    else:
                        # Non-PDF mixed file - process for textual
                        pdf_file, pdf_error = self.convert_to_pdf(file_path, textual_dir)
                        if pdf_file:
                            textual_outputs.append(str(pdf_file.relative_to(submission_dir)))
                        else:
                            # PDF conversion failed, track this file
                            failed_files.append({
                                'original_path': str(file_path),
                                'filename': file_path.name,
                                'size': file_path.stat().st_size,
                                'category': category,
                                'failure_reason': f'PDF conversion failed: {pdf_error}',
                                'conversion_type': 'PDF'
                            })
                    
                    # Always convert to images for visual analysis
                    images, img_error = self.convert_to_images(file_path, visual_dir)
                    if images:
                        for img in images:
                            visual_outputs.append(str(img.relative_to(submission_dir)))
                    else:
                        failed_files.append({
                            'original_path': str(file_path),
                            'filename': file_path.name,
                            'size': file_path.stat().st_size,
                            'category': category,
                            'failure_reason': f'Image conversion failed: {img_error}',
                            'conversion_type': 'Image'
                        })
            
            # Create preprocessing info
            preprocess_info = {
                'submission_name': submission_dir.name,
                'processing_timestamp': str(subprocess.run(['date'], capture_output=True, text=True).stdout.strip()),
                'original_files': original_files,
                'textual_files': textual_outputs,
                'visual_files': visual_outputs,
                'skipped_files': skipped_files,
                'scanned_pdfs': scanned_pdfs,
                'summary': {
                    'total_original_files': len(original_files),
                    'textual_outputs': len(textual_outputs),
                    'visual_outputs': len(visual_outputs),
                    'skipped_files': len(skipped_files),
                    'failed_files': len(failed_files),
                    'scanned_pdfs': len(scanned_pdfs)
                }
            }
            
            # Save preprocessing info
            info_path = processed_dir / "preprocess_info.json"
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(preprocess_info, f, indent=2)
            
            # Save failed files if any
            if failed_files:
                submissions_root = submission_dir.parent
                self.save_failed_files(submission_dir, failed_files, submissions_root)
                
                # Remove processed folder from failed submissions to allow retry
                if processed_dir.exists():
                    shutil.rmtree(processed_dir)
                    logger.info(f"Removed processed folder from {submission_dir.name} due to failures - can be retried")
                
                # Create detailed failure summary
                failure_details = {}
                for failed_file in failed_files:
                    reason = failed_file['failure_reason']
                    if reason not in failure_details:
                        failure_details[reason] = []
                    failure_details[reason].append(failed_file['filename'])
                
                # Create concise but informative failure reason
                failure_summary = []
                for reason, files in failure_details.items():
                    if len(files) == 1:
                        failure_summary.append(f"{files[0]}: {reason}")
                    else:
                        failure_summary.append(f"{len(files)} files: {reason}")
                
                failure_reason = "; ".join(failure_summary)
                logger.warning(f"Failed to process {submission_dir.name}: {failure_reason}")
                return False, failure_reason
            
            logger.info(f"Processed {submission_dir.name}: {preprocess_info['summary']}")
            return True, None
    
    def preprocess_all_submissions(self, submissions_dir: Path, workers: int = 4) -> Dict[str, bool]:
        """Preprocess all submissions in the directory using parallel processing."""
        results = {}
        failed_submissions = {}  # Track failure reasons
        
        # Get all submission directories
        submission_dirs = [d for d in submissions_dir.iterdir() 
                          if d.is_dir() and not d.name.startswith('#')]
        
        logger.info(f"Found {len(submission_dirs)} submissions to preprocess")
        
        if workers == 1:
            # Sequential processing
            for submission_dir in submission_dirs:
                try:
                    success, failure_reason = self.process_submission_directory(submission_dir)
                    results[submission_dir.name] = success
                    if not success:
                        failed_submissions[submission_dir.name] = failure_reason or "Unknown error"
                except Exception as e:
                    logger.error(f"Error processing {submission_dir.name}: {e}")
                    results[submission_dir.name] = False
                    failed_submissions[submission_dir.name] = str(e)
        else:
            # Parallel processing
            logger.info(f"Processing submissions in parallel with {workers} workers")
            
            # Kill any hanging processes before starting
            self.kill_hanging_processes()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_submission = {
                    executor.submit(self.process_submission_directory, submission_dir): submission_dir.name
                    for submission_dir in submission_dirs
                }
                
                completed_count = 0
                total_count = len(submission_dirs)
                
                try:
                    for future in concurrent.futures.as_completed(future_to_submission, timeout=600):
                        submission_name = future_to_submission[future]
                        try:
                            success, failure_reason = future.result(timeout=60)
                            results[submission_name] = success
                            completed_count += 1
                            
                            if success:
                                logger.info(f"✓ Completed ({completed_count}/{total_count}): {submission_name}")
                            else:
                                logger.warning(f"✗ Failed ({completed_count}/{total_count}): {submission_name}")
                                failed_submissions[submission_name] = failure_reason or "Unknown error"
                                
                        except concurrent.futures.TimeoutError:
                            logger.error(f"Timeout processing {submission_name} - killing hanging processes")
                            self.kill_hanging_processes()
                            results[submission_name] = False
                            failed_submissions[submission_name] = "Processing timeout"
                            completed_count += 1
                        except Exception as e:
                            logger.error(f"Error processing {submission_name}: {e}")
                            results[submission_name] = False
                            failed_submissions[submission_name] = str(e)
                            completed_count += 1
                            
                except (concurrent.futures.TimeoutError, KeyboardInterrupt):
                    logger.warning("Processing interrupted - cleaning up...")
                    self.kill_hanging_processes()
                    
                    # Cancel remaining futures
                    for future in future_to_submission:
                        if not future.done():
                            future.cancel()
                            submission_name = future_to_submission[future]
                            results[submission_name] = False
                            failed_submissions[submission_name] = "Processing cancelled"
        
        # Generate summary
        successful = sum(results.values())
        total = len(results)
        
        summary_report = {
            'total_submissions': total,
            'successful_preprocessing': successful,
            'failed_preprocessing': total - successful,
            'failed_submissions': failed_submissions  # Only include failed ones with reasons
        }
        
        # Save summary report
        summary_path = submissions_dir / "preprocessing_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, indent=2)
        
        logger.info(f"Preprocessing complete: {successful}/{total} submissions processed successfully")
        if failed_submissions:
            logger.warning(f"Failed submissions: {list(failed_submissions.keys())}")
        
        return results

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    logger.info("Received interrupt signal. Shutting down gracefully...")
    sys.exit(0)

def main():
    """Main function to run preprocessing."""
    import argparse
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(description='Preprocess student submissions')
    parser.add_argument('submissions_dir', type=Path, help='Directory containing submissions')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4, use 1 for sequential)')
    
    args = parser.parse_args()
    
    if not args.submissions_dir.exists():
        logger.error(f"Submissions directory not found: {args.submissions_dir}")
        sys.exit(1)
    
    try:
        preprocessor = SubmissionPreprocessor()
        results = preprocessor.preprocess_all_submissions(args.submissions_dir, workers=args.workers)
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(0)
    
    # Print final summary
    successful = sum(results.values())
    total = len(results)
    print(f"\nPreprocessing Summary:")
    print(f"Total submissions: {total}")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {total - successful}")
    
    if successful > 0:
        print(f"\nProcessed submissions now have:")
        print(f"- processed/textual/ folder with PDF files and text files")
        print(f"- processed/visual/ folder with image files")
        print(f"- processed/preprocess_info.json with processing details")

if __name__ == "__main__":
    main() 