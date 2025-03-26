import os
import json
import requests
import zipfile
import shutil
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import pytz
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(
    filename='data_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z'  # Include timezone in logs
)

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config.json')
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)

# Timezone setup
UTC_TZ = pytz.UTC
LOCAL_TZ = pytz.timezone(CONFIG['timezone'])

def ensure_dir_exists(directory: str) -> None:
    """Create a directory if it doesn’t exist."""
    os.makedirs(directory, exist_ok=True)

def download_file(url: str, destination: str) -> bool:
    """Download a file from a URL to a destination path."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded {os.path.basename(destination)} successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        return False

def unzip_file(zip_path: str, extract_dir: str) -> str:
    """Unzip a file to a specified directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    logging.info(f"Unzipped {zip_path} to {extract_dir}")
    return extract_dir

def get_last_modified_date(url: str) -> Optional[datetime]:
    """Retrieve the Last-Modified date from the HTTP header of a URL."""
    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            dt = parsedate_to_datetime(last_modified)
            return UTC_TZ.localize(dt)  # Make it UTC-aware
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking Last-Modified for {url}: {e}")
        return None

def get_latest_available_zip_info(base_url: str, max_months_back: int = 12) -> Tuple[Optional[str], Optional[str], Optional[Tuple[int, int]]]:
    """Find the latest available zip file by checking recent months."""
    current_date = datetime.now(UTC_TZ)
    for i in range(max_months_back):
        check_date = current_date - timedelta(days=30 * i)
        month_name = check_date.strftime("%B")
        year = check_date.year
        url = base_url.format(month=month_name, year=year)
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                month_num = check_date.month
                filename = f"U_SRG-STIG_Library_{month_name}_{year}.zip"
                return url, filename, (year, month_num)
        except requests.exceptions.RequestException:
            continue
    logging.warning("No recent STIG/SRG library found.")
    return None, None, None

def fetch_data() -> None:
    """Fetch data files based on config.json and save to appropriate directories."""
    # Define directory paths
    root_dir = os.path.dirname(os.path.abspath(CONFIG_PATH))
    data_dir = os.path.join(root_dir, "data")
    cci_list_dir = os.path.join(root_dir, CONFIG["cci_list_dir"])
    stig_zips_dir = os.path.join(data_dir, "stig_zips")
    srg_dir = os.path.join(root_dir, CONFIG["srg_dir"])
    stig_dir = os.path.join(root_dir, CONFIG["stig_dir"])

    # Create directories
    ensure_dir_exists(data_dir)
    ensure_dir_exists(cci_list_dir)
    ensure_dir_exists(stig_zips_dir)
    ensure_dir_exists(srg_dir)
    ensure_dir_exists(stig_dir)

    # Load or initialize last processed data
    last_processed_file = os.path.join(data_dir, "last_processed.json")
    if os.path.exists(last_processed_file):
        with open(last_processed_file, 'r') as f:
            last_processed = json.load(f)
            disa_last_processed = tuple(last_processed.get("disa_zip", [0, 0]))
            nist_mapping_last_modified_str = last_processed.get("nist_mapping", "1970-01-01T00:00:00Z")
            nist_mapping_last_modified = datetime.fromisoformat(nist_mapping_last_modified_str)
            # If it's naive, localize it to UTC; if already aware, keep it as is
            if nist_mapping_last_modified.tzinfo is None:
                nist_mapping_last_modified = UTC_TZ.localize(nist_mapping_last_modified)
            elif nist_mapping_last_modified.tzinfo != UTC_TZ:
                # Convert to UTC if it's in a different timezone
                nist_mapping_last_modified = nist_mapping_last_modified.astimezone(UTC_TZ)
    else:
        disa_last_processed = (0, 0)
        nist_mapping_last_modified = UTC_TZ.localize(datetime(1970, 1, 1))

    # Download NIST 800-53 attack mapping
    mapping_url = CONFIG["nist_800_53_attack_mapping_url"]
    mapping_filename = mapping_url.split('/')[-1]
    mapping_dest = os.path.join(data_dir, mapping_filename)
    current_mapping_modified = get_last_modified_date(mapping_url)
    if current_mapping_modified and current_mapping_modified > nist_mapping_last_modified:
        if download_file(mapping_url, mapping_dest):
            with open(last_processed_file, 'w') as f:
                last_processed = {
                    "disa_zip": list(disa_last_processed),
                    "nist_mapping": current_mapping_modified.isoformat()
                }
                json.dump(last_processed, f)
            logging.info(f"Updated {mapping_filename} based on new modification date {current_mapping_modified.astimezone(LOCAL_TZ)}")
        else:
            logging.error(f"Failed to update {mapping_filename} despite newer modification date.")
    elif current_mapping_modified:
        logging.info(f"{mapping_filename} is up to date with modification date {current_mapping_modified.astimezone(LOCAL_TZ)}.")
    else:
        logging.warning(f"Could not determine modification date for {mapping_filename}; downloading anyway.")
        download_file(mapping_url, mapping_dest)

    # Download NIST baselines
    for level, url in CONFIG["baselines"].items():
        filename = url.split('/')[-1]
        dest_path = os.path.join(data_dir, filename)
        logging.info(f"Downloading {filename}...")
        download_file(url, dest_path)

    # Download NIST SP 800-53 catalog
    catalog_url = CONFIG["nist_sp800_53_catalog_url"]
    catalog_filename = catalog_url.split('/')[-1]
    catalog_dest = os.path.join(data_dir, catalog_filename)
    logging.info(f"Downloading {catalog_filename}...")
    download_file(catalog_url, catalog_dest)

    # Download CCI list
    cci_url = CONFIG["cci_list_url"]
    cci_zip = os.path.join(cci_list_dir, "U_CCI_List.zip")
    logging.info(f"Downloading CCI list...")
    if download_file(cci_url, cci_zip):
        unzip_file(cci_zip, cci_list_dir)
        os.remove(cci_zip)
        logging.info(f"Cleaned up {cci_zip}")

    # Handle STIGs and SRGs
    base_url = CONFIG["disa_url"]
    latest_url, latest_filename, latest_date = get_latest_available_zip_info(base_url)
    if latest_url is None:
        logging.warning("No recent STIG/SRG library found; skipping STIG/SRG processing.")
        return

    if latest_date and latest_date > disa_last_processed:
        dest_path = os.path.join(stig_zips_dir, latest_filename)
        if download_file(latest_url, dest_path):
            try:
                temp_extract_dir = os.path.join(stig_zips_dir, "temp_extract")
                ensure_dir_exists(temp_extract_dir)
                unzip_file(dest_path, temp_extract_dir)
                
                for root, _, files in os.walk(temp_extract_dir):
                    for file in files:
                        if file.endswith(CONFIG["xml_suffix"]):
                            src_path = os.path.join(root, file)
                            if CONFIG["srg_zip_suffix"].replace(".zip", "") in file:
                                dest_path = os.path.join(srg_dir, file)
                            else:
                                dest_path = os.path.join(stig_dir, file)
                            shutil.move(src_path, dest_path)
                            logging.info(f"Moved {file} to {dest_path}")
                
                shutil.rmtree(temp_extract_dir)
                with open(last_processed_file, 'w') as f:
                    last_processed = {
                        "disa_zip": list(latest_date),
                        "nist_mapping": nist_mapping_last_modified.isoformat()
                    }
                    json.dump(last_processed, f)
                logging.info(f"Successfully processed {latest_filename}")
            except Exception as e:
                logging.error(f"Error processing {latest_filename}: {e}")
        else:
            logging.error(f"Failed to download {latest_filename}")
    else:
        logging.info(f"Latest STIG/SRG library {latest_filename} is already processed; skipping.")

if __name__ == "__main__":
    fetch_data()