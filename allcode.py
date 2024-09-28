import gradio as gr
import argparse
import ast
import datetime
import os
from pathlib import Path
import fnmatch
import logging
from concurrent.futures import ThreadPoolExecutor
from statistics import mean
import json
import csv
import yaml

# Set up logging for better error tracking and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path='config.yaml'):
    """Loads configuration from a YAML file."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def read_file(filepath):
    """Reads the content of a file, returning it as a string."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except OSError as e:
        logging.warning(f"Error reading {filepath}: {e}")
        return ""

def collect_files(root_dir, ignored_dirs, other_exts, necessary_files, code_exts):
    """
    Collects Python and other relevant files from the project directory.

    Args:
        root_dir (str): The root directory of the project.
        ignored_dirs (set): Directories to ignore.
        other_exts (set): File extensions for other relevant files.
        necessary_files (set): Set of necessary file names.
        code_exts (set): File extensions for code files.

    Returns:
        tuple: Two lists, one of Python file paths and another of other relevant file paths.
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

    return code_files, other_files

def collect_folder_structure(root_dir, ignored_dirs):
    """
    Collects the folder structure of the project.

    Args:
        root_dir (str): The root directory of the project.
        ignored_dirs (set): Set of directory patterns to ignore.

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
    return folder_structure

def write_file_contents(root_dir, files, pt, pre_post_name, header):
    """Writes the content of specified files to the project.txt."""
    
    pt.write(f"{pre_post_name}{pre_post_name} {header} {pre_post_name}{pre_post_name}")
    
    for file in files:
        pt.write(f"\n\n{pre_post_name} {file} {pre_post_name }\n\n")
        try:
            content = read_file(os.path.join(root_dir, file))
            pt.write(content)
        except OSError as e:
            logging.warning(f"Error reading {file}: {e}")

def write_folder_structure_txt(root_dir, pt, ignored_dirs):
    """Writes the folder structure to the project.txt."""
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
    """Writes the content of code and other files to project.txt."""
    try:
        with open(project_txt_path, 'w', encoding='utf-8') as pt:
            write_file_contents(root_dir, code_files, pt, pre_post_name, "Code Files")
            write_file_contents(root_dir, other_files, pt, pre_post_name, "Other Files")
            write_folder_structure_txt(root_dir, pt, ignored_dirs)
    except OSError as e:
        logging.error(f"Error writing to project.txt: {e}")

def extract_imports_and_functions(file_content):
    """
    Parses the Python file content and extracts import statements and function definitions.

    Args:
        file_content (str): The content of the Python file.

    Returns:
        tuple: A list of import statements and a list of functions with detailed information.
    """
    imports = []
    functions = []

    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        logging.warning(f"Syntax error while parsing file: {e}")
        return imports, functions

    for node in ast.iter_child_nodes(tree):
        # Extract import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    imports.append(f"import {alias.name} as {alias.asname}")
                else:
                    imports.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ''
            for alias in node.names:
                if alias.asname:
                    imports.append(f"from {module} import {alias.name} as {alias.asname}")
                else:
                    imports.append(f"from {module} import {alias.name}")
        
        # Extract function definitions
        elif isinstance(node, ast.FunctionDef):
            func_name = node.name
            func_docstring = ast.get_docstring(node)
            func_params = [arg.arg for arg in node.args.args]
            # Getting the function definition as a string
            func_def = ast.unparse(node) if hasattr(ast, 'unparse') else f"def {func_name}(...):"
            # Extract the full source code of the function
            func_source = ast.get_source_segment(file_content, node) if hasattr(ast, 'get_source_segment') else func_def
            
            functions.append({
                "name": func_name,
                "docstring": func_docstring if func_docstring else "",
                "parameters": func_params,
                "definition": func_def,
                "source": func_source
            })

    return imports, functions

def analyze_file(filepath):
    """Analyzes a single code file for statistics."""
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

def generate_stats(root_dir, code_files):
    """Generates statistics about the codebase, including TODO counts."""
    total_lines, total_functions, total_classes, total_todos = 0, 0, 0, 0
    function_lengths = []
    file_lengths = []

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda file: analyze_file(os.path.join(root_dir, file)), code_files)

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
        'Total Code Files': len(code_files),
        'Total Lines of Code': total_lines,
        'Total Functions': total_functions,
        'Total Classes': total_classes,
        'Average Function Length': avg_func_length,
        'Average File Length': avg_file_length,
        'Total TODOs': total_todos
    }

def get_output_filename(base_name, suffix, extension, timestamp):
    """
    Helper function to generate consistent output filenames.

    Args:
        base_name (str): The base name from config.yaml.
        suffix (str): A suffix to differentiate file types (e.g., 'stats', 'data').
        extension (str): File extension (e.g., 'json', 'csv', 'txt').
        timestamp (str): The common timestamp string.

    Returns:
        str: The constructed filename.
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
        logging.info(f"Statistics have been saved to JSON at: {json_path}")
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

        logging.info(f"Statistics have been saved to CSV at: {csv_path}")
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

        logging.info(f"Statistics have been saved to TXT at: {txt_path}")
        return txt_filename
    except IOError as e:
        logging.error(f"Error writing to TXT file: {e}")
        return None

def write_project_json(root_dir, code_files, other_files, ignored_dirs, output_dir, base_name, timestamp, folder_structure):
    """
    Writes the collected project data to a JSON file with improved nesting and readability,
    including the full source code of each function.
    """
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
        logging.info(f"Project data has been saved to JSON at: {json_path}")
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
        logging.info(f"Code files list has been saved to CSV at: {code_csv_path}")
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
        logging.info(f"Imports have been saved to CSV at: {imports_csv_path}")
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
        logging.info(f"Functions have been saved to CSV at: {functions_csv_path}")
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
        logging.info(f"Other files list has been saved to CSV at: {other_csv_path}")
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
        logging.info(f"Folder structure has been saved to CSV at: {folder_csv_path}")
        output_files.append(folder_csv_filename)
    except IOError as e:
        logging.error(f"Error writing folder structure to CSV: {e}")

    return output_files

def process_codebase(root_dir, output_formats):
    """Processes the codebase and generates outputs based on selected formats."""
    # Load configuration
    config = load_config()
    ignored_dirs = set(config['directories']['ignore'])
    other_exts = set(config['extensions']['other'])
    code_exts = set(config['extensions']['code'])
    necessary_files = set(name.lower() for name in config['files']['necessary'])
    pre_post_name = config['output']['file_designation_pre_post_format']
    project_filename = config['output']['file_name']

    # Collect files
    code_files, other_files = collect_files(root_dir, ignored_dirs, other_exts, necessary_files, code_exts)

    # Collect folder_structure
    folder_structure = collect_folder_structure(root_dir, ignored_dirs)

    # Generate a timestamp for the filename (once)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the output folder if it doesn't exist
    output_dir = os.path.join(root_dir, "cd-output")
    os.makedirs(output_dir, exist_ok=True)

    # Prepare output data
    stats = generate_stats(root_dir, code_files)

    # Initialize response dictionary
    response = {
        "status": "Success",
        "CodeBase": []
    }

    # Handle Statistics Outputs
    if 'Statistics' in output_formats:
        stats_output = output_formats['Statistics']
        if 'json' in stats_output:
            json_filename = write_stats_json(stats, output_dir, project_filename, timestamp)
            if json_filename:
                response["CodeBase"].append(json_filename)
        if 'csv' in stats_output:
            csv_filename = write_stats_csv(stats, output_dir, project_filename, timestamp)
            if csv_filename:
                response["CodeBase"].append(csv_filename)
        if 'txt' in stats_output:
            txt_filename = write_stats_txt(stats, output_dir, project_filename, timestamp)
            if txt_filename:
                response["CodeBase"].append(txt_filename)

    # Handle Codebase Outputs
    if 'Codebase' in output_formats:
        codebase_output = output_formats['Codebase']
        # Write project.txt if TXT is selected
        if 'txt' in codebase_output:
            project_txt_filename = get_output_filename(project_filename, "project", "txt", timestamp)
            project_txt_path = os.path.join(output_dir, project_txt_filename)
            write_project_txt(root_dir, code_files, other_files, project_txt_path, ignored_dirs, pre_post_name)
            response["CodeBase"].append(project_txt_filename)
        # Write JSON
        if 'json' in codebase_output:
            json_filename = write_project_json(root_dir, code_files, other_files, ignored_dirs, output_dir, project_filename, timestamp, folder_structure)
            if json_filename:
                response["CodeBase"].append(json_filename)
        # Write CSV
        if 'csv' in codebase_output:
            csv_files = write_project_csv(root_dir, code_files, other_files, folder_structure, output_dir, project_filename, timestamp)
            if csv_files:
                response["CodeBase"].extend(csv_files)

    return response

def validate_selection(codebase_selection, statistics_selection):
    """Validates that at least one format is selected for both Codebase and Statistics."""
    errors = []
    if not codebase_selection:
        errors.append("At least one format must be selected for Codebase outputs.")
    if not statistics_selection:
        errors.append("At least one format must be selected for Statistics outputs.")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Document a Code Base.")
    parser.add_argument("--cli", action='store_true', help="Run in command-line mode.")
    parser.add_argument("root_dir", nargs='?', default=os.getcwd(),
                        help="Path to the project root. Defaults to current directory.")
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        logging.error("Argument parsing failed. Please check your input.")
        return  # Exit the main function gracefully

    if args.cli:
        # Run as a command-line tool
        output_formats = {
            "Codebase": ["txt", "json", "csv"],
            "Statistics": ["json", "csv", "txt"]
        }
        response = process_codebase(args.root_dir, output_formats)

        # Print response
        logging.info("===== Output Files Generated =====")
        for file in response["output_files"]:
            logging.info(f"- {file}")
    else:
        # Launch Gradio Interface by default
        def gradio_process(root_dir, codebase_selection, statistics_selection):
            errors = validate_selection(codebase_selection, statistics_selection)
            if errors:
                return {"error": " ".join(errors)}
            
            output_formats = {
                "Codebase": codebase_selection,
                "Statistics": statistics_selection
            }
            response = process_codebase(root_dir, output_formats)
            return {
                "Status": response["status"],
                "Generated Files": response["CodeBase"]
            }

        with gr.Blocks() as iface:
            gr.Markdown("# Codebase Documenter")

            with gr.Row():
                with gr.Column():
                    root_dir_input = gr.Textbox(label="Project Root Directory", value=os.getcwd(), lines=1)
                with gr.Column():
                    run_button = gr.Button("Run Documenter")
            
            gr.Markdown("## Select Output Formats")

            with gr.Group():
                gr.Markdown("### Codebase Outputs")
                codebase_checkbox = gr.CheckboxGroup(
                    choices=["txt", "json", "csv"],
                    label="Select formats for Codebase:",
                    value=["txt"]
                )

                gr.Markdown("### Statistics Outputs")
                statistics_checkbox = gr.CheckboxGroup(
                    choices=["txt", "json", "csv"],
                    label="Select formats for Statistics:",
                    value=["json"]
                )
            
            output = gr.JSON(label="Output")

            run_button.click(
                fn=gradio_process,
                inputs=[root_dir_input, codebase_checkbox, statistics_checkbox],
                outputs=output
            )

            gr.Markdown("""
            ## Instructions

            1. **Project Root Directory:** Enter the path to your project's root directory. If left blank, the current directory will be used.
            2. **Select Output Formats:**
               - **Codebase Outputs:** Choose among TXT, JSON, and CSV to generate documentation of your codebase.
               - **Statistics Outputs:** Choose among TXT, JSON, and CSV to generate statistics about your codebase.
            3. **Run Documenter:** Click the "Run Documenter" button to generate the selected outputs.
            4. **View Outputs:** The generated files will be saved in the `cd-output` directory within your project root.
            """)

        iface.launch(debug=True)  # Enable debug mode for Gradio

if __name__ == "__main__":
    main()
