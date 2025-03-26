# THIS CODE IS DEPRECATED REFER TO THE DATA_FETCHER.PY IN THE MODULES DIRECTORY

import os
import json
import requests
import zipfile
from datetime import datetime, timedelta
import shutil

def download_file(url, destination):
    """Download a file from a URL to a destination path if it exists."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded {os.path.basename(destination)} successfully.")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"Failed to download {url}: {e}")
        return False

def unzip_file(zip_path, extract_dir):
    """Unzip a file to a specified directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return extract_dir

def get_file_mod_time(filepath):
    """Get the modification time of a file."""
    return datetime.fromtimestamp(os.path.getmtime(filepath))

def prune_old_files(directory, days=120):
    """Remove files older than the specified number of days."""
    cutoff = datetime.now() - timedelta(days=days)
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and get_file_mod_time(file_path) < cutoff:
            os.remove(file_path)
            print(f"Removed old file: {filename}")

def find_latest_stig_zip(base_url, stig_zips_dir):
    """Find the latest available STIG/SRG zip by checking recent months."""
    current_date = datetime.now()
    for i in range(3):  # Check current and past 2 months
        check_date = current_date - timedelta(days=30 * i)
        filename = f"U_SRG-STIG_Library_{check_date.strftime('%B')}_{check_date.year}.zip"
        url = base_url.format(month=check_date.strftime("%B"), year=check_date.year)
        dest_path = os.path.join(stig_zips_dir, filename)
        if download_file(url, dest_path):
            return dest_path
    return None

def fetch_data(config_path):
    """Fetch data files based on config.json and save to appropriate directories."""
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)

    root_dir = os.path.dirname(os.path.abspath(config_path))
    data_dir = os.path.join(root_dir, "data")
    cci_list_dir = os.path.join(root_dir, config["cci_list_dir"])
    stig_zips_dir = os.path.join(data_dir, "stig_zips")
    srg_dir = os.path.join(root_dir, config["srg_dir"])
    stig_dir = os.path.join(root_dir, config["stig_dir"])

    # Create directories if they don’t exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(cci_list_dir, exist_ok=True)
    os.makedirs(stig_zips_dir, exist_ok=True)
    os.makedirs(srg_dir, exist_ok=True)
    os.makedirs(stig_dir, exist_ok=True)

    # Download NIST baselines
    for level, url in config["baselines"].items():
        filename = url.split('/')[-1]
        dest_path = os.path.join(data_dir, filename)
        print(f"Downloading {filename}...")
        download_file(url, dest_path)

    # Download NIST SP 800-53 catalog
    catalog_url = config["nist_sp800_53_catalog_url"]
    catalog_filename = catalog_url.split('/')[-1]
    catalog_dest = os.path.join(data_dir, catalog_filename)
    print(f"Downloading {catalog_filename}...")
    download_file(catalog_url, catalog_dest)

    # Download CCI list
    cci_url = config["cci_list_url"]
    cci_zip = os.path.join(cci_list_dir, "U_CCI_List.zip")
    print(f"Downloading CCI list...")
    if download_file(cci_url, cci_zip):
        unzip_file(cci_zip, cci_list_dir)
        os.remove(cci_zip)  # Clean up the zip file

    # Download STIGs and SRGs from DISA URL
    stig_zip_path = find_latest_stig_zip(config["disa_url"], stig_zips_dir)
    if stig_zip_path:
        # Check if the file is recent enough (30 days)
        if os.path.exists(stig_zip_path) and (datetime.now() - get_file_mod_time(stig_zip_path)).days < 30:
            print(f"{os.path.basename(stig_zip_path)} is recent enough; skipping further processing.")
        else:
            # Prune files older than 120 days in stig_zips_dir
            print(f"Pruning files older than 120 days in {stig_zips_dir}...")
            prune_old_files(stig_zips_dir)

            # Unzip and process STIG/SRG files
            temp_extract_dir = os.path.join(stig_zips_dir, "temp_extract")
            os.makedirs(temp_extract_dir, exist_ok=True)
            unzip_file(stig_zip_path, temp_extract_dir)

            # Move XML files to appropriate directories
            for root, _, files in os.walk(temp_extract_dir):
                for file in files:
                    if file.endswith(config["xml_suffix"]):
                        src_path = os.path.join(root, file)
                        if config["srg_zip_suffix"].replace(".zip", "") in file:
                            dest_path = os.path.join(srg_dir, file)
                        else:
                            dest_path = os.path.join(stig_dir, file)
                        shutil.move(src_path, dest_path)
                        print(f"Moved {file} to {dest_path}")

            # Clean up temporary extraction directory
            shutil.rmtree(temp_extract_dir)
            print(f"Cleaned up temporary extraction directory: {temp_extract_dir}")
    else:
        print("No recent STIG/SRG library found; skipping STIG/SRG processing.")

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    fetch_data(config_path)
