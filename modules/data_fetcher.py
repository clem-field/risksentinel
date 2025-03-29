import os
import json
import requests
import tempfile
import shutil
from datetime import datetime, timedelta
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
import pytz
import logging

# Configure logging
logging.basicConfig(
    filename='data_fetcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def download_file(url, destination):
    """Download a file from a URL to a destination path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded {os.path.basename(destination)} successfully.")
        print(f"Downloaded {os.path.basename(destination)} successfully.")
        return True
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to download {url}: {e}")
        print(f"Failed to download {url}: {e}")
        return False

def unzip_file(zip_path, extract_dir):
    """Unzip a file to a specified directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        logging.info(f"Unzipped {zip_path} to {extract_dir}")
        return extract_dir
    except zipfile.BadZipFile as e:
        logging.error(f"Failed to unzip {zip_path}: {e}")
        raise

def get_latest_available_zip_info(base_url, max_months_back=12):
    """Find the latest available STIG/SRG zip file by checking recent months."""
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
                logging.info(f"Found latest STIG/SRG zip: {filename}")
                return url, filename, (year, month_num)
        except requests.exceptions.RequestException:
            continue
    logging.warning("No recent STIG/SRG library found within the last 12 months.")
    return None, None, None

def get_last_modified_date(url):
    """Retrieve the Last-Modified date from the HTTP header of a URL."""
    try:
        response = requests.head(url)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            return parsedate_to_datetime(last_modified)  # Offset-aware datetime
        logging.warning(f"No Last-Modified header for {url}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking Last-Modified for {url}: {e}")
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
                logging.error(f"Download of {url} generated an exception: {e}")
                results.append((url, dest, False))
    return results

def write_last_processed(last_processed_file, data):
    """Write JSON data to a file atomically to prevent corruption."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', dir=os.path.dirname(last_processed_file))
    try:
        json.dump(data, temp_file, indent=2)  # Human-readable format
        temp_file.close()
        shutil.move(temp_file.name, last_processed_file)  # Atomic replace
        logging.info(f"Updated {last_processed_file} safely.")
    except Exception as e:
        os.unlink(temp_file.name)  # Clean up on error
        logging.error(f"Failed to write {last_processed_file}: {e}")
        raise

def extract_nested_zips(zip_path, base_extract_dir, stig_dir, srg_dir, docs_dir):
    """Recursively extract zip files and move XMLs to stig_dir/srg_dir, PDFs to docs_dir."""
    temp_extract_dir = os.path.join(base_extract_dir, f"extract_{os.path.basename(zip_path)}")
    os.makedirs(temp_extract_dir, exist_ok=True)
    unzip_file(zip_path, temp_extract_dir)

    for root, _, files in os.walk(temp_extract_dir):
        for file in files:
            src_path = os.path.join(root, file)
            if file.endswith('.zip'):
                # Recursively extract nested zips
                extract_nested_zips(src_path, base_extract_dir, stig_dir, srg_dir, docs_dir)
            elif file.endswith('.xml'):
                # Move XML files based on parent zip name
                parent_zip = os.path.basename(zip_path).upper()
                dest_dir = srg_dir if "_SRG" in parent_zip else stig_dir
                dest_path = os.path.join(dest_dir, file)
                shutil.move(src_path, dest_path)
                logging.info(f"Moved {file} to {dest_path}")
            elif file.endswith('.pdf') and file.startswith('_'):
                # Move underscore-prefixed PDFs to docs_dir
                dest_path = os.path.join(docs_dir, file)
                shutil.move(src_path, dest_path)
                logging.info(f"Moved {file} to {dest_path}")

    # Clean up temporary extraction directory
    shutil.rmtree(temp_extract_dir, ignore_errors=True)

def fetch_data(config_path):
    """Fetch data files based on config.json and save to appropriate directories."""
    # Load config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logging.info("Loaded config successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load config: {e}")
        raise

    # Define directory paths
    root_dir = os.path.dirname(os.path.abspath(config_path))
    data_dir = os.path.join(root_dir, "data")
    docs_dir = os.path.join(data_dir, "docs")
    cci_list_dir = os.path.join(root_dir, config["cci_list_dir"])
    stig_zips_dir = os.path.join(data_dir, "stig_zips")
    srg_dir = os.path.join(root_dir, config["srg_dir"])
    stig_dir = os.path.join(root_dir, config["stig_dir"])

    # Create directories if they don’t exist
    for directory in [data_dir, docs_dir, cci_list_dir, stig_zips_dir, srg_dir, stig_dir]:
        os.makedirs(directory, exist_ok=True)
        logging.debug(f"Ensured directory exists: {directory}")

    # Load or initialize last processed data
    utc = pytz.UTC
    last_processed_file = os.path.join(data_dir, "last_processed.json")
    default_last_processed = {
        "last_updated": utc.localize(datetime(1970, 1, 1)).isoformat()
    }
    if os.path.exists(last_processed_file):
        try:
            with open(last_processed_file, 'r') as f:
                last_processed = json.load(f)
            last_updated_str = last_processed.get("last_updated", "1970-01-01T00:00:00Z")
            dt = datetime.fromisoformat(last_updated_str.rstrip("Z"))
            last_updated = utc.localize(dt) if dt.tzinfo is None else dt.astimezone(utc)
            logging.info(f"Loaded existing {last_processed_file}")
        except (json.JSONDecodeError, ValueError) as e:
            logging.warning(f"Corrupted {last_processed_file}: {e}. Initializing with defaults.")
            last_updated = utc.localize(datetime(1970, 1, 1))
            write_last_processed(last_processed_file, default_last_processed)
    else:
        logging.info(f"{last_processed_file} not found. Creating with defaults.")
        last_updated = utc.localize(datetime(1970, 1, 1))
        write_last_processed(last_processed_file, default_last_processed)

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
    if current_mapping_modified and current_mapping_modified > last_updated:
        download_tasks.append((mapping_url, mapping_dest))
    elif not os.path.exists(mapping_dest):  # Download if file doesn’t exist
        download_tasks.append((mapping_url, mapping_dest))

    # Download NIST baselines
    for level, url in config["baselines"].items():
        filename = url.split('/')[-1]
        dest_path = os.path.join(data_dir, filename)
        if not os.path.exists(dest_path):  # Only download if missing
            download_tasks.append((url, dest_path))

    # Download NIST SP 800-53 catalog
    catalog_url = config["nist_sp800_53_catalog_url"]
    catalog_filename = catalog_url.split('/')[-1]
    catalog_dest = os.path.join(data_dir, catalog_filename)
    if not os.path.exists(catalog_dest):  # Only download if missing
        download_tasks.append((catalog_url, catalog_dest))

    # Execute parallel downloads
    if download_tasks:
        results = download_parallel(download_tasks)
        for url, dest, success in results:
            if url == mapping_url and success and current_mapping_modified and current_mapping_modified > last_updated:
                last_processed = {
                    "last_updated": current_mapping_modified.isoformat()
                }
                write_last_processed(last_processed_file, last_processed)
                logging.info(f"Updated {mapping_filename} based on new modification date.")
            elif url == mapping_url and not success:
                logging.warning(f"Failed to update {mapping_filename} despite newer modification date.")

    # Download CCI list
    cci_url = config["cci_list_url"]
    cci_zip = os.path.join(cci_list_dir, "U_CCI_List.zip")
    if download_file(cci_url, cci_zip):
        unzip_file(cci_zip, cci_list_dir)
        os.remove(cci_zip)
        logging.info("Processed CCI list successfully.")

    # Handle STIGs and SRGs
    base_url = config["disa_url"]
    latest_url, latest_filename, latest_date = get_latest_available_zip_info(base_url)
    if latest_url is None:
        logging.warning("No recent STIG/SRG library found; skipping STIG/SRG processing.")
        return

    # Compare latest_date (year, month) with last_updated timestamp
    latest_date_dt = utc.localize(datetime(latest_date[0], latest_date[1], 1))
    if latest_date_dt > last_updated:
        dest_path = os.path.join(stig_zips_dir, latest_filename)
        if download_file(latest_url, dest_path):
            try:
                extract_nested_zips(dest_path, stig_zips_dir, stig_dir, srg_dir, docs_dir)
                # Update last_processed with the current time after successful processing
                last_processed = {
                    "last_updated": datetime.now(utc).isoformat()
                }
                write_last_processed(last_processed_file, last_processed)
                logging.info(f"Successfully processed {latest_filename}")
            except Exception as e:
                logging.error(f"Error processing {latest_filename}: {e}")
                raise
            finally:
                # Clean up the downloaded zip file
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                    logging.info(f"Removed {dest_path}")
    else:
        logging.info(f"Latest STIG/SRG library {latest_filename} is already processed; skipping.")

if __name__ == "__main__":
    try:
        config_path = os.path.join(os.path.dirname(__file__), '../config.json')
        fetch_data(config_path)
    except Exception as e:
        logging.error(f"Data fetcher failed: {e}")
        print(f"Error: {e}")
        exit(1)