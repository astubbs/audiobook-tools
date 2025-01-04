import re
import os
import subprocess
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Create M4B audiobook with chapters from CUE file')
    parser.add_argument('--input-aac', help='Input AAC file (if not provided, will use FLAC)')
    return parser.parse_args()

# Input and output files
OUTPUT_DIR = "./out"
cue_file = os.path.join(OUTPUT_DIR, "combined.cue")
ffmpeg_chapters_file = os.path.join(OUTPUT_DIR, "chapters.txt")

def get_audio_duration_ms(audio_file):
    """Get the duration of the audio file in milliseconds"""
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_file]
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

def main():
    args = parse_args()
    
    # Determine input audio file
    if args.input_aac:
        input_audio = args.input_aac
        use_aac = True
    else:
        input_audio = os.path.join(OUTPUT_DIR, "combined.flac")
        use_aac = False

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

    # Get audio duration for the last chapter's end time
    duration_ms = get_audio_duration_ms(input_audio)

    # Write the chapters file in FFmpeg metadata format
    print(f"\nWriting chapters file: {ffmpeg_chapters_file}")
    with open(ffmpeg_chapters_file, "w", encoding="utf-8") as f:
        # Write FFmpeg metadata header
        f.write(";FFMETADATA1\n\n")
        
        # Write each chapter
        for i, (start_ms, title) in enumerate(chapters):
            # For each chapter except the last, end time is start of next chapter
            if i < len(chapters) - 1:
                end_ms = chapters[i + 1][0]
            else:
                end_ms = duration_ms
            
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={start_ms}\n")
            f.write(f"END={end_ms}\n")
            f.write(f"title={title}\n\n")

    print(f"FFmpeg chapters file created with {len(chapters)} chapters")
    print("\nNext step: Use ffmpeg to create the audiobook:")
    
    # Build ffmpeg command based on input type
    if use_aac:
        # If using AAC, just copy the stream
        print(f'ffmpeg -i "{input_audio}" -i "{ffmpeg_chapters_file}" -map_metadata 1 -c:a copy -movflags +faststart "./out/audiobook.m4b"')
    else:
        # If using FLAC, encode to AAC
        print(f'ffmpeg -i "{input_audio}" -i "{ffmpeg_chapters_file}" -map_metadata 1 -c:a aac -b:a 256k -movflags +faststart "./out/audiobook.m4b"')

if __name__ == "__main__":
    main() 