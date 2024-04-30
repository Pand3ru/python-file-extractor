import os
import hashlib
import zipfile
from tqdm import tqdm
from rarfile import RarFile
import argparse

verb = False # Default value. I don't think this matters

class InvalidPathError(Exception):
    """Custom exception for invalid path arguments."""
    def __init__(self, message):
        super().__init__(message)

def unzipFile(name: str, dest: str):
    """ Function that extracts passed zip-archive to passed destination path """
    with zipfile.ZipFile(name, 'r') as zip_ref:
        files = zip_ref.infolist()
        progress = tqdm(files, desc="Extracting")

        if verb: # We do this so 'if' only happens once.
            for file in progress:
                progress.set_description(f"Extracting {file.filename} into {dest}")
                zip_ref.extract(file, dest)
        else:
            for file in progress:
                zip_ref.extract(file, dest)
    return

def unrarFile(name: str, dest: str):
    """ Function that extracts passed rar-archive to passed destination path """
    with RarFile(name) as rar_ref:
        files = rar_ref.infolist()
        progress = tqdm(files, desc="Extracting")

        if verb: # We do this so 'if' only happens once.
            for file in progress:
                progress.set_description(f"Extracting {file.filename} into {dest}")
                rar_ref.extract(file, dest)
        else:
            for file in progress:
                rar_ref.extract(file, dest)
    return

def extract_rar_files(dest: str, single: bool):
    """ Extracts all rar-archives in a given folder dest. Rules of single-folder apply """
    if single:
        destRar = os.path.join(dest, "rar-content")
        if not checkExistence(destRar):
            try:
                os.makedirs(destRar)
            except Exception as e:
                if verb:
                    print(f"Error creating {destRar}")
                    raise e
                raise Exception(f"Error creating {destRar}")
        extraction_path = destRar
    else:
        extraction_path = "" # This can't happen anyway but compiler wants it

    for file in os.listdir(dest):
        filepath = os.path.join(dest, file)
        if filepath.endswith(".rar"):
            if not single:
                extraction_path = os.path.join(dest, os.path.splitext(os.path.basename(filepath))[0])
            if verb:
                print(f"Extracting {filepath} into {extraction_path}")
            unrarFile(filepath, extraction_path)

def check_given_arguments(dest: str, origin: str, verb: bool) -> str:
    """ Checks the given arguments of argument parser for correctness.
        Destination Path has to be non existent or of type directory
        Origin Path has to refer to a file and exist                """

    if checkExistence(origin) == False:
        raise InvalidPathError(f"{origin} does not exist")
    if checkExistence(dest):
        if not os.path.isdir(dest):
            raise InvalidPathError(f"Specified location {dest} is a file. Destination should be of type: directory")
        elif not os.path.isdir(origin):
            dest = os.path.join(dest, os.path.splitext(os.path.basename(origin))[0]) # Hell awaits me
            return dest
        else:
            return dest
    else: # non existent
        if askUser(f"{dest} does not exist. Do you want to create it?") == False:
            raise Exception(f"Operation cancelled by {os.environ.get('USER')}")
        else:
            os.makedirs(dest, exist_ok=True)
            if verb:
                print(f"Creating {dest}")
            return dest

def copy_file(src, dst):
    """ Copy a file from src to dst with a progress bar and checksum verification. """
    if os.path.isdir(src):
        print(f"Skipped copying directory: {src}")
        return None  # Return None or an appropriate value for directories

    buffer_size = 1024 * 1024 # 1MB
    sha256_hash = hashlib.sha256()
    total_size = os.path.getsize(src)

    if checkExistence(dst):
        if askUser(f"{dst} already exists. Do you want to overwrite it?"):
            if verb:
                print("removing {dst}")
            os.remove(dst)
        else:
            print(f"skipping {src}")
            return 'skipped'

    with open(src, 'rb') as forigin, open(dst, 'wb') as fdest, tqdm(
        total=total_size, unit='B', unit_scale=True, desc=f"Copying {os.path.basename(src)} to {dst}") as pbar:
        while True:
            buffer = forigin.read(buffer_size)
            if not buffer:
                break
            fdest.write(buffer)
            sha256_hash.update(buffer)
            pbar.update(len(buffer))

    return sha256_hash.hexdigest()

def compare_hashes(src, dst):
    """ Compares hashes of the original file and the copied file. """
    if os.path.isdir(src):
        print(f"Skipping directory: {src}")
        return True  # Skip directories

    copied_hash = copy_file(src, dst)
    if copied_hash is None or copied_hash == 'skipped':
        return True  # Handle directories or skipped files gracefully

    original_hash = calculate_file_hash(src)

    if original_hash == copied_hash:
        if verb:
            print(f"Integrity verified for {src}")
        return True
    else:
        os.remove(dst)
        if verb:
            print(f"Hashes did not match. Removing {dst}")
        return False

def calculate_file_hash(filepath: str):
    """ Calculate the SHA-256 hash of a file """
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def initParser()->argparse.ArgumentParser:
    """ Initializes and configures the argument parser """
    parser = argparse.ArgumentParser(description="Copy files with ensured integrity")
    
    parser.add_argument('-d', '--destination', type=str, help='path to destination directory', required=True) # This has to be a folder
    parser.add_argument('-o', '--origin', type=str, help='path to origin directory', required=True) # This has to be a file
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode')
    parser.add_argument('-s', '--singlefolder', action='store_true', help='store rar-archives in a single folder')

    return parser

def checkExistence(path: str) -> bool:
    """ Checks if a file exists """
    return os.path.exists(path)

def askUser(message: str) -> bool:
    """ Promts user with a y/n question """
    while(True):
        user_input = input(f"{message} (y/n): ").lower()

        if user_input == 'yes' or user_input == 'y':
            return True
        if user_input == 'no' or user_input == 'n':
            return False

def containsRar(dest: str) -> bool:
    """ Checks if given folder contains rar-archives """
    if verb:
        print(f"Checking if {dest} contains rar-archives")
    for file in os.listdir(dest):
        if file.endswith(".rar"):
            return True
    return False

def copy_directory_with_integrity(src, dst):
    """ Recursively copies a directory and its contents with integrity checks for each file """
    if not os.path.exists(dst):
        os.makedirs(dst)
        if verb:
            print(f"Created directory {dst}")

    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dst_item = os.path.join(dst, item)
        if os.path.isdir(src_item):
            copy_directory_with_integrity(src_item, dst_item)  # Recursive call for directories
        else:
            if not compare_hashes(src_item, dst_item):
                print(f"File {src_item} is possibly corrupted. It was deleted automatically.")
def main():
    global verb 

    args = initParser().parse_args()

    # Get all arguments
    origin = args.origin
    dest = args.destination
    verb = args.verbose
    single = args.singlefolder

    dest = check_given_arguments(dest, origin, verb) # Will raise at runtime

    # Fix this mess.

    if origin.endswith(".rar") or origin.endswith(".zip"):
        if origin.endswith(".rar"):
            unrarFile(origin, dest)
        if origin.endswith(".zip"):
            unzipFile(origin, dest)
        
        if not containsRar(dest):
            return

        if askUser(f"rar-archive(s) found in {dest}. Do you want to extract them as well?") == False:
            return
        
        extract_rar_files(dest, single)
    else:
        if verb:
            print("Starting copy...")
        if os.path.isdir(origin):
            if verb:
                print(f"{origin} is of type folder. Copying it's content to {dest}")
                copy_directory_with_integrity(origin, dest)
        else:
            if not compare_hashes(origin, dest):
                print(f"File {origin} is possibly corrupted. It was deleted automatically")

if __name__ == "__main__":
    main()
