import os
import logging
from datetime import datetime
from .config import load_config
from .file_utils import collect_files, collect_folder_structure
from .analysis import generate_stats
from .output_writers import (write_stats_json, write_stats_csv, write_stats_txt, 
                             write_project_json, write_project_csv,write_project_txt)


def get_output_filename(base_name, suffix, extension, timestamp):
    """
    Helper function to generate consistent output filenames.
    """
    return f"{base_name}-{suffix}-{timestamp}.{extension}"

def process_codebase(root_dir, output_formats):
    """
    Processes the codebase and generates outputs based on selected formats.
    
    Args:
        root_dir (str): The root directory of the project.
        output_formats (dict): Selected output formats for Codebase and Statistics.
    
    Returns:
        dict: Information about generated files.
    """
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
            txt_filename = get_output_filename(project_filename, "project", "txt", timestamp)
            txt_path = os.path.join(output_dir, txt_filename)
            if txt_filename:
                response["CodeBase"].append(txt_filename) # Assuming you have a write_project_txt function similar to write_project_json
            # Implement write_project_txt similarly to write_project_json
            write_project_txt(root_dir, code_files, other_files, txt_path, ignored_dirs, pre_post_name)  
            response["CodeBase"].append(txt_filename)
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

    logging.info("Processing of codebase completed.")
    return response

def validate_selection(codebase_selection, statistics_selection):
    """Validates that at least one format is selected for both Codebase and Statistics."""
    errors = []
    if not codebase_selection:
        errors.append("At least one format must be selected for Codebase outputs.")
    if not statistics_selection:
        errors.append("At least one format must be selected for Statistics outputs.")
    return errors
