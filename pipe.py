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
        else:
            dest = os.path.join(dest, os.path.splitext(os.path.basename(origin))[0]) # Hell awaits me
            print(f"called {dest}")
            return dest
    else: # non existent
        if askUser(f"{dest} does not exist. Do you want to create it?") == False:
            raise Exception(f"Operation cancelled by {os.environ.get('USER')}")
        else:
            os.makedirs(dest, exist_ok=True)
            if verb:
                print(f"Creating {dest}")
            return dest

def copy_file(origin: str, dest: str):
    """ Copy a file from src to dst with a progress bar and checksum verification. """
    buffer_size = 1024 * 1024 # 1MB
    sha256_hash = hashlib.sha256()

    total_size = os.path.getsize(origin)
    dest_file_path = os.path.join(dest, os.path.basename(origin))
    with open(origin, 'rb') as forigin, open(dest_file_path, 'wb') as fdest, tqdm(
        total=total_size, unit='B', unit_scale=True, desc=f"Copying {os.path.basename(origin)} to {dest_file_path}") as pbar:
        while True:
            buffer = forigin.read(buffer_size)
            if not buffer:
                break
            fdest.write(buffer)
            sha256_hash.update(buffer)
            pbar.update(len(buffer))
    return sha256_hash.hexdigest()

def compare_hashes(original: str, copy: str) -> bool:
    """ Verify the integrity of the copied file by comparing hashes """
    original_hash = copy_file(original, copy)
    copied_hash = calculate_file_hash(copy)
    
    if original_hash == copied_hash:
        return True
    else:
        return False

def calculate_file_hash(filepath: str):
    """ Calculate the SHA-256 hash of a file """
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as file:
        for byte_block in iter(lambda: file.read(4096), "b"):
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

def main():
    global verb 

    args = initParser().parse_args()

    # Get all arguments
    origin = args.origin
    dest = args.destination
    verb = args.verbose
    single = args.singlefolder

    dest = check_given_arguments(dest, origin, verb) # Will raise at runtime

    if origin.endswith(".rar") or origin.endswith(".zip"):
        if origin.endswith(".rar"):
            unrarFile(origin, dest)
        if origin.endswith(".zip"):
            unzipFile(origin, dest) # WARNING: Check if it is even a zip file
        
        if not containsRar(dest):
            return

        if askUser(f"rar-archive(s) found in {dest}. Do you want to extract them as well?") == False:
            return
        
        extract_rar_files(dest, single)
    else:
        if verb:
            print("Starting copy...")
        compare_hashes(origin, dest) 

if __name__ == "__main__":
    main()
