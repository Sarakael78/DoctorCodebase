# Codebase Documenter

## Overview

Codebase Documenter is a Python tool designed to help you document and analyze your project by generating a comprehensive file (`project_<timestamp>.txt`). This file contains all your source code, configuration files, and project structure, along with detailed statistics.

### Use Cases

- **Code Sharing**: Easily share your codebase with others.
- **Project Archiving**: Create a snapshot of your project at a specific point in time.
- **Developer Onboarding**: Quickly onboard new developers by providing a clear view of the project structure.
- **Project Analysis**: Gain insights into your project's complexity and structure through statistics.

**_The output file includes:_**

- Source code of all Python files in the project
- Content of configuration files (`.cfg`, `.ini`, `.yaml`, `.yml`, `.toml`)
- Content of JSON files (`.json`)
- Content of essential files like `requirements.txt` and `Dockerfile`
- A representation of the project's folder structure
- Project statistics (number of files, lines of code, functions, classes, and other interesting stats)

### Features

- **Comprehensive Documentation**: Captures source code, configuration files, JSON files, and a folder structure.
- **Detailed Statistics**: Provides insights into the codebase's size and complexity (files, lines of code, functions, classes, TODO comments).
- **Customizable and Extensible**: Easily modify the script to include/exclude specific file types or directories as needed.

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone CodeBase_Documenter.git
cd CodeBase_Documenter
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage
To run the script, use the following command:
```bash
python allcode.py [root_dir]
```

- **root_dir (optional):** This is the path to the root directory of your project. If you do not provide this argument, the script will default to using the current working directory.

## Output
- The script will generate a file named project*<timestamp>.txt within the output directory located in your project's root directory.
- The **timestamp** in the filename indicates the date and time when the file was generated.
- If the output directory does not exist, the script will create it automatically.

## Configuration
- The script utilizes a config.yaml file to manage settings such as ignored directories and recognized file extensions.
- You can customize these settings to fit the specific needs of your project.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License.
