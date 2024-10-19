import os
import json
import csv
import logging
from .analysis import extract_imports_and_functions
from .file_utils import read_file
import fnmatch

def get_output_filename(base_name, suffix, extension, timestamp):
    """
    Helper function to generate consistent output filenames.
    """
    return f"{base_name}-{suffix}-{timestamp}.{extension}"

def write_stats_json(stats, output_dir, base_name, timestamp):
    """Writes statistics to a JSON file with improved nesting."""
    json_filename = get_output_filename(base_name, "stats", "json", timestamp)
    json_path = os.path.join(output_dir, json_filename)
    try:
        structured_stats = {
            "Codebase Statistics": {
                "Files": {
                    "Total Code Files": stats['Total Code Files'],
                    "Total Lines of Code": stats['Total Lines of Code']
                },
                "Components": {
                    "Total Functions": stats['Total Functions'],
                    "Total Classes": stats['Total Classes']
                }
            },
            "Code Quality": {
                "Metrics": {
                    "Average Function Length": stats['Average Function Length'],
                    "Average File Length": stats['Average File Length']
                },
                "Maintenance": {
                    "Total TODOs": stats['Total TODOs']
                }
            }
        }

        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(structured_stats, json_file, indent=4)
        logging.info(f"Statistics saved to JSON: {json_filename}")
        return json_filename
    except IOError as e:
        logging.error(f"Error writing to JSON file: {e}")
        return None

def write_stats_csv(stats, output_dir, base_name, timestamp):
    """Writes statistics to a CSV file."""
    csv_filename = get_output_filename(base_name, "stats", "csv", timestamp)
    csv_path = os.path.join(output_dir, csv_filename)
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Category', 'Statistic', 'Value'])

            # Codebase Statistics
            code_stats = ['Total Code Files', 'Total Lines of Code', 'Total Functions', 'Total Classes']
            for key in code_stats:
                writer.writerow(['Codebase Statistics', key, stats[key]])

            # Code Quality
            quality_stats = ['Average Function Length', 'Average File Length', 'Total TODOs']
            for key in quality_stats:
                writer.writerow(['Code Quality', key, stats[key]])

        logging.info(f"Statistics saved to CSV: {csv_filename}")
        return csv_filename
    except IOError as e:
        logging.error(f"Error writing to CSV file: {e}")
        return None

def write_stats_txt(stats, output_dir, base_name, timestamp):
    """Writes statistics to a TXT file."""
    txt_filename = get_output_filename(base_name, "stats", "txt", timestamp)
    txt_path = os.path.join(output_dir, txt_filename)
    try:
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write("===== Codebase Statistics =====\n")
            txt_file.write(f"Total Code Files: {stats['Total Code Files']}\n")
            txt_file.write(f"Total Lines of Code: {stats['Total Lines of Code']}\n")
            txt_file.write(f"Total Functions: {stats['Total Functions']}\n")
            txt_file.write(f"Total Classes: {stats['Total Classes']}\n\n")

            txt_file.write("===== Code Quality =====\n")
            txt_file.write(f"Average Function Length: {stats['Average Function Length']}\n")
            txt_file.write(f"Average File Length: {stats['Average File Length']}\n")
            txt_file.write(f"Total TODOs: {stats['Total TODOs']}\n")

        logging.info(f"Statistics saved to TXT: {txt_filename}")
        return txt_filename
    except IOError as e:
        logging.error(f"Error writing to TXT file: {e}")
        return None
    
def write_file_contents(root_dir, files, pt, pre_post_name, header):
    """Writes the content of specified files to the project.txt.

    Args:
        root_dir (str): The root directory of the project.
        files (list): List of file paths.
        file_type (str): Type of files being processed (e.g., code files).
        pt (file object): The file object to write the contents into.
    """
    
    pt.write(f"{pre_post_name}{pre_post_name} {header} {pre_post_name}{pre_post_name}")
    
    for file in files:
        pt.write(f"\n\n{pre_post_name} {file} {pre_post_name }\n\n")
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
        dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, pattern) for pattern in ignored_dirs)]

        level = dirpath.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        pt.write(f"{indent}{os.path.basename(dirpath)}/\n")
        sub_indent = ' ' * 4 * (level + 1)
        for fname in filenames:
            pt.write(f"{sub_indent}{fname}\n")
            
def write_project_txt(root_dir, code_files, other_files, project_txt_path, ignored_dirs, pre_post_name):
    """Writes the content of code and other files to project.txt.

    Args:
        root_dir (str): The root directory of the project.
        code_files (list): List of code file paths.
        other_files (list): List of other relevant file paths.
        project_txt_path (str): Path to the output project.txt file.
        ignored_dirs (set): Directories to ignore.
    """
    try:
        with open(project_txt_path, 'w', encoding='utf-8') as pt:
            write_file_contents(root_dir, code_files, pt, pre_post_name, "Code Files")
            write_file_contents(root_dir, other_files, pt, pre_post_name, "Other Files")
            write_folder_structure(root_dir, pt, ignored_dirs)
    except OSError as e:
        logging.error(f"Error writing to project.txt: {e}")
        
def write_project_json(root_dir, code_files, other_files, ignored_dirs, output_dir, base_name, timestamp, folder_structure):
    """Writes the collected project data to a JSON file with improved nesting and readability."""
    project_data = {
        'code_files': {},
        'other_files': {},
        'folder_structure': folder_structure
    }

    # Collect code files content with imports and functions
    for file in code_files:
        file_path = os.path.join(root_dir, file)
        content = read_file(file_path)
        imports, functions = extract_imports_and_functions(content)
        project_data['code_files'][file] = {
            "imports": imports,
            "functions": functions,
            "content": content.splitlines()
        }

    # Collect other files content as a list of lines
    for file in other_files:
        file_path = os.path.join(root_dir, file)
        content = read_file(file_path)
        project_data['other_files'][file] = {"content": content.splitlines()}

    # Write to JSON file with indentation for better readability
    json_filename = get_output_filename(base_name, "data", "json", timestamp)
    json_path = os.path.join(output_dir, json_filename)
    try:
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(project_data, json_file, indent=4)
        logging.info(f"Project data saved to JSON: {json_filename}")
        return json_filename
    except IOError as e:
        logging.error(f"Error writing project data to JSON file: {e}")
        return None

def write_project_csv(root_dir, code_files, other_files, folder_structure, output_dir, base_name, timestamp):
    """Writes project data summaries to CSV files."""
    output_files = []

    # Write Code Files List
    code_csv_filename = get_output_filename(base_name, "code_files", "csv", timestamp)
    code_csv_path = os.path.join(output_dir, code_csv_filename)
    try:
        with open(code_csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Code Files'])
            for file in code_files:
                writer.writerow([file])
        logging.info(f"Code files list saved to CSV: {code_csv_filename}")
        output_files.append(code_csv_filename)
    except IOError as e:
        logging.error(f"Error writing code files to CSV: {e}")

    # Write Imports List
    imports_csv_filename = get_output_filename(base_name, "imports", "csv", timestamp)
    imports_csv_path = os.path.join(output_dir, imports_csv_filename)
    try:
        with open(imports_csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['File', 'Import Statement'])
            for file in code_files:
                file_path = os.path.join(root_dir, file)
                content = read_file(file_path)
                imports, _ = extract_imports_and_functions(content)
                for imp in imports:
                    writer.writerow([file, imp])
        logging.info(f"Imports saved to CSV: {imports_csv_filename}")
        output_files.append(imports_csv_filename)
    except IOError as e:
        logging.error(f"Error writing imports to CSV: {e}")

    # Write Functions List
    functions_csv_filename = get_output_filename(base_name, "functions", "csv", timestamp)
    functions_csv_path = os.path.join(output_dir, functions_csv_filename)
    try:
        with open(functions_csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['File', 'Function Name', 'Docstring', 'Parameters', 'Definition'])
            for file in code_files:
                file_path = os.path.join(root_dir, file)
                content = read_file(file_path)
                _, functions = extract_imports_and_functions(content)
                for func in functions:
                    writer.writerow([
                        file,
                        func['name'],
                        func['docstring'].replace('\n', ' ') if func['docstring'] else '',
                        ", ".join(func['parameters']),
                        func['definition'].replace('\n', ' ')
                    ])
        logging.info(f"Functions saved to CSV: {functions_csv_filename}")
        output_files.append(functions_csv_filename)
    except IOError as e:
        logging.error(f"Error writing functions to CSV: {e}")

    # Write Other Files List
    other_csv_filename = get_output_filename(base_name, "other_files", "csv", timestamp)
    other_csv_path = os.path.join(output_dir, other_csv_filename)
    try:
        with open(other_csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Other Files'])
            for file in other_files:
                writer.writerow([file])
        logging.info(f"Other files list saved to CSV: {other_csv_filename}")
        output_files.append(other_csv_filename)
    except IOError as e:
        logging.error(f"Error writing other files to CSV: {e}")

    # Write Folder Structure
    folder_csv_filename = get_output_filename(base_name, "folder_structure", "csv", timestamp)
    folder_csv_path = os.path.join(output_dir, folder_csv_filename)
    try:
        with open(folder_csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Directory', 'Subdirectories', 'Files'])
            for dir, contents in folder_structure.items():
                subdirs = '; '.join(contents['subdirectories']) if contents['subdirectories'] else 'None'
                files = '; '.join(contents['files']) if contents['files'] else 'None'
                writer.writerow([dir, subdirs, files])
        logging.info(f"Folder structure saved to CSV: {folder_csv_filename}")
        output_files.append(folder_csv_filename)
    except IOError as e:
        logging.error(f"Error writing folder structure to CSV: {e}")

    return output_files
