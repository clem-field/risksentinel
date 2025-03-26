import argparse
import subprocess
import sys
import json
from datetime import datetime, timedelta
import logging
import os
import glob
from lxml import etree  # For parsing XML files
import requests  # For OpenRouter API calls
import pytz  # For timezone handling

# Configure logging
logging.basicConfig(
    filename='compliance_llm.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_data_freshness(config, max_age_days=7):
    """Check if the compliance data is fresh based on last_processed.json.

    Args:
        config (dict): Configuration dictionary from config.json.
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
        tz = pytz.timezone(config["timezone"])
        now = datetime.now(tz)
        # Ensure last_updated is timezone-aware if it has an offset, otherwise localize it
        if last_updated.tzinfo is None:
            last_updated = tz.localize(last_updated)
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
    base_path = os.path.dirname(os.path.dirname(__file__))
    namespaces = {
        "xccdf": "http://checklists.nist.gov/xccdf/1.1",
        "cci": "http://iase.disa.mil/cci"
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

def process_llm_prompt(config, compliance_data, prompt):
    """Process a user prompt using OpenRouter API with compliance data context.

    Args:
        config (dict): Configuration dictionary with API settings.
        compliance_data (dict): Loaded compliance data.
        prompt (str): User input prompt.

    Returns:
        str: Response from OpenRouter or error message.
    """
    # Prepare context from compliance data (limit to avoid overwhelming API)
    context = "Compliance Data Context:\n"
    if prompt.startswith("get "):
        control_id = prompt.replace("get ", "").strip()
        if control_id in compliance_data:
            data = compliance_data[control_id]
            context += (f"Control ID: {control_id}\n"
                        f"Type: {data['type']}\n"
                        f"Title: {data['title']}\n"
                        f"Description: {data['description'][:500]}... (truncated)\n"
                        f"CCIs: {', '.join(data['ccis']) if data['ccis'] else 'None'}\n"
                        f"Source File: {data['file']}\n")
        else:
            return f"No data found for control ID: {control_id}"
    elif "search" in prompt:
        keyword = prompt.replace("search ", "").strip()
        matches = [
            (cid, d) for cid, d in compliance_data.items()
            if keyword.lower() in d['title'].lower() or keyword.lower() in d['description'].lower()
        ]
        if matches:
            context += f"Found {len(matches)} matches for '{keyword}':\n"
            for cid, d in matches[:3]:  # Limit to 3 for context brevity
                context += f"- {cid} ({d['type']}): {d['title']}\n"
        else:
            return f"No matches found for '{keyword}'"
    else:
        # General query, include a summary
        context += f"Total controls loaded: {len(compliance_data)}\n"

    # Construct the full prompt for OpenRouter
    full_prompt = f"{context}\nUser Query: {prompt}\nProvide a concise, accurate response based on the context."

    # OpenRouter API request
    headers = {
        "Authorization": f"Bearer {config['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config["DEEPSEEK_MODEL"],
        "messages": [{"role": "user", "content": full_prompt}]
    }
    try:
        response = requests.post(
            f"{config['OPENROUTER_BASE_URL']}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except requests.RequestException as e:
        logging.error(f"OpenRouter API error: {e}")
        return f"Error contacting OpenRouter: {str(e)}"

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
    logging.info(f"Loaded config: {json.dumps(config, indent=2)}")

    # Verify API key
    if not config.get("OPENROUTER_API_KEY") or config["OPENROUTER_API_KEY"] == "<YOUR_OPEN_ROUTER_API_KEY>":
        logging.error("OpenRouter API key not configured.")
        print("Error: Please set a valid OPENROUTER_API_KEY in config.json.")
        sys.exit(1)

    # Force update if --update flag is provided
    if args.update:
        logging.info("Updating compliance data...")
        try:
            subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "data_fetcher.py")], check=True)
            logging.info("Data updated successfully.")
            print("Data updated successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update data: {e}")
            print(f"Error: Failed to update data: {e}. Proceeding with existing data.")

    # Check data freshness and notify user
    if not check_data_freshness(config):
        logging.warning("Compliance data may be outdated.")
        print("Warning: Compliance data may be outdated. Consider updating with --update or running data_fetcher.py.")

    # Check if critical directories exist
    base_path = os.path.dirname(os.path.dirname(__file__))
    print(f"Script base path: {base_path}")
    for dir_key in ["stig_dir", "srg_dir", "cci_list_dir"]:
        dir_path = os.path.join(base_path, config[dir_key])
        print(f"Checking {dir_key}: {dir_path}")
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
        sys.exit(1)
    else:
        logging.info(f"Loaded {len(compliance_data)} compliance items.")
        print(f"Compliance LLM tool running with {len(compliance_data)} items loaded.")

    # Interactive LLM prompt loop
    print("Welcome to the Compliance LLM Tool! Type 'exit' to quit.")
    while True:
        prompt = input("Enter your query: ").strip()
        if prompt.lower() == "exit":
            print("Exiting Compliance LLM Tool.")
            break
        response = process_llm_prompt(config, compliance_data, prompt)
        print(response)
        logging.info(f"User prompt: '{prompt}' | Response: '{response[:100]}...'")

if __name__ == "__main__":
    main()