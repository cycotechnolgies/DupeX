import os
import hashlib
from collections import defaultdict
from PIL import Image
import imagehash
import send2trash

class DuplicateEngine:
    def __init__(self):
        self.exact_duplicates = [] # List of lists of file paths
        self.similar_duplicates = [] # List of dicts with paths and confidence
        self.hash_cache = {}

    def get_file_hash(self, filepath, blocksize=65536):
        """Returns the SHA-256 hash of a file."""
        if filepath in self.hash_cache:
            return self.hash_cache[filepath]
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as afile:
                buf = afile.read(blocksize)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(blocksize)
            file_hash = hasher.hexdigest()
            self.hash_cache[filepath] = file_hash
            return file_hash
        except Exception:
            return None

    def find_exact_duplicates(self, files_by_size, progress_callback=None, abort_event=None, pause_event=None):
        """
        Pass 1: Find exact duplicates by hashing files of the same size.
        files_by_size: dict mapping size to list of filepaths.
        """
        total_files = sum(len(paths) for paths in files_by_size.values() if len(paths) > 1)
        processed = 0

        for size, paths in files_by_size.items():
            if abort_event and abort_event.is_set():
                break
            
            if len(paths) < 2:
                continue
            
            hashes = defaultdict(list)
            for path in paths:
                if abort_event and abort_event.is_set():
                    break
                if pause_event:
                    pause_event.wait()
                    
                file_hash = self.get_file_hash(path)
                if file_hash:
                    hashes[file_hash].append(path)
                processed += 1
                if progress_callback:
                    progress_callback(processed, total_files, f"Hashing {os.path.basename(path)}")

            for file_hash, identical_paths in hashes.items():
                if len(identical_paths) > 1:
                    self.exact_duplicates.append(identical_paths)
        
        return self.exact_duplicates

    def find_similar_images(self, image_paths, progress_callback=None):
        """
        Pass 2: Find similar images using pHash.
        """
        hashes = {}
        total = len(image_paths)
        for i, path in enumerate(image_paths):
            try:
                with Image.open(path) as img:
                    hashes[path] = imagehash.phash(img)
            except Exception:
                pass
            if progress_callback:
                progress_callback(i + 1, total, f"Analyzing image {os.path.basename(path)}")
        
        # O(N^2) comparison - fine for small numbers, needs optimization for large datasets
        # A simple clustering approach based on hamming distance
        visited = set()
        for path1, hash1 in hashes.items():
            if path1 in visited:
                continue
            
            group = [path1]
            visited.add(path1)
            
            for path2, hash2 in hashes.items():
                if path2 in visited:
                    continue
                # Hamming distance threshold for similarity (e.g., <= 5 is very similar)
                if hash1 - hash2 <= 5: 
                    group.append(path2)
                    visited.add(path2)
            
            if len(group) > 1:
                self.similar_duplicates.append({
                    'type': 'image',
                    'files': group,
                    'confidence': 95 # Hardcoded for now based on threshold
                })

    def delete_files(self, filepaths):
        """Safely sends files to the recycle bin."""
        success_count = 0
        for path in filepaths:
            try:
                # Windows SHFileOperation API requires normalized backslashes
                normalized_path = os.path.abspath(os.path.normpath(path))
                send2trash.send2trash(normalized_path)
                success_count += 1
            except Exception as e:
                print(f"Error deleting {path}: {e}")
        return success_count
