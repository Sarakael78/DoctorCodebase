import ast
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from statistics import mean
from .file_utils import read_file

def extract_imports_and_functions(file_content):
    """
    Parses the Python file content and extracts import statements and function definitions.

    Returns:
        tuple: (list_of_imports, list_of_function_details)
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

    logging.debug("Extracted imports and functions from file content.")
    return imports, functions

def analyze_file(filepath):
    """Analyzes a single code file for statistics."""
    content = read_file(filepath)
    lines = content.count('\n') + 1  # +1 to count the last line if not empty
    try:
        tree = ast.parse(content)
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    except (SyntaxError, UnicodeDecodeError) as e:
        logging.warning(f"Skipping file due to parsing error: {filepath} - {e}")
        return lines, 0, 0, 0

    todos = sum(1 for line in content.splitlines() if "# TODO" in line)
    return lines, functions, classes, todos

def generate_stats(root_dir, code_files):
    """Generates statistics about the codebase, including TODO counts."""
    total_lines, total_functions, total_classes, total_todos = 0, 0, 0, 0
    function_counts = []
    file_lengths = []

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda file: analyze_file(os.path.join(root_dir, file)), code_files)

    for lines, functions, classes, todos in results:
        total_lines += lines
        total_functions += functions
        total_classes += classes
        total_todos += todos
        file_lengths.append(lines)
        if functions > 0:
            function_counts.append(functions)

    avg_func_length = mean(function_counts) if function_counts else 0
    avg_file_length = mean(file_lengths) if file_lengths else 0

    stats = {
        'Total Code Files': len(code_files),
        'Total Lines of Code': total_lines,
        'Total Functions': total_functions,
        'Total Classes': total_classes,
        'Average Function Length': round(avg_func_length, 2),
        'Average File Length': round(avg_file_length, 2),
        'Total TODOs': total_todos
    }

    logging.info("Generated statistics for the codebase.")
    return stats
