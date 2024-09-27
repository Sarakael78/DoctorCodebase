import argparse
import ast
import datetime
import os
from pathlib import Path
import fnmatch
import logging
from concurrent.futures import ThreadPoolExecutor
from statistics import mean
import json, csv, yaml

# Set up logging for better error tracking and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path='config.yaml'):
    """Loads configuration from a YAML file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: Configuration settings.
    """
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def read_file(filepath):
    """Reads the content of a file, returning it as a string.

    Args:
        filepath (str): The path to the file.

    Returns:
        str: Content of the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except OSError as e:
        logging.warning(f"Error reading {filepath}: {e}")
        return ""

def collect_files(root_dir, ignored_dirs, config_exts, necessary_files):
    """Collects Python and other relevant files from the project directory.

    Args:
        root_dir (str): The root directory of the project.
        ignored_dirs (set): Directories to ignore.
        config_exts (set): File extensions for configuration files.
        necessary_files (set): Set of necessary file names.

    Returns:
        tuple: Two lists, one of Python file paths and another of other relevant file paths.
    """
    python_files = []
    other_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Ignore specified directories using pattern matching
        dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, pattern) for pattern in ignored_dirs)]
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root_dir)
            ext = Path(filename).suffix.lower()

            if ext == '.py':
                python_files.append(rel_path)
            elif ext in config_exts or filename in necessary_files:
                other_files.append(rel_path)

    return python_files, other_files

def write_file_contents(root_dir, files, file_type, pt):
    """Writes the content of specified files to the project.txt.

    Args:
        root_dir (str): The root directory of the project.
        files (list): List of file paths.
        file_type (str): Type of files being processed (e.g., Python files).
        pt (file object): The file object to write the contents into.
    """
    for file in files:
        pt.write(f"\n\n===== {file_type} - {file} =====\n\n")
        try:
            content = read_file(os.path.join(root_dir, file))
            pt.write(content)
        except OSError as e:
            logging.warning(f"Error reading {file}: {e}")

def write_folder_structure(root_dir, pt, ignored_dirs):
    """Writes the folder structure to the project.txt.

    Args:
        root_dir (str): The root directory of the project.
        pt (file object): The file object to write the folder structure into.
        ignored_dirs (set): Directories to ignore.
    """
    pt.write("\n\n===== Folder Structure =====\n\n")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]

        level = dirpath.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        pt.write(f"{indent}{os.path.basename(dirpath)}/\n")
        sub_indent = ' ' * 4 * (level + 1)
        for fname in filenames:
            pt.write(f"{sub_indent}{fname}\n")

def write_project_txt(root_dir, python_files, other_files, project_txt_path, ignored_dirs):
    """Writes the content of Python and other files to project.txt.

    Args:
        root_dir (str): The root directory of the project.
        python_files (list): List of Python file paths.
        other_files (list): List of other relevant file paths.
        project_txt_path (str): Path to the output project.txt file.
        ignored_dirs (set): Directories to ignore.
    """
    try:
        with open(project_txt_path, 'w', encoding='utf-8') as pt:
            write_file_contents(root_dir, python_files, "Python files", pt)
            write_file_contents(root_dir, other_files, "Other necessary files", pt)
            write_folder_structure(root_dir, pt, ignored_dirs)
    except OSError as e:
        logging.error(f"Error writing to project.txt: {e}")

def analyze_file(filepath):
    """Analyzes a single Python file for statistics.

    Args:
        filepath (str): The path to the Python file.

    Returns:
        tuple: Lines, function count, class count, and TODO count in the file.
    """
    content = read_file(filepath)
    lines = content.count('\n')
    try:
        tree = ast.parse(content)
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    except (SyntaxError, UnicodeDecodeError) as e:
        logging.warning(f"Skipping file due to error in parsing: {filepath} - {e}")
        return lines, 0, 0, 0

    todos = sum(1 for line in content.splitlines() if "# TODO" in line)
    return lines, functions, classes, todos

def generate_stats(root_dir, python_files):
    """Generates statistics about the Python code, including TODO counts.

    Args:
        root_dir (str): The root directory of the project.
        python_files (list): List of Python file paths.

    Returns:
        dict: Statistics including total files, lines, functions, classes, and TODOs.
    """
    total_lines, total_functions, total_classes, total_todos = 0, 0, 0, 0
    function_lengths = []
    file_lengths = []

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda file: analyze_file(os.path.join(root_dir, file)), python_files)

    for lines, functions, classes, todos in results:
        total_lines += lines
        total_functions += functions
        total_classes += classes
        total_todos += todos
        file_lengths.append(lines)
        if functions > 0:  # Avoid division by zero
            function_lengths.append(functions)

    avg_func_length = mean(function_lengths) if function_lengths else 0
    avg_file_length = mean(file_lengths) if file_lengths else 0

    return {
        'Total Python files': len(python_files),
        'Total lines of code': total_lines,
        'Total functions': total_functions,
        'Total classes': total_classes,
        'Average function length': avg_func_length,
        'Average file length': avg_file_length,
        'Total TODOs': total_todos
    }

def write_stats_json(stats, output_dir, timestamp):
    """Writes statistics to a JSON file.

    Args:
        stats (dict): The statistics to write.
        output_dir (str): The directory to save the output file.
        timestamp (str): Timestamp to append to the filename.
    """
    json_path = os.path.join(output_dir, f"project_stats_{timestamp}.json")
    try:
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(stats, json_file, indent=4)
    except IOError as e:
        logging.error(f"Error writing to JSON file: {e}")

def write_stats_csv(stats, output_dir, timestamp):
    """Writes statistics to a CSV file.

    Args:
        stats (dict): The statistics to write.
        output_dir (str): The directory to save the output file.
        timestamp (str): Timestamp to append to the filename.
    """
    csv_path = os.path.join(output_dir, f"project_stats_{timestamp}.csv")
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Statistic', 'Value'])
            for key, value in stats.items():
                writer.writerow([key, value])
    except IOError as e:
        logging.error(f"Error writing to CSV file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Analyze a Python project.")
    parser.add_argument("root_dir", nargs='?', default=os.getcwd(),
                        help="Path to the project root. Defaults to current directory.")
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    ignored_dirs = set(config['directories']['ignored'])
    config_exts = set(config['extensions']['config'])
    necessary_files = set(config['files']['necessary'])

    python_files, other_files = collect_files(args.root_dir, ignored_dirs, config_exts, necessary_files)

    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    project_txt_filename = f"project_{timestamp}.txt"

    # Create the output folder if it doesn't exist
    output_dir = os.path.join(args.root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Construct the full path for the output file
    project_txt_path = os.path.join(output_dir, project_txt_filename)

    write_project_txt(args.root_dir, python_files, other_files, project_txt_path, ignored_dirs)

    stats = generate_stats(args.root_dir, python_files)

    # Print stats
    logging.info("===== Project Statistics =====")
    for key, value in stats.items():
        logging.info(f"{key}: {value}")

if __name__ == "__main__":
    main()
