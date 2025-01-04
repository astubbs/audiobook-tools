#!/bin/bash
set -e

# Create M4B using FFmpeg
ffmpeg -y \
       -i "./out/audiobook.aac" \
       -i "./out/chapters.txt" \
       -map_metadata 1 \
       -c:a copy \
       -movflags +faststart \
       "./out/audiobook.m4b"

echo "M4B file created at ./out/audiobook.m4b using FFmpeg" 