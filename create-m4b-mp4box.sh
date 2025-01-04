#!/bin/bash
set -e

# Create M4B using MP4Box (force overwrite with -tmp)
MP4Box -tmp -add "./out/audiobook.aac" \
       -chap "./out/chapters.txt" \
       "./out/audiobook.m4b"

echo "M4B file created at ./out/audiobook.m4b using MP4Box" 