import argparse
import subprocess
import sys
import json
from datetime import datetime, timedelta, timezone
import logging
import os
import glob
from lxml import etree  # For parsing XML files
from openai import OpenAI  # For OpenRouter API interaction

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
        age = datetime.now(timezone.utc) - last_updated
        return age < timedelta(days=max_age_days)
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"Error reading last_processed.json: {e}")
        return False

def load_compliance_data(config, base_path):
    """Load compliance data from directories specified in config.json.

    Args:
        config (dict): Configuration dictionary from config.json.
        base_path (str): Path to the project root directory.

    Returns:
        dict: A dictionary containing loaded compliance data.
    """
    data = {}

    # Load STIG data
    stig_dir = os.path.join(base_path, config["stig_dir"])
    print(f"Looking for STIG data in: {stig_dir}")
    logging.info(f"Checking STIG directory: {stig_dir}")
    stig_files = glob.glob(os.path.join(stig_dir, "*.xml"))
    if not stig_files:
        print(f"No .xml files found in {stig_dir}")
        logging.warning(f"No XML files found in {stig_dir}")
    else:
        print(f"Found {len(stig_files)} .xml files in {stig_dir}")
    for xml_file in stig_files:
        try:
            tree = etree.parse(xml_file)
            for elem in tree.findall(".//Rule"):
                control_id = elem.get("id")
                title = elem.find("title").text
                data[control_id] = {"title": title, "type": "STIG"}
            logging.info(f"Loaded STIG data from {xml_file}")
        except Exception as e:
            logging.error(f"Failed to parse STIG file {xml_file}: {e}")

    # Load SRG data (placeholder)
    srg_dir = os.path.join(base_path, config["srg_dir"])
    print(f"Looking for SRG data in: {srg_dir}")
    logging.info(f"Checking SRG directory: {srg_dir}")
    srg_files = glob.glob(os.path.join(srg_dir, "*.xml"))
    if not srg_files:
        print(f"No .xml files found in {srg_dir}")
        logging.warning(f"No XML files found in {srg_dir}")

    # Load CCI data (placeholder)
    cci_dir = os.path.join(base_path, config["cci_list_dir"])
    print(f"Looking for CCI data in: {cci_dir}")
    logging.info(f"Checking CCI directory: {cci_dir}")
    cci_files = glob.glob(os.path.join(cci_dir, "*.xml"))
    if not cci_files:
        print(f"No .xml files found in {cci_dir}")
        logging.warning(f"No XML files found in {cci_dir}")

    # Add SRG and CCI parsing logic here if files exist
    return data

def main():
    parser = argparse.ArgumentParser(description="Compliance LLM Tool")
    parser.add_argument("--update", action="store_true", help="Update compliance data before running")
    args = parser.parse_args()

    logging.info("Starting compliance LLM tool.")

    # Load config and determine project root
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    if not os.path.exists(config_path):
        logging.error("config.json not found.")
        print("Error: config.json not found. Exiting.")
        sys.exit(1)
    base_path = os.path.dirname(os.path.abspath(config_path))  # Project root directory
    logging.info(f"Project root base path: {base_path}")
    print(f"Using project root: {base_path}")
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
    missing_dirs = []
    for dir_key in ["stig_dir", "srg_dir", "cci_list_dir"]:
        dir_path = os.path.join(base_path, config[dir_key])
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_key)
            logging.warning(f"{dir_key} not found: {dir_path}")

    if missing_dirs:
        logging.error(f"Missing directories: {', '.join(missing_dirs)}. Attempting to fetch data...")
        print(f"Error: Missing directories ({', '.join(missing_dirs)}). Running data_fetcher.py to download the data...")
        try:
            subprocess.run([sys.executable, "modules/data_fetcher.py"], check=True)
            logging.info("Data fetched successfully after missing directories detected.")
            print("Data fetched successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to fetch data: {e}")
            print(f"Error: Failed to fetch data: {e}. Proceeding without local data.")

    # Load compliance data
    logging.info("Loading compliance data...")
    compliance_data = load_compliance_data(config, base_path)
    if not compliance_data:
        logging.warning("No compliance data loaded. Functionality may be limited.")
        print("Warning: No compliance data found. Functionality may be limited.")
    else:
        logging.info(f"Loaded {len(compliance_data)} compliance items.")
        print(f"Loaded {len(compliance_data)} compliance items.")

    # Initialize OpenRouter client
    client = OpenAI(
        api_key=config["OPENROUTER_API_KEY"],
        base_url=config["OPENROUTER_BASE_URL"]
    )

    # Interactive LLM loop
    print("Welcome to the Compliance LLM Tool! Type 'exit' to quit.")
    while True:
        query = input("\nEnter your compliance question: ").strip()
        if query.lower() == 'exit':
            print("Exiting Compliance LLM Tool.")
            break
        if not query:
            print("Please enter a question.")
            continue

        # Construct prompt with compliance data
        context = "\n".join([f"{k}: {v['title']}" for k, v in compliance_data.items()]) if compliance_data else "No local compliance data available."
        prompt = (
            "You are a compliance assistant specializing in NIST SP 800-53 and STIGs. "
            "Use the provided compliance data to answer the question accurately. "
            "If the data lacks sufficient information, provide a general response based on your knowledge.\n\n"
            f"Compliance Data:\n{context}\n\n"
            f"Question: {query}\n\nAnswer:"
        )

        try:
            response = client.chat.completions.create(
                model=config["DEEPSEEK_MODEL"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            answer = response.choices[0].message.content
            print(f"\nAnswer: {answer}")
        except Exception as e:
            logging.error(f"LLM query failed: {e}")
            print(f"Error: Failed to get response from LLM: {e}")

if __name__ == "__main__":
    main()