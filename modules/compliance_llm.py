import argparse
import subprocess
import sys
import json
from datetime import datetime, timedelta, timezone  # Added timezone import
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
        # Use UTC timezone for consistency
        now = datetime.now(timezone.utc)
        age = now - last_updated
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
    namespaces = {
        "xccdf": "http://checklists.nist.gov/xccdf/1.1",
        "cci": "http://iase.disa.mil/cci"  # Placeholder for CCI files
    }

    # Load STIG data
    stig_dir = os.path.join(base_path, config["stig_dir"])
    for xml_file in glob.glob(os.path.join(stig_dir, "*.xml")):
        try:
            tree = etree.parse(xml_file)
            rules = tree.findall(".//xccdf:Group/xccdf:Rule", namespaces)
            for rule in rules:
                control_id = rule.get("id")
                title_elem = rule.find("xccdf:title", namespaces)
                title = title_elem.text if title_elem is not None else "No title"
                desc_elem = rule.find("xccdf:description", namespaces)
                description = desc_elem.text if desc_elem is not None else "No description"
                cci_elems = rule.findall("xccdf:ident[@system='http://cyber.mil/cci']", namespaces)
                ccis = [cci.text for cci in cci_elems] if cci_elems else []
                data[control_id] = {
                    "title": title,
                    "description": description,
                    "type": "STIG",
                    "file": os.path.basename(xml_file),
                    "ccis": ccis
                }
            logging.info(f"Parsed STIG file {xml_file} with {len(rules)} rules")
        except Exception as e:
            logging.error(f"Failed to parse STIG file {xml_file}: {e}")

    # Load SRG data
    srg_dir = os.path.join(base_path, config["srg_dir"])
    for xml_file in glob.glob(os.path.join(srg_dir, "*.xml")):
        try:
            tree = etree.parse(xml_file)
            rules = tree.findall(".//xccdf:Group/xccdf:Rule", namespaces)
            for rule in rules:
                control_id = rule.get("id")
                title_elem = rule.find("xccdf:title", namespaces)
                title = title_elem.text if title_elem is not None else "No title"
                desc_elem = rule.find("xccdf:description", namespaces)
                description = desc_elem.text if desc_elem is not None else "No description"
                cci_elems = rule.findall("xccdf:ident[@system='http://cyber.mil/cci']", namespaces)
                ccis = [cci.text for cci in cci_elems] if cci_elems else []
                data[control_id] = {
                    "title": title,
                    "description": description,
                    "type": "SRG",
                    "file": os.path.basename(xml_file),
                    "ccis": ccis
                }
            logging.info(f"Parsed SRG file {xml_file} with {len(rules)} rules")
        except Exception as e:
            logging.error(f"Failed to parse SRG file {xml_file}: {e}")

    # Load CCI data (placeholder until CCI XML structure is provided)
    cci_dir = os.path.join(base_path, config["cci_list_dir"])
    for xml_file in glob.glob(os.path.join(cci_dir, "*.xml")):
        try:
            tree = etree.parse(xml_file)
            # Tentative CCI parsing (adjust based on actual CCI XML structure)
            cci_items = tree.findall(".//cci:cci_item", namespaces)
            for cci_item in cci_items:
                cci_id = cci_item.get("id")
                title_elem = cci_item.find("cci:title", namespaces)
                title = title_elem.text if title_elem is not None else "No title"
                desc_elem = cci_item.find("cci:description", namespaces)
                description = desc_elem.text if desc_elem is not None else "No description"
                data[cci_id] = {
                    "title": title,
                    "description": description,
                    "type": "CCI",
                    "file": os.path.basename(xml_file)
                }
            logging.info(f"Parsed CCI file {xml_file} with {len(cci_items)} items")
        except Exception as e:
            logging.error(f"Failed to parse CCI file {xml_file}: {e}")

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
        print(f"Compliance LLM tool running with {len(compliance_data)} items loaded.")

    # Main functionality (placeholder)
    print("Compliance LLM tool running with loaded data.")
    # Add your LLM processing logic here using compliance_data

if __name__ == "__main__":
    main()