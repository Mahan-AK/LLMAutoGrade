#!/bin/bash
# Entry point script for grading system - either process solutions or grade submissions

if [ $# -eq 0 ]; then
    echo "Usage: $0 <command> [arguments...]"
    echo ""
    echo "Commands:"
    echo "  solution <assignment_id> <solution_pdf> <structure_hint> <solution_dir> <api_key>"
    echo "    Process a solution directory"
    echo ""
    echo "  grade <submissions_dir> <solution_dir> <api_key> [options...]"
    echo "    Preprocess and grade submissions"
    echo ""
    echo "Examples:"
    echo "  $0 solution 0 Assignment_0_Solution.pdf structure_hint_assignment_0.txt Model_Solutions/Assignment_0/ YOUR_API_KEY"
    echo "  $0 grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ YOUR_API_KEY"
    echo "  $0 grade Submissions/Assignment_0/ Model_Solutions/Assignment_0/ YOUR_API_KEY --model_type pro --parallel 4"
    exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
    "solution")
        if [ $# -lt 5 ]; then
            echo "Error: solution command requires <assignment_id> <solution_pdf> <structure_hint> <solution_dir> <api_key>"
            echo "Usage: $0 solution <assignment_id> <solution_pdf> <structure_hint> <solution_dir> <api_key>"
            exit 1
        fi
        ASSIGNMENT_ID="$1"
        SOLUTION_PDF="$2"
        STRUCTURE_HINT="$3"
        SOLUTION_DIR="$4"
        API_KEY="$5"
        
        echo "Processing solution: $SOLUTION_DIR"
        
        python scripts/parse_solution.py \
            --assignment_id "$ASSIGNMENT_ID" \
            --solution_pdf "$SOLUTION_PDF" \
            --structure_hint "$STRUCTURE_HINT" \
            --api_key "$API_KEY"
        ;;
        
    "grade")
        if [ $# -lt 3 ]; then
            echo "Error: grade command requires <submissions_dir> <solution_dir> <api_key>"
            exit 1
        fi
        SUBMISSIONS_DIR="$1"
        SOLUTION_DIR="$2"
        API_KEY="$3"
        shift 3
        
        echo "Preprocessing submissions: $SUBMISSIONS_DIR"
        python scripts/preprocess_submissions.py "$SUBMISSIONS_DIR" "$@"
        
        echo "Grading submissions..."
        python scripts/process_submissions.py \
            --submissions_dir "$SUBMISSIONS_DIR" \
            --solution_dir "$SOLUTION_DIR" \
            --api_key "$API_KEY" \
            "$@"
        ;;
        
    *)
        echo "Unknown command: $COMMAND"
        echo "Use 'solution' or 'grade'"
        exit 1
        ;;
esac 