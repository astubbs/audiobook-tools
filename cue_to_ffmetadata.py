import re

# Input and output files
cue_file = "combined.cue"
ffmetadata_file = "chapters.ffmetadata"

# Helper function to convert CUE time (MM:SS:FF) to milliseconds
def cue_time_to_milliseconds(cue_time):
    minutes, seconds, frames = map(int, cue_time.split(":"))
    total_seconds = minutes * 60 + seconds + frames / 75  # Convert frames to seconds
    return int(total_seconds * 1000)  # Convert seconds to milliseconds

# Parse the CUE file
with open(cue_file, "r", encoding="utf-8") as f:
    cue_lines = f.readlines()

chapters = []
current_chapter = None

print("Starting CUE file parsing...")

for line in cue_lines:
    # Match TRACK lines to prepare for a new chapter
    if re.match(r"^\s*TRACK\s+\d+\s+AUDIO", line):
        if current_chapter is not None:
            chapters.append(current_chapter)
        current_chapter = {"START": None, "TITLE": None}
        print("New chapter initialized.")

    # Match TITLE lines to set the chapter title
    elif "TITLE" in line and current_chapter is not None:
        title_match = re.search(r'TITLE "(.*)"', line)
        if title_match:
            current_chapter["TITLE"] = title_match.group(1)
            print(f"Set chapter title: {current_chapter['TITLE']}")

    # Match INDEX 01 lines to set the chapter start time
    elif "INDEX 01" in line and current_chapter is not None:
        time_match = re.search(r"INDEX 01 (\d+:\d+:\d+)", line)
        if time_match:
            current_chapter["START"] = cue_time_to_milliseconds(time_match.group(1))
            print(f"Set chapter start time: {current_chapter['START']} ms")

# Add the last chapter if it exists
if current_chapter is not None:
    chapters.append(current_chapter)

# Set the END time for all chapters except the last
print("Setting end times for chapters...")
for i in range(len(chapters) - 1):
    chapters[i]["END"] = chapters[i + 1]["START"]
    print(f"Chapter {i+1}: START={chapters[i]['START']} ms, END={chapters[i]['END']} ms")

# Set the END time for the last chapter (arbitrary buffer added)
if len(chapters) > 0:
    chapters[-1]["END"] = chapters[-1]["START"] + 10000  # Add 10 seconds buffer
    print(f"Last chapter: START={chapters[-1]['START']} ms, END={chapters[-1]['END']} ms")

# Write the FFmetadata file
print(f"Writing FFmetadata file to {ffmetadata_file}...")
with open(ffmetadata_file, "w", encoding="utf-8") as f:
    f.write(";FFMETADATA1\n")
    for chapter in chapters:
        if chapter["TITLE"] and chapter["START"] is not None and chapter["END"] is not None:
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={chapter['START']}\n")
            f.write(f"END={chapter['END']}\n")
            f.write(f"title={chapter['TITLE']}\n\n")
            print(f"Written chapter: {chapter['TITLE']} (START={chapter['START']} ms, END={chapter['END']} ms)")

print(f"FFmetadata file created: {ffmetadata_file}")