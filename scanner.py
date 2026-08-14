import os
from collections import defaultdict

# Common system directories to skip by default for safety and speed
DEFAULT_EXCLUDES = [
    'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
    'System32', 'AppData', '$Recycle.Bin', 'System Volume Information',
    '.git', '.svn', 'node_modules'
]

# File type extensions mappings
FILE_TYPES = {
    'Images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
    'Videos': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'},
    'Audio': {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'},
    'Documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.csv'}
}

class Scanner:
    def __init__(self, min_size_bytes=1024):
        self.min_size_bytes = min_size_bytes
        self.excludes = set([e.lower() for e in DEFAULT_EXCLUDES])

    def get_extensions_from_filters(self, filters):
        """Returns a set of allowed extensions based on active filters."""
        if 'All Files' in filters:
            return None # None means all extensions
        
        exts = set()
        for f in filters:
            if f in FILE_TYPES:
                exts.update(FILE_TYPES[f])
        return exts

    def scan_directories(self, paths, filters, progress_callback=None):
        """
        Scans given paths for files matching the filters.
        Groups files by their exact size.
        Returns: 
        - dict: {size_in_bytes: [filepaths]}
        - list: [image_filepaths] (useful for pass 2 image hashing)
        """
        files_by_size = defaultdict(list)
        image_files = []
        
        allowed_exts = self.get_extensions_from_filters(filters)
        image_exts = FILE_TYPES['Images']

        total_scanned = 0

        for root_path in paths:
            if not os.path.exists(root_path):
                continue
            
            for dirpath, dirnames, filenames in os.walk(root_path):
                # Filter out excluded directories in-place to avoid descending into them
                dirnames[:] = [d for d in dirnames if d.lower() not in self.excludes]
                
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    ext = os.path.splitext(filename)[1].lower()
                    
                    if allowed_exts is not None and ext not in allowed_exts:
                        continue
                    
                    try:
                        # Follow symlinks? No, usually bad idea for duplicates
                        if os.path.islink(filepath):
                            continue
                            
                        size = os.path.getsize(filepath)
                        if size < self.min_size_bytes:
                            continue
                        
                        files_by_size[size].append(filepath)
                        
                        if ext in image_exts:
                            image_files.append(filepath)
                            
                        total_scanned += 1
                        if progress_callback and total_scanned % 500 == 0:
                            progress_callback(f"Scanned {total_scanned} files...")
                            
                    except (OSError, FileNotFoundError, PermissionError):
                        continue

        if progress_callback:
            progress_callback(f"Scan complete. Found {total_scanned} candidate files.")

        return files_by_size, image_files
