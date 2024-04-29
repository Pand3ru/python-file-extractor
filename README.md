# File Integrity Script

## Overview
This repository contains a Python script designed to handle file operations with an emphasis on maintaining integrity during file transfers. It's a simple utility aimed at ensuring that files are copied or extracted (from ZIP and RAR archives) without corruption. This script is ideal for users who need to ensure that their files remain intact after copying, especially in environments where data corruption might be a concern.

## Features
- **File Copying**: Copies files from one location to another with a SHA-256 integrity check.
- **Archive Extraction**: Supports extracting files from ZIP and RAR archives while preserving file integrity.
- **Progress Display**: Provides a progress bar during file operations for better user interaction.
- **Verbose Output**: Optional verbose output to track detailed operations.

## Usage
To use this script, you need Python installed on your system along with some dependencies listed below.

### Dependencies
- `tqdm`
- `rarfile` (For handling RAR files)

Install them using pip:
```bash
pip install tqdm rarfile
```

### Running the script
Clone this repository, navigate to the directory containing the script, and run it as follows:
```bash
python3 script_name.py -o <origin_path> -d <destination_path> [-v] [-s]
```
- `-o`: Origin file or directory path
- `-d`: Destination directory path
- `-v`: Enable verbose output (optional)
- `-s`: Extract all RAR archives into a single folder (optional)

## Contributions
Contributions are welcome! If you have a bug fix, improvement, or new feature suggestion, feel free to fork this repository and submit a pull request.

## Project Status
This script is provided as-is for those who find it useful. Once completed, it will not be actively maintained, so please consider this when deciding to use it for critical applications.

## License
This project is open-sourced under the MIT License. See the LICENSE file for more details.


