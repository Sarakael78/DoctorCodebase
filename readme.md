# DoctorCodebase

## Overview

**DoctorCodebase** is a Python tool designed to help you document and analyze your codebase by generating a comprehensive file (`<projectname>_<timestamp>.txt`). This file will contain all your source code, configuration files, and project structure, along with detailed statistics.

### Use Cases

- **Code Sharing**: Easily share your codebase with others.
- **Project Archiving**: Create a snapshot of your project at a specific point in time.
- **Developer Onboarding**: Quickly onboard new developers by providing a clear view of the project structure.
- **Project Analysis**: Gain insights into your project's complexity and structure through statistics.
- **AI Context**: Provide an AI your full code base in one file.

**_The output file includes:_**

- **Source code** of all Python files in the project
- Content of **other files** (customizable in the config.yaml file)
- Content of **essential files** like `requirements.txt` and `Dockerfile` (also customizable)
- A representation of the project's **folder structure**
- **Project statistics** (number of files, lines of code, functions, classes, and other interesting stats)

### Features

- **Comprehensive Documentation**: Captures source code, configuration files, JSON files, and a folder structure.
- **Detailed Statistics**: Provides insights into the codebase's size and complexity (files, lines of code, functions, classes, TODO comments).
- **Customizable and Extensible**: Easily modify the script to include/exclude specific file types or directories as needed.

## Installation

**Install Git** 

- **Clone** the repository and navigate to the project directory:
  ```bash
  git clone DSB-odeBase_Documenter.git
  cd DSB-CodeBase_Documenter
  ```

- Create a **virtual environment** in the project directory:
  ```bash
  python -m venv .venv
  ```

- Activate the virtual environment:
  - **On Windows:**
    ```bash
    .venv\Scripts\activate
    ```
  - **On macOS and Linux:**
    ```bash
    source .venv/bin/activate
    ```

- Install the required **dependencies** within the virtual environment:
  ``` bash
  pip install -r requirements.txt
  ```

#### Explanation

- **Creating a Virtual Environment**: The command `python -m venv .venv` creates a virtual environment in a directory named `.venv` within your project directory.
- **Activating the Virtual Environment**: The activation commands differ slightly between Windows and Unix-based systems (macOS and Linux).
- **Installing Dependencies**: Once the virtual environment is activated, `pip install -r requirements.txt` installs the necessary packages into this isolated environment.

This approach helps manage dependencies more effectively and avoids potential conflicts with other Python projects on your system.
## Output

Depending on the selected options, the script will generate:

- **Codebase Outputs:**
  - **TXT:** Comprehensive documentation of code and project structure.
  - **JSON:** Structured JSON containing code files, other files, and folder structure.
  - **CSV:** Separate CSV files listing code files, other files, and folder structure.

- **Statistics Outputs:**
  - **TXT:** Formatted text file with codebase statistics.
  - **JSON:** Structured JSON with categorized statistics.
  - **CSV:** CSV file summarizing statistics.

## Usage

### CLI Mode

To run the script in CLI mode and generate all output files:
```bash
python allcode.py --cli [root_dir]


## Usage
To run the script, use the following command:
```bash
python allcode.py [root_dir]
```

- **root_dir (optional):** This is the path to the root directory of your project. If you do not provide this argument, the script will default to using the current working directory.



## Configuration
- The script utilizes a config.yaml file to manage settings such as ignored directories and recognized file extensions.
- You can customize these settings to fit the specific needs of your project.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License.
