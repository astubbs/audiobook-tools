#!/bin/bash
set -e

# Create AAC from FLAC with settings optimized for spoken word
ffmpeg -y \
       -i "./out/combined.flac" \
       -c:a aac \
       -b:a 64k \
       -movflags +faststart \
       "./out/audiobook.aac"

echo "AAC file created at ./out/audiobook.aac" 