import re
import os
import subprocess

# Input and output files
OUTPUT_DIR = "./out"
cue_file = os.path.join(OUTPUT_DIR, "combined.cue")
mp4box_chapters_file = os.path.join(OUTPUT_DIR, "chapters.txt")

def get_audio_duration_ms():
    """Get the duration of the FLAC file in milliseconds"""
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', 
           os.path.join(OUTPUT_DIR, "combined.flac")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    import json
    data = json.loads(result.stdout)
    return int(float(data['format']['duration']) * 1000)

# Helper function to convert CUE time (MM:SS:FF) to milliseconds
def cue_time_to_ms(cue_time):
    minutes, seconds, frames = map(int, cue_time.split(":"))
    # In CD audio, there are exactly 75 frames per second
    total_ms = (minutes * 60 + seconds) * 1000 + (frames * 1000 // 75)
    return total_ms

def ms_to_timestamp(ms):
    """Convert milliseconds to HH:MM:SS.mmm format for MP4Box"""
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    ms %= 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"

# Parse the CUE file
print(f"Reading CUE file: {cue_file}")
with open(cue_file, "r", encoding="utf-8") as f:
    cue_lines = f.readlines()

chapters = []
current_title = None

for line in cue_lines:
    # Match TITLE lines to get chapter titles
    if "TITLE" in line:
        title_match = re.search(r'TITLE "(.*)"', line)
        if title_match:
            current_title = title_match.group(1)
    # Match INDEX 01 lines to get chapter start times
    elif "INDEX 01" in line and current_title:
        time_match = re.search(r"INDEX 01 (\d+:\d+:\d+)", line)
        if time_match:
            start_ms = cue_time_to_ms(time_match.group(1))
            chapters.append((start_ms, current_title))

# Write the chapters file in MP4Box format
print(f"\nWriting chapters file: {mp4box_chapters_file}")
with open(mp4box_chapters_file, "w", encoding="utf-8") as f:
    # Write each chapter in HH:MM:SS.mmm format
    for start_ms, title in chapters:
        timestamp = ms_to_timestamp(start_ms)
        f.write(f"{timestamp} {title}\n")

print(f"MP4Box chapters file created with {len(chapters)} chapters")
print("\nNext step: Use MP4Box to create the audiobook:")
print(f'MP4Box -add "./out/combined.flac" -chap "{mp4box_chapters_file}" "./out/audiobook.m4b"')