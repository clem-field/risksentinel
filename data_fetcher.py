import os
import requests
import shutil
import zipfile
import json
from colorama import Fore, Style
from datetime import datetime, timedelta

def load_config(config_file="config.json"):
    """
    Load configuration settings from a JSON file.

    This function reads the configuration file specified by `config_file` and returns
    the settings as a dictionary. If the file is not found or contains invalid JSON,
    it raises an appropriate exception.

    Args:
        config_file (str): Path to the configuration file. Defaults to 'config.json'.

    Returns:
        dict: Configuration settings loaded from the JSON file.

    Raises:
        FileNotFoundError: If the config file is not found.
        json.JSONDecodeError: If the config file contains invalid JSON.
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

def get_previous_month(month, year, steps_back):
    """
    Calculate the month and year a specified number of months before the given date.

    This function takes a month and year, and calculates the month and year that is
    `steps_back` months prior. It handles year transitions automatically.

    Args:
        month (str): Full month name (e.g., "October").
        year (str): Four-digit year (e.g., "2023").
        steps_back (int): Number of months to go back.

    Returns:
        tuple: (month, year) of the previous month as strings.
    """
    date = datetime.strptime(f"{month} {year}", "%B %Y")
    for _ in range(steps_back):
        date = date.replace(day=1) - timedelta(days=1)  # Move to last day of previous month
    return date.strftime("%B"), date.strftime("%Y")

def fetch_disa_data(config, base_path):
    """
    Fetch DISA data from a URL and save it locally, with fallback to previous months.

    This function attempts to download the DISA ZIP file for the current month. If the
    file is not available, it tries the previous two months. It saves the file in the
    base path and returns the file name.

    Args:
        config (dict): Configuration settings from the config file.
        base_path (str): Base directory path for file operations.

    Returns:
        str: Path to the downloaded DISA file.

    Raises:
        ValueError: If no valid ZIP file is found after trying the current and previous months.
    """
    disa_url_template = config["disa_url"]
    month = datetime.now().strftime('%B')
    year = datetime.now().strftime('%Y')
    
    for i in range(3):
        disa_url = disa_url_template.format(month=month, year=year)
        print(f"Attempting to retrieve file from {disa_url}")
        response = requests.get(disa_url)
        
        if response.status_code == 200 and 'application/zip' in response.headers.get('Content-Type', ''):
            disa_file = disa_url.split('/')[-1]
            with open(disa_file, 'wb') as output_file:
                output_file.write(response.content)
            print(f"Stored {disa_file} in {base_path}")
            return disa_file
        
        month, year = get_previous_month(month, year, 1)
    
    raise ValueError("No valid ZIP file found in the last 3 months")

def fetch_nist_mapping(config, base_path):
    """
    Fetch the NIST 800-53 ATT&CK mapping file if it doesn't exist or is outdated.

    This function checks if the NIST mapping file exists locally and if it is up to date
    by comparing the 'Last-Modified' header of the remote file with the local file's
    modification time. If the local file is missing or outdated, it downloads the remote file.

    Args:
        config (dict): Configuration settings from the config file.
        base_path (str): Base directory path for file operations.

    Returns:
        str: Path to the local NIST mapping file, or None if download fails.
    """
    nist_url = config["nist_800_53_attack_mapping_url"]
    data_folder = os.path.join(base_path, "data")
    nist_file = os.path.join(data_folder, nist_url.split('/')[-1])
    
    # Ensure data folder exists
    os.makedirs(data_folder, exist_ok=True)
    
    # Get remote file's last modified date
    response = requests.head(nist_url)
    if response.status_code != 200:
        print(Fore.RED + f"Error: Could not access {nist_url} (Status: {response.status_code})")
        return None
    
    remote_date_str = response.headers.get('Last-Modified')
    if not remote_date_str:
        print(Fore.YELLOW + "Warning: No Last-Modified header found, attempting download anyway")
        remote_date = datetime.now()
    else:
        remote_date = datetime.strptime(remote_date_str, "%a, %d %b %Y %H:%M:%S GMT")
    
    # Check local file
    should_download = False
    if not os.path.exists(nist_file):
        print(Fore.CYAN + f"No local NIST mapping found at {nist_file}")
        should_download = True
    else:
        local_date = datetime.fromtimestamp(os.path.getmtime(nist_file))
        if remote_date > local_date:
            print(Fore.CYAN + f"Remote NIST file ({remote_date}) is newer than local ({local_date})")
            should_download = True
        else:
            print(Fore.GREEN + f"Local NIST file ({local_date}) is up to date")
    
    # Download if necessary
    if should_download:
        print(f"Downloading NIST mapping from {nist_url}")
        response = requests.get(nist_url)
        if response.status_code == 200:
            with open(nist_file, 'wb') as f:
                f.write(response.content)
            print(Fore.GREEN + f"Stored NIST mapping at {nist_file}")
            # Set the local file's modification time to match the remote file
            if remote_date_str:
                os.utime(nist_file, times=(remote_date.timestamp(), remote_date.timestamp()))
        else:
            print(Fore.RED + f"Failed to download NIST mapping (Status: {response.status_code})")
            return None
    
    return nist_file

def fetch_cci_list(config, base_path):
    """
    Fetch the CCI list ZIP file if it doesn't exist or is outdated, and extract it.

    This function checks the 'Last-Modified' header of the remote CCI list ZIP file
    and compares it with the local '.last_modified' file in the CCI list directory.
    If the remote file is newer or the local file doesn't exist, it downloads and
    extracts the ZIP file to the specified directory.

    Args:
        config (dict): Configuration settings from the config file.
        base_path (str): Base directory path for file operations.

    Returns:
        str: Path to the downloaded CCI ZIP file, or None if no download occurred.
    """
    cci_url = config["cci_list_url"]
    cci_dir = os.path.join(base_path, config["cci_list_dir"])
    last_modified_file = os.path.join(cci_dir, ".last_modified")
    
    # Ensure CCI directory exists
    os.makedirs(cci_dir, exist_ok=True)
    
    # Get remote file's last modified date
    response = requests.head(cci_url)
    if response.status_code != 200:
        print(Fore.RED + f"Error: Could not access {cci_url} (Status: {response.status_code})")
        return None
    
    remote_date_str = response.headers.get('Last-Modified')
    if not remote_date_str:
        print(Fore.YELLOW + "Warning: No Last-Modified header found, attempting download anyway")
        remote_date = datetime.now()
    else:
        remote_date = datetime.strptime(remote_date_str, "%a, %d %b %Y %H:%M:%S GMT")
    
    # Check if .last_modified exists and its modification time
    should_download = False
    if not os.path.exists(last_modified_file):
        print(Fore.CYAN + f"No local CCI list found in {cci_dir}")
        should_download = True
    else:
        local_date = datetime.fromtimestamp(os.path.getmtime(last_modified_file))
        if remote_date > local_date:
            print(Fore.CYAN + f"Remote CCI list ({remote_date}) is newer than local ({local_date})")
            should_download = True
        else:
            print(Fore.GREEN + f"Local CCI list ({local_date}) is up to date")
    
    if should_download:
        # Download the ZIP
        cci_zip_file = os.path.join(base_path, cci_url.split('/')[-1])
        print(f"Downloading CCI list from {cci_url}")
        response = requests.get(cci_url)
        if response.status_code == 200:
            with open(cci_zip_file, 'wb') as f:
                f.write(response.content)
            print(Fore.GREEN + f"Stored CCI list ZIP at {cci_zip_file}")
            
            # Extract the ZIP to cci_dir
            with zipfile.ZipFile(cci_zip_file, 'r') as zip_ref:
                zip_ref.extractall(cci_dir)
            print(Fore.MAGENTA + f"Extracted CCI list to {cci_dir}")
            
            # Create or update .last_modified file
            with open(last_modified_file, 'w') as f:
                f.write(remote_date_str or str(datetime.now()))
            # Set the modification time
            if remote_date_str:
                os.utime(last_modified_file, times=(remote_date.timestamp(), remote_date.timestamp()))
            else:
                os.utime(last_modified_file)
        else:
            print(Fore.RED + f"Failed to download CCI list (Status: {response.status_code})")
            return None
    else:
        cci_zip_file = None  # No download occurred
    
    return cci_zip_file

def extract_and_sort_files(config, disa_file, base_path):
    """
    Extract the DISA ZIP file and sort contents into SRG and STIG directories.

    This function extracts the contents of the DISA ZIP file into a temporary directory,
    then moves SRG and STIG ZIP files into their respective directories. It further extracts
    these ZIP files and moves the XML files to the root of their directories.

    Args:
        config (dict): Configuration settings from the config file.
        disa_file (str): Path to the downloaded DISA ZIP file.
        base_path (str): Base directory path for file operations.
    """
    file_location = os.path.join(base_path, config["file_imports_dir"]) + '/'
    srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
    stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

    # Extract files from the DISA ZIP
    print(Fore.MAGENTA + f"Extracting files to: {file_location}")
    with zipfile.ZipFile(disa_file, 'r') as zObject:
        zObject.extractall(path=file_location)

    # Sort SRGs and STIGs into respective folders
    print(Fore.CYAN + f"Checking for SRGs and STIGs in: {file_location}")
    files = os.listdir(file_location)
    for f in files:
        if f.endswith(config["srg_zip_suffix"]):
            print(Fore.CYAN + f"Moving {f} to {srg_folder}")
            shutil.move(file_location + f, srg_folder + f)
        elif f.endswith(config["zip_suffix"]):
            print(Fore.CYAN + f"Moving {f} to {stig_folder}")
            shutil.move(file_location + f, stig_folder + f)

    # Extract nested ZIPs and move XML files
    for folder, suffix in [(srg_folder, "SRG"), (stig_folder, "STIG")]:
        for item in os.listdir(folder):
            if not item.endswith(config["zip_suffix"]):
                continue
            file_name = os.path.abspath(folder + item)
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                zip_ref.extractall(folder)
            os.remove(file_name)  # Remove the nested ZIP after extraction

        # Move XML files to the root of the folder
        for subdir, _, files in os.walk(folder):
            for f in files:
                if f.endswith(config["xml_suffix"]):
                    print(Fore.LIGHTYELLOW_EX + f"Moving {f} to {folder}")
                    shutil.move(os.path.join(subdir, f), folder + f)

def clean_up_files(config, disa_file, cci_zip_file, base_path):
    """
    Remove temporary files and directories, keeping only XML files and extracted CCI list.

    This function removes the downloaded DISA and CCI ZIP files and cleans up the SRG and STIG
    directories by deleting any non-XML files and empty directories.

    Args:
        config (dict): Configuration settings from the config file.
        disa_file (str): Path to the downloaded DISA ZIP file.
        cci_zip_file (str): Path to the downloaded CCI ZIP file.
        base_path (str): Base directory path for file operations.
    """
    srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
    stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

    # Remove the downloaded DISA ZIP file
    if disa_file and os.path.exists(disa_file):
        os.remove(disa_file)
        print(Fore.RED + f"Removed {disa_file} from {base_path}")

    # Remove the downloaded CCI ZIP file
    if cci_zip_file and os.path.exists(cci_zip_file):
        os.remove(cci_zip_file)
        print(Fore.RED + f"Removed {cci_zip_file} from {base_path}")

    # Clean up non-XML files and empty directories in SRG and STIG folders
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
    """
    Main function to fetch, extract, and clean DISA data, NIST mapping, and CCI list.

    This function orchestrates the entire process:
    1. Loads configuration settings.
    2. Creates necessary directories.
    3. Fetches DISA data, NIST mapping, and CCI list files.
    4. Extracts and sorts DISA files.
    5. Cleans up temporary files.

    Guide for Developers:
        - Modify 'config.json' to change URLs, directories, or file suffixes.
        - Ensure required directories exist and have write permissions.
        - Dependencies: requests, colorama (see requirements.txt).
        - Runs in the current working directory; adjust paths if needed.
    """
    base_path = os.getcwd()
    config = load_config()

    # Create required directories if they don't exist
    for dir_key in ["file_imports_dir", "srg_dir", "stig_dir", "cci_list_dir"]:
        os.makedirs(os.path.join(base_path, config[dir_key]), exist_ok=True)

    # Execute the workflow
    disa_file = fetch_disa_data(config, base_path)
    nist_file = fetch_nist_mapping(config, base_path)
    cci_zip_file = fetch_cci_list(config, base_path)
    extract_and_sort_files(config, disa_file, base_path)
    clean_up_files(config, disa_file, cci_zip_file, base_path)
    print(Style.RESET_ALL)

if __name__ == "__main__":
    main()
