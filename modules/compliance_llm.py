import argparse
import subprocess
import sys
import json
from datetime import datetime, timedelta, timezone
import logging
import os
import glob
from lxml import etree  # For parsing XML files

# Configure logging
logging.basicConfig(
    filename='compliance_llm.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_data_freshness(max_age_days=7):
    """Check if the compliance data is fresh based on last_processed.json.

    Args:
        max_age_days (int): Maximum age in days before data is considered outdated.

    Returns:
        bool: True if data is fresh, False otherwise.
    """
    last_processed_file = os.path.join("data", "last_processed.json")
    if not os.path.exists(last_processed_file):
        logging.warning("last_processed.json missing. Data freshness unknown.")
        return False

    try:
        with open(last_processed_file, 'r') as f:
            last_processed = json.load(f)
        last_updated_str = last_processed.get('last_updated')
        if not last_updated_str:
            logging.warning("No 'last_updated' key in last_processed.json.")
            return False
        last_updated = datetime.fromisoformat(last_updated_str)
        age = datetime.now(timezone.utc) - last_updated  # Fixed: Use UTC-aware datetime.now()
        return age < timedelta(days=max_age_days)
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"Error reading last_processed.json: {e}")
        return False

def load_compliance_data(config):
    """Load compliance data from directories specified in config.json.

    Args:
        config (dict): Configuration dictionary from config.json.

    Returns:
        dict: A dictionary containing loaded compliance data.
    """
    data = {}
    base_path = os.path.dirname(__file__)

    # Load STIG data
    stig_dir = os.path.join(base_path, config["stig_dir"])
    for xml_file in glob.glob(os.path.join(stig_dir, "*.xml")):
        try:
            tree = etree.parse(xml_file)
            for elem in tree.findall(".//Rule"):
                control_id = elem.get("id")
                title = elem.find("title").text
                data[control_id] = {"title": title, "type": "STIG"}
        except Exception as e:
            logging.error(f"Failed to parse STIG file {xml_file}: {e}")

    # Placeholder for SRG and CCI data (extend as needed)
    srg_dir = os.path.join(base_path, config["srg_dir"])
    cci_dir = os.path.join(base_path, config["cci_list_dir"])
    # Add parsing logic for SRG and CCI files here if required

    return data

def main():
    parser = argparse.ArgumentParser(description="Compliance LLM Tool")
    parser.add_argument("--update", action="store_true", help="Update compliance data before running")
    args = parser.parse_args()

    logging.info("Starting compliance LLM tool.")

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    if not os.path.exists(config_path):
        logging.error("config.json not found.")
        print("Error: config.json not found. Exiting.")
        sys.exit(1)
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Force update if --update flag is provided
    if args.update:
        logging.info("Updating compliance data...")
        try:
            subprocess.run([sys.executable, "modules/data_fetcher.py"], check=True)
            logging.info("Data updated successfully.")
            print("Data updated successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update data: {e}")
            print(f"Error: Failed to update data: {e}. Proceeding with existing data.")

    # Check data freshness and notify user
    if not check_data_freshness():
        logging.warning("Compliance data may be outdated.")
        print("Warning: Compliance data may be outdated. Consider updating with --update or running data_fetcher.py.")

    # Check if critical directories exist
    base_path = os.path.dirname(__file__)
    for dir_key in ["stig_dir", "srg_dir", "cci_list_dir"]:
        dir_path = os.path.join(base_path, config[dir_key])
        if not os.path.exists(dir_path):
            logging.error(f"{dir_key} not found: {dir_path}")
            print(f"Error: {dir_key} not found. Please run data_fetcher.py to download the data.")
            sys.exit(1)

    # Load compliance data
    logging.info("Loading compliance data...")
    compliance_data = load_compliance_data(config)
    if not compliance_data:
        logging.warning("No compliance data loaded. Functionality may be limited.")
        print("Warning: No compliance data found. Functionality may be limited.")
    else:
        logging.info(f"Loaded {len(compliance_data)} compliance items.")

    # Main functionality (placeholder)
    print("Compliance LLM tool running with loaded data.")
    # Add your LLM processing logic here using compliance_data

if __name__ == "__main__":
    main()