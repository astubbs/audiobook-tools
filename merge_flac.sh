#!/bin/bash
set -e

# Check arguments
DRY_RUN=false
BASE_DIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            BASE_DIR="$1"
            shift
            ;;
    esac
done

# Check if directory argument is provided
if [ -z "$BASE_DIR" ]; then
    echo "Usage: $0 [-d|--dry-run] <audiobook_directory>"
    exit 1
fi

# Directory containing the audiobook CDs
BASE_DIR="$BASE_DIR"
OUTPUT_DIR="./out"

# Find all FLAC files and sort them numerically by CD number
echo "Finding FLAC files..."
flac_files=()
while IFS= read -r file; do
    flac_files+=("$file")
done < <(find "$BASE_DIR" -name "CD*.flac" -o -name "*CD*.flac" | sort -V)

# Verify we found files
if [ ${#flac_files[@]} -eq 0 ]; then
    echo "Error: No FLAC files found in $BASE_DIR"
    exit 1
fi

# Show what files were found and in what order
echo -e "\nFiles would be combined in this order:"
for i in "${!flac_files[@]}"; do
    echo "$((i+1)). ${flac_files[$i]}"
    duration=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${flac_files[$i]}")
    hours=$(printf "%.2f" "$(echo "$duration / 3600" | bc -l)")
    echo "   Duration: $hours hours"
done

# Show total number of files
echo -e "\nTotal files to merge: ${#flac_files[@]}"

if [ "$DRY_RUN" = true ]; then
    echo -e "\nDry run complete. No files were merged."
    exit 0
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Clear any existing combined file
rm -f "$OUTPUT_DIR/combined.flac"

# Merge FLAC files using sox
echo -e "\nMerging FLAC files..."
sox --show-progress "${flac_files[@]}" "$OUTPUT_DIR/combined.flac"

echo "Combined FLAC file created: $OUTPUT_DIR/combined.flac"

# Verify the output
duration=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_DIR/combined.flac")
hours=$(printf "%.2f" "$(echo "$duration / 3600" | bc -l)")
echo "Combined file duration: $hours hours"