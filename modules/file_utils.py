import os
from pathlib import Path
import fnmatch
import logging

def read_file(filepath):
    """Reads the content of a file, returning it as a string."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            logging.debug(f"Read file: {filepath}")
            return content
    except OSError as e:
        logging.warning(f"Error reading {filepath}: {e}")
        return ""

def collect_files(root_dir, ignored_dirs, other_exts, necessary_files, code_exts):
    """
    Collects Python and other relevant files from the project directory.
    
    Returns:
        tuple: (list_of_code_files, list_of_other_files)
    """
    code_files = []
    other_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Ignore specified directories using pattern matching
        dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, pattern) for pattern in ignored_dirs)]
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root_dir)
            ext = Path(filename).suffix.lower()

            if ext in code_exts:
                code_files.append(rel_path)
            elif ext in other_exts or filename.lower() in necessary_files:
                other_files.append(rel_path)

    logging.info(f"Collected {len(code_files)} code files and {len(other_files)} other files.")
    return code_files, other_files

def collect_folder_structure(root_dir, ignored_dirs):
    """
    Collects the folder structure of the project.
    
    Returns:
        dict: A dictionary representing the folder structure.
    """
    folder_structure = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Ignore specified directories
        dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, pattern) for pattern in ignored_dirs)]
        rel_dir = os.path.relpath(dirpath, root_dir)
        folder_structure[rel_dir] = {
            'subdirectories': dirnames,
            'files': filenames
        }
    logging.info("Collected folder structure.")
    return folder_structure
