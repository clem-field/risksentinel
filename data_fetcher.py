import os
import requests
import shutil
import zipfile
import json
from colorama import Fore, Style
from datetime import datetime, timedelta
import logging

# Configure logging to overwrite the log file each time
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'debug.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'  # Overwrite the log file each time
)

def load_config(config_file="config.json"):
    """
    Load configuration settings from a JSON file.
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
    """
    date = datetime.strptime(f"{month} {year}", "%B %Y")
    for _ in range(steps_back):
        date = date.replace(day=1) - timedelta(days=1)
    return date.strftime("%B"), date.strftime("%Y")

def fetch_disa_data(config, base_path):
    """
    Fetch DISA STIG ZIP data, checking if the local file is up to date before downloading.
    """
    disa_url_template = config["disa_url"]
    stig_zip_dir = os.path.join(base_path, "data", "stig_zips")
    os.makedirs(stig_zip_dir, exist_ok=True)
    
    current_month = datetime.now().strftime('%B')
    current_year = datetime.now().strftime('%Y')
    
    for i in range(3):  # Check current and previous two months
        month, year = get_previous_month(current_month, current_year, i)
        disa_url = disa_url_template.format(month=month, year=year)
        disa_file_name = f"U_SRG-STIG_Library_{month}_{year}.zip"
        local_file_path = os.path.join(stig_zip_dir, disa_file_name)
        
        # Check if the local file exists and is up to date
        response = requests.head(disa_url)
        if response.status_code == 200:
            remote_date_str = response.headers.get('Last-Modified')
            if remote_date_str:
                remote_date = datetime.strptime(remote_date_str, "%a, %d %b %Y %H:%M:%S GMT")
                if os.path.exists(local_file_path):
                    local_date = datetime.fromtimestamp(os.path.getmtime(local_file_path))
                    if local_date >= remote_date:
                        print(Fore.GREEN + f"Local STIG ZIP for {month} {year} is up to date.")
                        return local_file_path
                # If local file is outdated or doesn't exist, download it
                print(Fore.CYAN + f"Downloading STIG ZIP for {month} {year}...")
                response = requests.get(disa_url)
                if response.status_code == 200:
                    with open(local_file_path, 'wb') as output_file:
                        output_file.write(response.content)
                    # Set the local file's modification time to match the server's 'Last-Modified' time
                    os.utime(local_file_path, (remote_date.timestamp(), remote_date.timestamp()))
                    print(Fore.GREEN + f"Stored {disa_file_name} in {stig_zip_dir}")
                    return local_file_path
                else:
                    print(Fore.RED + f"Failed to download STIG ZIP for {month} {year} (Status: {response.status_code})")
            else:
                print(Fore.YELLOW + f"No Last-Modified header for {disa_url}, downloading anyway...")
                response = requests.get(disa_url)
                if response.status_code == 200:
                    with open(local_file_path, 'wb') as output_file:
                        output_file.write(response.content)
                    print(Fore.GREEN + f"Stored {disa_file_name} in {stig_zip_dir}")
                    return local_file_path
                else:
                    print(Fore.RED + f"Failed to download STIG ZIP for {month} {year} (Status: {response.status_code})")
        else:
            print(Fore.YELLOW + f"STIG ZIP for {month} {year} not found (Status: {response.status_code}), checking previous month...")
    
    raise ValueError("No valid STIG ZIP file found in the last 3 months")

def fetch_file(url, base_path, file_desc):
    """
    Fetch a file if it doesn’t exist locally or is outdated, with descriptive messages.
    """
    data_folder = os.path.join(base_path, "data")
    os.makedirs(data_folder, exist_ok=True)
    local_file = os.path.join(data_folder, url.split('/')[-1])
    
    response = requests.head(url)
    if response.status_code != 200:
        print(Fore.RED + f"Error: Could not access {url} for {file_desc} (Status: {response.status_code})")
        return None
    
    remote_date_str = response.headers.get('Last-Modified')
    remote_date = datetime.strptime(remote_date_str, "%a, %d %b %Y %H:%M:%S GMT") if remote_date_str else datetime.now()
    
    should_download = False
    if not os.path.exists(local_file):
        print(Fore.CYAN + f"No local {file_desc} found at {local_file}")
        should_download = True
    else:
        local_date = datetime.fromtimestamp(os.path.getmtime(local_file))
        if remote_date > local_date:
            print(Fore.CYAN + f"Remote {file_desc} ({remote_date}) is newer than local ({local_date})")
            should_download = True
        else:
            print(Fore.GREEN + f"Local {file_desc} ({local_date}) is up to date")
    
    if should_download:
        print(f"Downloading {file_desc} from {url}")
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_file, 'wb') as f:
                f.write(response.content)
            print(Fore.GREEN + f"Stored {file_desc} at {local_file}")
            if remote_date_str:
                os.utime(local_file, (remote_date.timestamp(), remote_date.timestamp()))
        else:
            print(Fore.RED + f"Failed to download {file_desc} (Status: {response.status_code})")
            return None
    return local_file

def fetch_cci_list(config, base_path):
    """
    Fetch the CCI list ZIP file if it doesn’t exist or is outdated, and extract it.
    """
    cci_url = config["cci_list_url"]
    cci_dir = os.path.join(base_path, config["cci_list_dir"])
    last_modified_file = os.path.join(cci_dir, ".last_modified")
    
    os.makedirs(cci_dir, exist_ok=True)
    
    response = requests.head(cci_url)
    if response.status_code != 200:
        print(Fore.RED + f"Error: Could not access {cci_url} (Status: {response.status_code})")
        return None
    
    remote_date_str = response.headers.get('Last-Modified')
    remote_date = datetime.strptime(remote_date_str, "%a, %d %b %Y %H:%M:%S GMT") if remote_date_str else datetime.now()
    
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
        cci_zip_file = os.path.join(base_path, "data", "cci_list.zip")
        print(f"Downloading CCI list from {cci_url}")
        response = requests.get(cci_url)
        if response.status_code == 200:
            with open(cci_zip_file, 'wb') as f:
                f.write(response.content)
            print(Fore.GREEN + f"Stored CCI list ZIP at {cci_zip_file}")
            with zipfile.ZipFile(cci_zip_file, 'r') as zip_ref:
                zip_ref.extractall(cci_dir)
            print(Fore.MAGENTA + f"Extracted CCI list to {cci_dir}")
            with open(last_modified_file, 'w') as f:
                f.write(remote_date_str or str(datetime.now()))
            if remote_date_str:
                os.utime(last_modified_file, (remote_date.timestamp(), remote_date.timestamp()))
        else:
            print(Fore.RED + f"Failed to download CCI list (Status: {response.status_code})")
            return None
    else:
        cci_zip_file = None
    return cci_zip_file

def extract_and_sort_files(config, disa_file, base_path):
    """
    Extract the DISA ZIP file and sort contents into SRG and STIG directories.
    """
    file_location = os.path.join(base_path, config["file_imports_dir"])
    srg_folder = os.path.join(base_path, config["srg_dir"])
    stig_folder = os.path.join(base_path, config["stig_dir"])

    with zipfile.ZipFile(disa_file, 'r') as zObject:
        zObject.extractall(path=file_location)

    files = os.listdir(file_location)
    for f in files:
        if f.endswith(config["srg_zip_suffix"]):
            shutil.move(os.path.join(file_location, f), os.path.join(srg_folder, f))
        elif f.endswith(config["zip_suffix"]):
            shutil.move(os.path.join(file_location, f), os.path.join(stig_folder, f))

    srg_xml_moved = 0
    stig_xml_moved = 0

    for folder in [srg_folder, stig_folder]:
        for item in os.listdir(folder):
            if not item.endswith(config["zip_suffix"]):
                continue
            file_name = os.path.join(folder, item)
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                zip_ref.extractall(folder)
            os.remove(file_name)

        for subdir, _, files in os.walk(folder):
            for f in files:
                if f.endswith(config["xml_suffix"]):
                    shutil.move(os.path.join(subdir, f), os.path.join(folder, f))
                    if folder == srg_folder:
                        srg_xml_moved += 1
                    else:
                        stig_xml_moved += 1

    return srg_xml_moved, stig_xml_moved

def clean_up_files(config, cci_zip_file, base_path):
    """
    Remove temporary files and directories, keeping only XML files and extracted CCI list.
    Note: STIG ZIP files are no longer deleted here to allow reuse.
    """
    srg_folder = os.path.join(base_path, config["srg_dir"])
    stig_folder = os.path.join(base_path, config["stig_dir"])

    # Remove the downloaded CCI ZIP file if it exists
    if cci_zip_file and os.path.exists(cci_zip_file):
        logging.debug(f"Removing {cci_zip_file}")
        os.remove(cci_zip_file)

    srg_files_deleted = 0
    srg_dirs_deleted = 0
    stig_files_deleted = 0
    stig_dirs_deleted = 0

    for folder in [srg_folder, stig_folder]:
        for subdir, dirs, files in os.walk(folder):
            for f in files:
                if not f.endswith(config["xml_suffix"]):
                    file_path = os.path.join(subdir, f)
                    logging.debug(f"Deleting {file_path}")
                    os.remove(file_path)
                    if folder == srg_folder:
                        srg_files_deleted += 1
                    else:
                        stig_files_deleted += 1

        for root, dirs, _ in os.walk(folder, topdown=False):
            for directory in dirs:
                dirpath = os.path.join(root, directory)
                if not os.listdir(dirpath):
                    logging.debug(f"Deleting directory: {dirpath}")
                    os.rmdir(dirpath)
                    if folder == srg_folder:
                        srg_dirs_deleted += 1
                    else:
                        stig_dirs_deleted += 1

    return srg_files_deleted, srg_dirs_deleted, stig_files_deleted, stig_dirs_deleted

def cleanup_old_stig_zips(base_path):
    """
    Remove STIG ZIP files older than 120 days to manage storage.
    """
    stig_zip_dir = os.path.join(base_path, "data", "stig_zips")
    max_age_days = 120
    now = datetime.now()
    cutoff_time = (now - timedelta(days=max_age_days)).timestamp()

    for file in os.listdir(stig_zip_dir):
        file_path = os.path.join(stig_zip_dir, file)
        if os.path.isfile(file_path):
            mod_time = os.path.getmtime(file_path)
            if mod_time < cutoff_time:
                os.remove(file_path)
                logging.debug(f"Deleted old STIG ZIP file: {file_path}")

def main():
    """
    Main function to fetch, extract, and clean DISA data, NIST mapping, baselines, catalog, and CCI list.
    """
    base_path = os.getcwd()
    config = load_config()

    for dir_key in ["file_imports_dir", "srg_dir", "stig_dir", "cci_list_dir"]:
        os.makedirs(os.path.join(base_path, config[dir_key]), exist_ok=True)

    disa_file = fetch_disa_data(config, base_path)
    
    # Fetch NIST 800-53 attack mapping
    fetch_file(config["nist_800_53_attack_mapping_url"], base_path, "NIST 800-53 ATT&CK mapping")
    
    # Fetch baselines
    for level, url in config["baselines"].items():
        fetch_file(url, base_path, f"{level} baseline")
    
    # Fetch NIST SP 800-53 control catalog
    fetch_file(config["nist_sp800_53_catalog_url"], base_path, "NIST SP 800-53 control catalog")
    
    cci_zip_file = fetch_cci_list(config, base_path)
    srg_xml_moved, stig_xml_moved = extract_and_sort_files(config, disa_file, base_path)
    srg_files_deleted, srg_dirs_deleted, stig_files_deleted, stig_dirs_deleted = clean_up_files(
        config, cci_zip_file, base_path
    )
    
    # Clean up old STIG ZIP files older than 120 days
    cleanup_old_stig_zips(base_path)

    print(Fore.GREEN + "Summary:")
    print(f" - Moved {srg_xml_moved} XML files to SRG directory")
    print(f" - Moved {stig_xml_moved} XML files to STIG directory")
    print(f" - Deleted {srg_files_deleted} files from SRG directory")
    print(f" - Deleted {stig_files_deleted} files from STIG directory")
    print(f" - Deleted {srg_dirs_deleted} directories from SRG directory")
    print(f" - Deleted {stig_dirs_deleted} directories from STIG directory")
    print(Style.RESET_ALL)

if __name__ == "__main__":
    main()
