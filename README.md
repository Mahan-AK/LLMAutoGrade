# LLMAutoGrade

An automated grading system for student submissions using Google's Gemini Large Language Models. The system processes various file formats, extracts content, and provides intelligent grading with cost tracking and comprehensive reporting.

## Project Structure

```
LLMAutoGrade/
├── README.md                    # This file
├── requirements.txt             # All Python dependencies (merged)
├── grade.sh                     # Main entry point script
├── .gitignore                   # Git ignore rules
│
├── scripts/                     # Core processing scripts
│   ├── process_submissions.py   # Main submission processing and grading
│   ├── parse_solution.py        # Solution parsing and processing
│   ├── preprocess_submissions.py # Submission preprocessing pipeline
│   ├── prompts.py              # LLM prompts and instructions
│   └── utils.py                # Utility functions (cost calculation)
│
├── Model_Solutions/             # Reference solutions (processed)
│   ├── Assignment_0/
│   ├── Assignment_1/
│   └── .../
│
├── Submissions/                 # Student submissions
│   ├── Assignment_0/
│   ├── Assignment_1/
│   └── .../
│
├── logs/                        # Log files
└── .venv/                       # Python virtual environment
```

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd LLMAutoGrade

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Setup System Dependencies

**IMPORTANT: Preprocessing is designed for Linux systems and requires specific system packages.**

```bash
# Install required system packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install poppler-utils libreoffice pandoc p7zip-full unrar wkhtmltopdf
```

**Required System Packages:**
- **poppler-utils**: PDF processing (`pdftoppm`, `pdftotext`)
- **libreoffice**: Office document conversion (DOCX, PPTX, ODT)
- **pandoc**: Document format conversion
- **wkhtmltopdf**: HTML to PDF conversion
- **p7zip-full**: 7Z archive extraction
- **unrar**: RAR archive extraction

**Installation Commands:**
- **Ubuntu/Debian**: `sudo apt install poppler-utils libreoffice pandoc wkhtmltopdf p7zip-full unrar`
- **CentOS/RHEL/Fedora**: `sudo dnf install poppler-utils libreoffice pandoc wkhtmltopdf p7zip unrar`

### 3. Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Set it as an environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

## Workflow Overview

The LLMAutoGrade system follows a specific workflow that requires two input files for each assignment:

### **Input Files Required:**

1. **Model Solution PDF** (`Assignment_X_Solution.pdf`)
   - Contains the complete solution to the assignment
   - Can be a concatenation of different document types
   - Structure doesn't need to be strictly unified
   - Must be in PDF format

2. **Structure Hint File** (`structure_hint_assignment_X.txt`)
   - Defines the assignment structure and grading points
   - Maps every gradable unit to its point value
   - Allows you to override/modify points from the PDF
   - Essential for consistent grading

### **Complete Workflow:**

```
1. Prepare Input Files
   ├── Model Solution PDF
   └── Structure Hint File
   
2. Process Solution
   ├── Extract text and images from PDF
   ├── Parse and structure using Gemini
   └── Create grading reference
   
3. Grade Submissions
   ├── Preprocess student submissions
   ├── Grade against processed solution
   └── Generate detailed reports
```

## Usage

The system has two main operations, both accessible through the `grade.sh` script:

### Process Solutions

First, process your model solutions to create the grading reference:

```bash
./grade.sh solution 0 Assignment_0_Solution.pdf structure_hint_assignment_0.txt Model_Solutions/Assignment_0/ $GEMINI_API_KEY
```

**What this does:**
- Extracts text and images from the solution PDF
- Parses and structures the solution using Gemini
- Creates `processed_solution_info.json` for grading
- Generates page images for visual analysis
- Produces structured markdown with proper formatting

**Output files created:**
- `processed_solution_info.json` - Metadata for grading system
- `parsed_solution_X.md` - Structured solution with proper formatting
- `extracted_solution_text.md` - Raw extracted text from PDF
- `solution_text.txt` - Plain text version
- `pages/` - Directory with page images for visual analysis

## Structure Hint Files

The structure hint file is crucial for defining how assignments are graded. It maps every gradable unit to its point value and ensures consistent grading across all submissions.

### **Structure Format:**

The file uses a hierarchical structure with indentation to define exercises, parts, and sub-parts:

```
Exercise X.Y:
i) [N points]
ii) [N points]
   a) [N points]
   b) [N points]
iii) [N points]
   a) [N points]
   b) [N points]
   c) [N points]
```

### **Examples:**

**Assignment 0:**
```
Exercise 0.1:
i)
a) 2 points
b) 2 points
c) 2 points
ii) 2 points
Exercise 0.2:
i) 2 points
ii) 2 points
iii) 2 points
iv) 2 points
```

**Assignment 1 (with null points):**
```
Exercise 1.1:
i) 3 points
ii) 4 points
iii) 1 point
Exercise 1.2:
i)
a) 1 point
b) 1 point
c) 2 points
ii)
a) 1 point
b) 1 point
c) 2 points
iii)
a) 1 point
b) 1 point
c) 0 points
Exercise 1.3:
0 points
```

### Grade Submissions

Then grade student submissions (includes preprocessing):

```bash
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY
```

**What this does:**
1. **Preprocess** submissions (extract archives, convert formats, organize content)
2. **Grade** submissions using the processed solution
3. **Generate** detailed reports and cost tracking

### **Grading Script Usage and Options**

The grading script (`process_submissions.py`) supports various options for customization:

#### **Basic Grading Command:**
```bash
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY
```

#### **Advanced Grading Options:**
```bash
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY \
    --model_type pro \
    --parallel 4 \
    --retry_count 3
```

#### **Available Options:**

| Option | Description | Default | Values |
|--------|-------------|---------|---------|
| `--model_type` | Gemini model to use | `pro` | `pro`, `flash` |
| `--parallel` | Concurrent submissions | `1` | `0` (auto), `1-10` |
| `--retry_count` | API retry attempts | `3` | `1-10` |
| `--regrade` | Skip parsing, only regrade | `false` | Flag (no value) |

#### **Model Types:**
- **`pro`**: Gemini 2.5 Pro - Higher quality, more expensive
- **`flash`**: Gemini 2.5 Flash - Faster, more cost-effective

#### **Parallel Processing:**
- **`--parallel 1`**: Sequential processing (default)
- **`--parallel 4`**: Process 4 submissions simultaneously
- **`--parallel 0`**: Auto-detect optimal number (capped at 4)

#### **Regrading Mode:**
```bash
# Only regrade existing submissions (skip preprocessing and parsing)
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY --regrade
```

**Useful for:**
- Adjusting grading criteria
- Fixing grading errors
- Recalculating scores
- Cost optimization (avoids re-parsing)

### **Practical Grading Examples:**

#### **Example 1: Basic Grading**
```bash
# Grade all submissions in Assignment 0
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY
```

#### **Example 2: Cost-Optimized Grading**
```bash
# Use Flash model for faster, cheaper processing
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY \
    --model_type flash \
    --parallel 2
```

#### **Example 3: High-Throughput Grading**
```bash
# Use Pro model with maximum parallel processing
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY \
    --model_type pro \
    --parallel 4 \
    --retry_count 5
```

#### **Example 4: Regrading Only**
```bash
# Regrade existing submissions (skip preprocessing)
./grade.sh grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ $GEMINI_API_KEY \
    --regrade \
    --model_type pro
```

## How It Works

### Stage 1: Solution Processing
- **PDF parsing**: Extracts text and creates page images using `pdftoppm` and `pdftotext`
- **LLM enhancement**: Uses Gemini Pro to improve parsed content and structure
- **Structure analysis**: Creates grading reference with point allocations from structure hint
- **Output generation**: Produces structured markdown and metadata files

### Stage 2: Preprocessing (for submissions)
- **Archive extraction**: ZIP, RAR, 7Z, TAR files
- **Format conversion**: DOCX, PPTX, IPYNB → PDF → Images
- **Content organization**: Separates textual and visual content
- **File validation**: Checks file sizes and formats

### Stage 3: Grading
- **Content analysis**: Processes preprocessed submissions
- **LLM grading**: Uses Gemini to compare with processed model solution
- **Point allocation**: Assigns scores based on structural hints
- **Cost tracking**: Monitors API usage and expenses

### **What Happens During Grading:**

1. **Submission Processing:**
   - Each student submission is processed individually
   - Preprocessed files are uploaded to Gemini API
   - LLM analyzes the submission content

2. **Solution Comparison:**
   - Submission is compared against the processed model solution
   - LLM evaluates each gradable unit from the structure hint
   - Points are assigned based on completeness and correctness

3. **Output Generation:**
   - **`grading_report.md`**: Detailed human-readable grading report
   - **`grading_result.json`**: Structured results for automated processing
   - **`grading_metadata.json`**: Cost, timing, and API usage data

4. **Error Handling:**
   - Failed submissions are logged and reported
   - Invalid submissions are moved to `#invalid_submissions/` folder
   - Comprehensive error reporting for debugging

### **What the Preprocessing Handles**

The preprocessing stage automatically converts **any file format** into LLM-compatible formats:

**Archive Files:**
- **ZIP, RAR, 7Z, TAR** → Automatically extracted and flattened
- **Nested archives** → Recursively extracted
- **Password-protected** → Handled when possible

**Document Formats:**
- **Word documents** (DOCX, DOC) → PDF + Images
- **PowerPoint** (PPTX, PPT) → PDF + Images  
- **Jupyter notebooks** (IPYNB) → PDF + Images
- **HTML files** → PDF + Images
- **Markdown** (MD) → PDF + Images
- **LaTeX** (TEX) → PDF + Images
- **OpenDocument** (ODT, RTF) → PDF + Images

**Image Formats:**
- **All image types** → Optimized JPG/PNG for LLM processing
- **High-resolution images** → Automatically resized to LLM limits
- **Multiple formats** → Standardized for consistency

**Code Files:**
- **Python, Java, C++** → Preserved as text
- **SQL, R, MATLAB** → Preserved as text
- **Configuration files** → Preserved as text

### **Preprocessing Output Structure**
After preprocessing, each submission gets a standardized structure:

```
Student_Name_12345/processed/
├── textual/                           # All text-based content
│   ├── assignment.pdf                 # Original PDF (if applicable)
│   ├── code.py                        # Code files
│   ├── extracted_text.txt             # Extracted text from documents
│   └── ...
├── visual/                            # All visual content
│   ├── page_1.jpg                     # Document pages as images
│   ├── page_2.jpg
│   ├── plot1.jpg                      # Original images
│   └── ...
└── preprocess_info.json               # Processing metadata
```

## 📁 File Format Support

### Input Formats
- **Documents**: PDF, DOCX, PPTX, IPYNB, HTML, RTF, ODT
- **Code**: Python, Java, C++, JavaScript, SQL, R, MATLAB
- **Text**: TXT, MD, JSON, CSV, XML, YAML, TEX
- **Images**: JPG, PNG, GIF, BMP, TIFF, SVG, WebP
- **Archives**: ZIP, RAR, 7Z, TAR, GZ

### Output Structure
```
submission_name/
├── processed/
│   ├── textual/          # Extracted text files
│   ├── visual/           # Generated images
│   └── preprocess_info.json
├── parsed_submission.md  # LLM-parsed content
├── grading_report.md     # Detailed grading report
├── grading_result.json   # Structured grading results
└── grading_metadata.json # Cost and processing metrics
```

## Cost Management

The system tracks API costs for both solution processing and grading:

- **Gemini Pro**: $1.25/1M input tokens, $10.00/1M output tokens
- **Gemini Flash**: $0.15/1M input tokens, $0.60/1M output tokens
- **Cost metadata** saved in `grading_metadata.json` for each submission

## Reports and Outputs

### Processing Reports
- **Location**: `#processing_reports/` folder
- **Content**: Success/failure summary for all submissions
- **Timing**: Generated with timestamps

### Grading Results
- **Individual**: `grading_result.json` in each submission folder
- **Summary**: `#processing_reports/` with overall statistics
- **Logs**: `submissions_processing.log` for debugging

### Invalid Submissions
- **Location**: `#invalid_submissions/` folder
- **Reports**: Individual failure reports and summary
- **Common issues**: Missing preprocessing, file format errors

## Dependencies

### Platform Compatibility

The preprocessing stage requires Linux-specific system tools for file conversion and archive extraction.

### Python Packages
```
google-generativeai>=0.3.0  # Gemini API
PyPDF2>=3.0.0              # PDF processing
Pillow>=9.0.0              # Image processing
psutil>=5.8.0              # Process management
rarfile>=4.0               # RAR archive support
jupyter>=1.0.0             # Notebook processing
nbconvert>=6.0.0           # Notebook conversion
requests                   # HTTP requests
pathlib                    # Path utilities
typing-extensions          # Type hints
```

### System Requirements

**System Packages:**
- **poppler-utils**: PDF processing (`pdftoppm`, `pdftotext`)
- **libreoffice**: Office document conversion (DOCX, PPTX, ODT, RTF)
- **pandoc**: Document format conversion (HTML, Markdown, etc.)
- **wkhtmltopdf**: HTML to PDF conversion
- **p7zip-full**: 7Z archive extraction
- **unrar**: RAR archive extraction
- **unzip/tar/gzip**: Standard archive formats

**Cross-Platform Requirements:**
- **Python 3.8+**: Required for all operations
- **Virtual Environment**: Recommended for dependency management


### Log Files
- **Main processing**: `submissions_processing.log`
- **Preprocessing**: `preprocessing.log`
- **Individual submissions**: Check submission folders for errors

## Performance Tips

- **Use Flash model** for cost-sensitive operations
- **Adjust parallel processing** based on API quota
- **Monitor costs** with `grading_metadata.json`
- **Batch process** assignments together
