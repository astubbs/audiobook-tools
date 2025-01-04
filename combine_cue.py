import os
import re
import subprocess
import json
import sys

# Parent directory containing subdirectories with .cue files
if "pytest" in sys.modules or "unittest" in sys.modules:
    BASE_DIR = "./tests/test_data/Eckhart Tolle - A New Earth"
else:
    BASE_DIR = "./Eckhart Tolle - A New Earth (Eckhart Tolle) - 2005 (FLAC, 278 kbps)"

OUTPUT_DIR = "./out"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "combined.cue")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize variables
track_number = 1
combined_cue_content = []

# Helper function to parse time strings
def time_to_seconds(time_str):
    """Convert a time string in MM:SS:FF format to seconds.
    
    Args:
        time_str: String in format "MM:SS:FF" where FF is frames (75 frames per second)
    
    Returns:
        Float representing the time in seconds
    """
    minutes, seconds, frames = map(int, time_str.split(":"))
    return minutes * 60 + seconds + frames / 75.0

def seconds_to_time(seconds):
    """Convert seconds to a time string in MM:SS:FF format.
    
    Args:
        seconds: Float representing time in seconds
    
    Returns:
        String in format "MM:SS:FF" where FF is frames (75 frames per second)
    """
    total_frames = round(seconds * 75)  # Convert to frames, rounding to nearest frame
    minutes = total_frames // (75 * 60)
    remaining_frames = total_frames % (75 * 60)
    seconds = remaining_frames // 75
    frames = remaining_frames % 75
    return f"{minutes:02d}:{seconds:02d}:{frames:02d}"

# Sort function for numeric sorting of CD files
def cd_sort_key(filename):
    # Extract the number from CD1, CD2, etc.
    match = re.search(r'CD(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def get_audio_length(audio_file_path):
    """Get the duration of an audio file in seconds using ffprobe.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Float representing the duration in seconds
        
    Raises:
        subprocess.CalledProcessError: If ffprobe fails to read the file
        json.JSONDecodeError: If ffprobe output is not valid JSON
        KeyError: If duration field is not found in ffprobe output
    """
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        str(audio_file_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

# Recursive function to calculate cumulative duration
def calculate_cumulative_duration(cue_files, index):
    """Calculate the start time for a given CD index by summing durations of previous CDs.
    
    Args:
        cue_files: List of paths to .cue files
        index: Index of the current CD (0-based)
    
    Returns:
        Float representing the start time in seconds for the current CD
    """
    if index == 0:
        return 0.0  # First CD always starts at 0
        
    # Get the audio file path from the previous CD's cue file
    previous_cue_path = cue_files[index - 1]
    with open(previous_cue_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the audio file name from the FILE directive
    audio_file_match = re.search(r'FILE\s+"([^"]+)"', content)
    if not audio_file_match:
        raise ValueError(f"No FILE directive found in {previous_cue_path}")
    
    # Construct the audio file path (in same directory as cue file)
    audio_file = os.path.join(os.path.dirname(previous_cue_path), audio_file_match.group(1))
    
    # Get the duration of the previous CD
    previous_cd_duration = get_audio_length(audio_file)
    
    # Add the duration of all previous CDs
    if index > 1:
        previous_cd_duration += calculate_cumulative_duration(cue_files, index - 1)
        
    return previous_cd_duration

# Process all .cue files in subdirectories, sorted by the CD number
cue_files = []
for root, dirs, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".cue"):
            cue_files.append(os.path.join(root, file))

# Sort the cue files based on the CD number
cue_files.sort(key=lambda x: cd_sort_key(x))

# Process each sorted .cue file
for i, cue_path in enumerate(cue_files):
    print(f"=== Processing: {cue_path} ===")
    with open(cue_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cumulative_duration = calculate_cumulative_duration(cue_files, i)

    # Track the current file and parse its tracks
    current_file = None
    for line in lines:
        # Check for the FILE directive
        if line.strip().startswith("FILE"):
            current_file = line.strip()
            combined_cue_content.append(current_file)
            print(f"Added FILE: {current_file}")
        
        # Check for the TRACK directive
        elif line.strip().startswith("TRACK"):
            combined_cue_content.append(f"  TRACK {track_number:02d} AUDIO")
            print(f"Added TRACK {track_number}")
            track_number += 1

        # Check for the TITLE directive
        elif line.strip().startswith("TITLE"):
            title_line = line.strip()
            if "CD" not in title_line:  # Skip "CD" chapters
                combined_cue_content.append(f"    {title_line}")
                print(f"Added TITLE: {title_line}")

        # Check for the PERFORMER directive
        elif line.strip().startswith("PERFORMER"):
            combined_cue_content.append(f"    {line.strip()}")
            print(f"Added PERFORMER: {line.strip()}")

        # Check for the INDEX directive
        elif line.strip().startswith("INDEX"):
            match = re.search(r"INDEX (\d+) (\d{2}:\d{2}:\d{2})", line)
            if match:
                index_number = match.group(1)
                index_time = match.group(2)
                index_time_seconds = time_to_seconds(index_time)
                cumulative_time = cumulative_duration + index_time_seconds
                combined_cue_content.append(
                    f"    INDEX {index_number} {seconds_to_time(cumulative_time)}"
                )
                print(f"Added INDEX {index_number}: {index_time} -> {seconds_to_time(cumulative_time)}")

# Write the combined cue file
if combined_cue_content:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(combined_cue_content))
    print(f"Combined .cue file created: {OUTPUT_FILE}")
else:
    print("No valid tracks were found across all .cue files. Combined file not created.")