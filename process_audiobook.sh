#!/bin/bash

confirm() {
    read -p "$1 [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            echo "Skipping..."
            false
            ;;
    esac
}

echo "Audio Book Processing Script"
echo "---------------------------"

if confirm "Step 1: Merge FLAC files?"; then
    ./merge_flac.sh
fi

if confirm "Step 2: Generate combined CUE file?"; then
    python combine_cue.py
fi

if confirm "Step 3: Generate chapter metadata?"; then
    python cue-to-mp4b.py
fi

if confirm "Step 4: Create M4B file?"; then
    MP4Box -add "./out/combined.flac" -chap "./out/chapters.txt" "./out/audiobook.m4b"
fi

if confirm "Step 5: Update chapters only? (if needed)"; then
    MP4Box -chap "./out/chapters.txt" "./out/audiobook.m4b"
fi

echo "Done!" 