import os
import json
import requests
from datetime import datetime, timedelta
import shutil
from email.utils import parsedate_to_datetime
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz  # For timezone handling

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

def get_latest_available_zip_info(base_url, max_months_back=12):
    """Find the latest available zip file by checking recent months."""
    current_date = datetime.now()
    for i in range(max_months_back):
        check_date = current_date - timedelta(days=30 * i)
        month_name = check_date.strftime("%B")
        year = check_date.year
        url = base_url.format(month=month_name, year=year)
        try:
            response = requests.head(url)
            if response.status_code == 200:
                month_num = check_date.month
                filename = f"U_SRG-STIG_Library_{month_name}_{year}.zip"
                return url, filename, (year, month_num)
        except requests.exceptions.RequestException:
            continue
    return None, None, None

def get_last_modified_date(url):
    """Retrieve the Last-Modified date from the HTTP header of a URL."""
    try:
        response = requests.head(url)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            return parsedate_to_datetime(last_modified)  # Returns offset-aware datetime
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error checking Last-Modified for {url}: {e}")
        return None

def download_parallel(urls_destinations):
    """Download multiple files in parallel using up to 4 concurrent threads."""
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
    """Fetch data files based on config.json and save to appropriate directories."""
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

    # Load or initialize last processed data with UTC timezone
    utc = pytz.UTC
    last_processed_file = os.path.join(data_dir, "last_processed.json")
    if os.path.exists(last_processed_file):
        with open(last_processed_file, 'r') as f:
            last_processed = json.load(f)
            disa_last_processed = tuple(last_processed.get("disa_zip", [0, 0]))
            nist_mapping_last_modified_str = last_processed.get("nist_mapping", "1970-01-01T00:00:00Z")
            dt = datetime.fromisoformat(nist_mapping_last_modified_str.rstrip("Z"))  # Parse without assuming Z
            if dt.tzinfo is None:  # If naive, localize to UTC
                nist_mapping_last_modified = utc.localize(dt)
            else:  # If aware, convert to UTC
                nist_mapping_last_modified = dt.astimezone(utc)
    else:
        disa_last_processed = (0, 0)
        nist_mapping_last_modified = utc.localize(datetime(1970, 1, 1))  # Make initial datetime UTC-aware

    # Prepare parallel downloads
    download_tasks = []

    # Download NIST 800-53 attack mapping
    framework = config.get("framework")
    if not framework:
        raise ValueError("No 'framework' specified in config.")
    attack_mapping_urls = config.get("attack_mapping_urls", {})
    if framework not in attack_mapping_urls:
        raise KeyError(f"No attack mapping URL found for framework '{framework}' in 'attack_mapping_urls'.")
    mapping_url = attack_mapping_urls[framework]
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
                with open(last_processed_file, 'w') as f:
                    last_processed = {
                        "disa_zip": list(disa_last_processed),
                        "nist_mapping": current_mapping_modified.isoformat()  # Already offset-aware, includes UTC offset
                    }
                    json.dump(last_processed, f)
                print(f"Updated {mapping_filename} based on new modification date.")
            elif url == mapping_url and not success:
                print(f"Failed to update {mapping_filename} despite newer modification date.")
            elif url == mapping_url:
                print(f"{mapping_filename} is up to date with modification date {current_mapping_modified}.")

    # Download CCI list
    cci_url = config["cci_list_url"]
    cci_zip = os.path.join(cci_list_dir, "U_CCI_List.zip")
    if download_file(cci_url, cci_zip):
        unzip_file(cci_zip, cci_list_dir)
        os.remove(cci_zip)

    # Handle STIGs and SRGs
    base_url = config["disa_url"]
    latest_url, latest_filename, latest_date = get_latest_available_zip_info(base_url)
    if latest_url is None:
        print("No recent STIG/SRG library found; skipping STIG/SRG processing.")
        return

    if latest_date > disa_last_processed:
        dest_path = os.path.join(stig_zips_dir, latest_filename)
        if download_file(latest_url, dest_path):
            try:
                temp_extract_dir = os.path.join(stig_zips_dir, "temp_extract")
                os.makedirs(temp_extract_dir, exist_ok=True)
                unzip_file(dest_path, temp_extract_dir)
                
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
                
                shutil.rmtree(temp_extract_dir)
                
                with open(last_processed_file, 'w') as f:
                    last_processed = {
                        "disa_zip": list(latest_date),
                        "nist_mapping": nist_mapping_last_modified.isoformat()  # Keep UTC-aware format
                    }
                    json.dump(last_processed, f)
                print(f"Successfully processed {latest_filename}")
            except Exception as e:
                print(f"Error processing {latest_filename}: {e}")
        else:
            print(f"Failed to download {latest_filename}")
    else:
        print(f"Latest STIG/SRG library {latest_filename} is already processed; skipping.")

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    fetch_data(config_path)
