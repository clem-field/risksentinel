import os
import json
import requests
from datetime import datetime, timedelta
import shutil
from email.utils import parsedate_to_datetime
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_file(url, destination):
    """Download a file from a URL to a destination path if it exists.

    Args:
        url (str): The URL to download the file from.
        destination (str): The local path where the file will be saved.

    Returns:
        bool: True if the download was successful, False otherwise.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request fails.
    """
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
    """Unzip a file to a specified directory.

    Args:
        zip_path (str): The path to the zip file to be extracted.
        extract_dir (str): The directory where the contents will be extracted.

    Returns:
        str: The path to the extraction directory.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return extract_dir

def get_latest_available_zip_info(base_url, max_months_back=12):
    """Find the latest available zip file by checking recent months.

    Args:
        base_url (str): The base URL template with {month} and {year} placeholders.
        max_months_back (int, optional): Maximum months to look back. Defaults to 12.

    Returns:
        tuple: (url, filename, (year, month_num)) if found, (None, None, None) otherwise.
    """
    current_date = datetime.now()
    for i in range(max_months_back):
        check_date = current_date - timedelta(days=30 * i)
        month_name = check_date.strftime("%B")  # e.g., "October"
        year = check_date.year
        url = base_url.format(month=month_name, year=year)
        try:
            response = requests.head(url)
            if response.status_code == 200:
                month_num = check_date.month  # e.g., 10 for October
                filename = f"U_SRG-STIG_Library_{month_name}_{year}.zip"
                return url, filename, (year, month_num)
        except requests.exceptions.RequestException:
            continue
    return None, None, None

def get_last_modified_date(url):
    """Retrieve the Last-Modified date from the HTTP header of a URL.

    Args:
        url (str): The URL to check for the Last-Modified header.

    Returns:
        datetime: The last modified date if available, None otherwise.
    """
    try:
        response = requests.head(url)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            return parsedate_to_datetime(last_modified)
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error checking Last-Modified for {url}: {e}")
        return None

def download_parallel(urls_destinations):
    """Download multiple files in parallel using up to 4 concurrent threads.

    Args:
        urls_destinations (list of tuples): List of (url, destination) pairs to download.

    Returns:
        list: List of tuples (url, dest, success) indicating success/failure for each download.
    """
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_url = {executor.submit(download_file, url, dest): (url, dest) for url, dest in urls_destinations}
        for future in as_completed(future_to_url):
            url, dest = future_to_url[future]
            try:
                result = future.result()
                results.append((url, dest, result))
            except Exception as e:
                print(f"Download of {url} generated an exception: {e}")
                results.append((url, dest, False))
    return results

def fetch_data(config_path):
    """Fetch data files based on config.json and save to appropriate directories.

    Args:
        config_path (str): Path to the configuration JSON file.

    This function handles downloading NIST mappings, baselines, catalogs, CCI lists,
    and the latest STIG/SRG libraries, using parallel downloads where applicable.
    """
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Define directory paths
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

    # Load or initialize last processed data
    last_processed_file = os.path.join(data_dir, "last_processed.json")
    if os.path.exists(last_processed_file):
        with open(last_processed_file, 'r') as f:
            last_processed = json.load(f)
            disa_last_processed = tuple(last_processed.get("disa_zip", [0, 0]))
            nist_mapping_last_modified = datetime.fromisoformat(last_processed.get("nist_mapping", "1970-01-01T00:00:00Z"))
    else:
        disa_last_processed = (0, 0)
        nist_mapping_last_modified = datetime(1970, 1, 1)

    # Prepare parallel downloads
    download_tasks = []

    # Download NIST 800-53 attack mapping
    mapping_url = config["nist_800_53_attack_mapping_url"]
    mapping_filename = mapping_url.split('/')[-1]
    mapping_dest = os.path.join(data_dir, mapping_filename)
    current_mapping_modified = get_last_modified_date(mapping_url)
    if current_mapping_modified and current_mapping_modified > nist_mapping_last_modified:
        download_tasks.append((mapping_url, mapping_dest))
    elif not current_mapping_modified:
        download_tasks.append((mapping_url, mapping_dest))

    # Download NIST baselines
    for level, url in config["baselines"].items():
        filename = url.split('/')[-1]
        dest_path = os.path.join(data_dir, filename)
        download_tasks.append((url, dest_path))

    # Download NIST SP 800-53 catalog
    catalog_url = config["nist_sp800_53_catalog_url"]
    catalog_filename = catalog_url.split('/')[-1]
    catalog_dest = os.path.join(data_dir, catalog_filename)
    download_tasks.append((catalog_url, catalog_dest))

    # Execute parallel downloads
    if download_tasks:
        results = download_parallel(download_tasks)
        for url, dest, success in results:
            if url == mapping_url and success and current_mapping_modified and current_mapping_modified > nist_mapping_last_modified:
                nist_mapping_last_modified = current_mapping_modified
            elif url == mapping_url and not success:
                print(f"Failed to update {mapping_filename} despite newer modification date.")
            elif url == mapping_url:
                print(f"{mapping_filename} is up to date with modification date {current_mapping_modified}.")

    # Download CCI list
    cci_url = config["cci_list_url"]
    cci_zip = os.path.join(cci_list_dir, "U_CCI_List.zip")
    if download_file(cci_url, cci_zip):
        unzip_file(cci_zip, cci_list_dir)
        os.remove(cci_zip)  # Clean up the zip file

    # Handle STIGs and SRGs
    base_url = config["disa_url"]
    latest_url, latest_filename, latest_date = get_latest_available_zip_info(base_url)
    if latest_url is None:
        print("No recent STIG/SRG library found; skipping STIG/SRG processing.")
    else:
        if latest_date > disa_last_processed:
            dest_path = os.path.join(stig_zips_dir, latest_filename)
            if download_file(latest_url, dest_path):
                try:
                    # Unzip and process
                    temp_extract_dir = os.path.join(stig_zips_dir, "temp_extract")
                    os.makedirs(temp_extract_dir, exist_ok=True)
                    unzip_file(dest_path, temp_extract_dir)
                    
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
                    
                    # Update disa_last_processed
                    disa_last_processed = latest_date
                except Exception as e:
                    print(f"Error processing {latest_filename}: {e}")
            else:
                print(f"Failed to download {latest_filename}")
        else:
            print(f"Latest STIG/SRG library {latest_filename} is already processed; skipping.")

    # Update last_processed.json with the current timestamp and updated values
    with open(last_processed_file, 'w') as f:
        last_processed = {
            "disa_zip": list(disa_last_processed),
            "nist_mapping": nist_mapping_last_modified.isoformat() + "Z",
            "last_updated": datetime.now().isoformat()  # Add last_updated timestamp
        }
        json.dump(last_processed, f)
    print("Data fetch completed. last_processed.json updated.")

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    fetch_data(config_path)