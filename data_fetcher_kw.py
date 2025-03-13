import os
import requests
import shutil
import zipfile
import json
from colorama import Fore, Back, Style
from datetime import datetime


def load_config(config_file="config.json"):
    """Load configuration settings from a JSON file.

    Args:
        config_file (str): Path to the configuration file. Defaults to 'config.json'.

    Returns:
        dict: Configuration settings.

    Raises:
        FileNotFoundError: If the config file is not found.
        json.JSONDecodeError: If the config file is invalid JSON.
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(Fore.RED + f"Error: Config file '{config_file}' not found.")
        raise
    except json.JSONDecodeError:
        print(Fore.RED + f"Error: Invalid JSON in '{config_file}'.")
        raise

def fetch_disa_data(config, base_path):
    """Fetch DISA data from the specified URL and save it locally.

    Args:
        config (dict): Configuration settings from config file.
        base_path (str): Base directory path for file operations.

    Returns:
        str: Path to the downloaded DISA file.
    """
    month = datetime.now().strftime('%B')
    year = datetime.now().strftime('%Y')
    disa_url = config["disa_url"]
    print(Back.YELLOW + f"Retrieving file from {disa_url}")
    get_disa_file = requests.get(disa_url)
    disa_file = disa_url.split('/')[-1]
    print(f"File {disa_file} was retrieved")

    with open(disa_file, 'wb') as output_file:
        output_file.write(get_disa_file.content)
    print(Fore.GREEN + f"Stored {disa_file} in {base_path}")
    return disa_file

def extract_and_sort_files(config, disa_file, base_path):
    """Extract the DISA zip file and sort contents into SRG and STIG directories.

    Args:
        config (dict): Configuration settings from config file.
        disa_file (str): Path to the downloaded DISA zip file.
        base_path (str): Base directory path for file operations.
    """
    file_location = os.path.join(base_path, config["file_imports_dir"]) + '/'
    srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
    stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

    # Extract files
    print(Fore.MAGENTA + f"Extracting files to: {file_location}")
    with zipfile.ZipFile(disa_file, 'r') as zObject:
        zObject.extractall(path=file_location)

    # Move SRGs and STIGs
    print(Fore.CYAN + f"Checking for SRGs and STIGs in: {file_location}")
    files = os.listdir(file_location)
    for f in files:
        if f.endswith(config["srg_zip_suffix"]):
            print(Fore.CYAN + f"Moving {f} to {srg_folder}")
            shutil.move(file_location + f, srg_folder + f)
        elif f.endswith(config["zip_suffix"]):
            print(Fore.CYAN + f"Moving {f} to {stig_folder}")
            shutil.move(file_location + f, stig_folder + f)

    # Unzip SRGs and STIGs, then sort XML files
    for folder, suffix in [(srg_folder, "SRG"), (stig_folder, "STIG")]:
        for item in os.listdir(folder):
            if not item.endswith(config["zip_suffix"]):
                continue
            file_name = os.path.abspath(folder + item)
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                zip_ref.extractall(folder)
            os.remove(file_name)

        for subdir, _, files in os.walk(folder):
            for f in files:
                if f.endswith(config["xml_suffix"]):
                    print(Fore.LIGHTYELLOW_EX + f"Moving {f} to {folder}")
                    shutil.move(os.path.join(subdir, f), folder + f)

def clean_up_files(config, disa_file, base_path):
    """Clean up temporary files and directories, keeping only XML files.

    Args:
        config (dict): Configuration settings from config file.
        disa_file (str): Path to the downloaded DISA zip file.
        base_path (str): Base directory path for file operations.
    """
    srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
    stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

    # Remove downloaded zip
    if os.path.exists(disa_file):
        os.remove(disa_file)
        print(Fore.RED + f"Removed {disa_file} from {base_path}")
    else:
        print("File does not exist")

    # Clean non-XML files and empty directories
    for folder in [srg_folder, stig_folder]:
        for subdir, dirs, files in os.walk(folder):
            for f in files:
                if not f.endswith(config["xml_suffix"]):
                    file_path = os.path.join(subdir, f)
                    print(Fore.RED + f"Deleting {f} from {folder}")
                    os.remove(file_path)

        for root, dirs, _ in os.walk(folder, topdown=False):
            for directory in dirs:
                dirpath = os.path.join(root, directory)
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    print(Fore.RED + f"Deleting: {dirpath}")

def main():
    """Main function to orchestrate fetching, extracting, and cleaning DISA data.

    Guide for Developers:
        - Modify 'config.json' to change URLs, directories, or file suffixes.
        - Ensure required directories exist or have write permissions.
        - Dependencies: requests, colorama (see requirements.txt).
        - Runs in the current working directory; adjust paths if needed.
    """
    base_path = os.getcwd()
    config = load_config()

    # Ensure directories exist
    for dir_key in ["file_imports_dir", "srg_dir", "stig_dir"]:
        os.makedirs(os.path.join(base_path, config[dir_key]), exist_ok=True)

    disa_file = fetch_disa_data(config, base_path)
    extract_and_sort_files(config, disa_file, base_path)
    clean_up_files(config, disa_file, base_path)
    print(Style.RESET_ALL)

if __name__ == "__main__":
    main()
