# DupeX - Duplicate File Finder

A modern, fast duplicate file finder built with Python and CustomTkinter. 
It uses a multi-threaded scanning engine to find exact duplicate files and similar images, videos, and documents without freezing the UI.

## Features
- Scans selected drives or folders for duplicates.
- Filters by file type (Images, Videos, Audio, Documents, All).
- Two-pass detection:
  - Exact match: Groups by size and checks SHA-256 hash.
  - Similar match: Uses perceptual hashing (pHash) for images to find resized/compressed versions.
- Safe deletion: Uses `send2trash` to send files to the Recycle Bin/Trash.

## Setup Instructions

1. Install Python 3.9+ 
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### Optional: ffmpeg for Video Similarity
If you want to use the video similarity features (which sample frames for perceptual hashing), you need to have `ffmpeg` installed on your system and available in your PATH.
- **Windows**: Download `ffmpeg` from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or use `winget install ffmpeg`.
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` (or your distribution's equivalent).
If `ffmpeg` is not found, the app will gracefully skip video similarity checks.
