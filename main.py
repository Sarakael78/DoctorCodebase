import argparse
import logging
import os
from modules.process import process_codebase
from modules.interface import launch_interface

# Set up logging for better error tracking and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Run as a command-line tool with all output formats
        output_formats = {
            "Codebase": ["txt", "json", "csv"],
            "Statistics": ["txt","json","csv" ]
        }
        response = process_codebase(args.root_dir, output_formats)

        # Print response
        logging.info("===== Output Files Generated =====")
        for file in response.get("CodeBase", []):
            logging.info(f"- {file}")
    else:
        # Launch Gradio Interface by default
        launch_interface()

if __name__ == "__main__":
    main()
