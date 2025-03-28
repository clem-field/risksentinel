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
    """Check if the compliance data is fresh based on last_processed.json."""
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
        if last_updated.tzinfo is None:
            last_updated = tz.localize(last_updated)
        age = now - last_updated
        return age < timedelta(days=max_age_days)
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"Error reading last_processed.json: {e}")
        return False

def load_compliance_data(config):
    """Load compliance data including NIST ATT&CK mappings.

    Args:
        config (dict): Configuration dictionary from config.json.

    Returns:
        dict: A dictionary containing loaded compliance data with ATT&CK mappings.
    """
    data = {}
    base_path = os.path.dirname(os.path.dirname(__file__))
    namespaces = {
        "xccdf": "http://checklists.nist.gov/xccdf/1.1",
        "cci": "http://iase.disa.mil/cci"
    }

    # Load NIST ATT&CK Mapping
    mapping_file = os.path.join(base_path, "data", "nist_800_53-rev5_attack-14.1-enterprise_json.json")
    nist_to_attack = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r') as f:
                mapping_data = json.load(f)
            if "controls" not in mapping_data:
                raise ValueError("Invalid JSON structure: 'controls' key missing")
            for control_id, details in mapping_data["controls"].items():
                nist_to_attack[control_id] = [
                    {"id": tech["id"], "name": tech["name"], "description": tech.get("description", "")}
                    for tech in details.get("techniques", [])
                ]
            logging.info(f"Loaded NIST ATT&CK mapping with {len(nist_to_attack)} controls")
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to load NIST ATT&CK mapping: {e}")
    else:
        logging.warning(f"NIST ATT&CK mapping file not found at {mapping_file}")

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
                ccis = [cci.text for cci in cci_elems if cci.text] if cci_elems else []
                data[control_id] = {
                    "title": title,
                    "description": description,
                    "type": "STIG",
                    "file": os.path.basename(xml_file),
                    "ccis": ccis,
                    "attack_techniques": []
                }
            logging.info(f"Parsed STIG file {xml_file} with {len(rules)} items")
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
                ccis = [cci.text for cci in cci_elems if cci.text] if cci_elems else []
                data[control_id] = {
                    "title": title,
                    "description": description,
                    "type": "SRG",
                    "file": os.path.basename(xml_file),
                    "ccis": ccis,
                    "attack_techniques": []
                }
            logging.info(f"Parsed SRG file {xml_file} with {len(rules)} items")
        except Exception as e:
            logging.error(f"Failed to parse SRG file {xml_file}: {e}")

    # Load CCI data and map ATT&CK techniques
    cci_dir = os.path.join(base_path, config["cci_list_dir"])
    for xml_file in glob.glob(os.path.join(cci_dir, "*.xml")):
        try:
            tree = etree.parse(xml_file)
            cci_items = tree.findall(".//cci:cci_item", namespaces)
            for cci_item in cci_items:
                cci_id = cci_item.get("id")
                if not cci_id:
                    logging.warning(f"Skipping cci_item with no id in {xml_file}")
                    continue
                definition_elem = cci_item.find("cci:definition", namespaces)
                definition = definition_elem.text if definition_elem is not None else "No definition"
                type_elem = cci_item.find("cci:type", namespaces)
                cci_type = type_elem.text if type_elem is not None else "Unknown type"
                status_elem = cci_item.find("cci:status", namespaces)
                status = status_elem.text if status_elem is not None else "Unknown status"
                publishdate_elem = cci_item.find("cci:publishdate", namespaces)
                publishdate = publishdate_elem.text if publishdate_elem is not None else "Unknown date"
                contributor_elem = cci_item.find("cci:contributor", namespaces)
                contributor = contributor_elem.text if contributor_elem is not None else "Unknown contributor"
                references = [
                    {
                        "creator": ref.get("creator", "Unknown creator"),
                        "title": ref.get("title", "No title"),
                        "version": ref.get("version", "Unknown version"),
                        "location": ref.get("location", "No location"),
                        "index": ref.get("index", "No index")
                    }
                    for ref in cci_item.findall("cci:references/cci:reference", namespaces)
                ]
                # Map ATT&CK techniques via NIST controls in references
                attack_techniques = []
                for ref in references:
                    if ref["creator"] == "NIST" and "SP 800-53" in ref["title"]:
                        nist_control = ref["index"].split()[0]  # e.g., "AC-1" from "AC-1 a 1"
                        if nist_control in nist_to_attack:
                            attack_techniques.extend(nist_to_attack[nist_control])
                data[cci_id] = {
                    "type": "CCI",
                    "definition": definition,
                    "cci_type": cci_type,
                    "status": status,
                    "publishdate": publishdate,
                    "contributor": contributor,
                    "references": references,
                    "file": os.path.basename(xml_file),
                    "attack_techniques": attack_techniques
                }
            logging.info(f"Parsed CCI file {xml_file} with {len(cci_items)} items")
        except Exception as e:
            logging.error(f"Failed to parse CCI file {xml_file}: {e}")

    # Propagate ATT&CK techniques to STIGs and SRGs via CCIs
    for item_id, item in data.items():
        if item["type"] in ["STIG", "SRG"] and "ccis" in item:
            attack_techniques = []
            for cci in item["ccis"]:
                if cci in data and "attack_techniques" in data[cci]:
                    attack_techniques.extend(data[cci]["attack_techniques"])
            item["attack_techniques"] = list({t["id"]: t for t in attack_techniques}.values())  # Remove duplicates

    return data

def process_llm_prompt(config, compliance_data, prompt):
    """Process a user prompt using OpenRouter API with compliance data context, including ATT&CK mappings."""
    context = "Compliance Data Context:\n"
    if prompt.startswith("get "):
        item_id = prompt.replace("get ", "").strip()
        if item_id in compliance_data:
            data = compliance_data[item_id]
            item_type = data["type"]
            if item_type in ["STIG", "SRG"]:
                context += (f"Control ID: {item_id}\n"
                            f"Type: {item_type}\n"
                            f"Title: {data['title']}\n"
                            f"Description: {data['description'][:500]}... (truncated)\n"
                            f"CCIs: {', '.join(data['ccis']) if 'ccis' in data and data['ccis'] else 'None'}\n"
                            f"Source File: {data['file']}\n")
            elif item_type == "CCI":
                ref_titles = [ref['title'] for ref in data['references']] if data['references'] else ["None"]
                context += (f"CCI ID: {item_id}\n"
                            f"Type: {item_type}\n"
                            f"Definition: {data['definition'][:500]}... (truncated)\n"
                            f"CCI Type: {data['cci_type']}\n"
                            f"Status: {data['status']}\n"
                            f"Publish Date: {data['publishdate']}\n"
                            f"Contributor: {data['contributor']}\n"
                            f"References: {', '.join(ref_titles)}\n"
                            f"Source File: {data['file']}\n")
            else:
                context += f"Unknown item type for ID: {item_id}\n"
            if "attack_techniques" in data and data["attack_techniques"]:
                context += "Mitigated ATT&CK Techniques:\n"
                for tech in data["attack_techniques"]:
                    context += f"  - {tech['id']}: {tech['name']} - {tech['description'][:100]}...\n"
        else:
            return f"No data found for ID: {item_id}"
    elif "search" in prompt:
        keyword = prompt.replace("search ", "").strip()
        matches = [
            (cid, d) for cid, d in compliance_data.items()
            if keyword.lower() in d.get('title', '').lower() or
               keyword.lower() in d.get('description', '').lower() or
               keyword.lower() in d.get('definition', '').lower()
        ]
        if matches:
            context += f"Found {len(matches)} matches for '{keyword}':\n"
            for cid, d in matches[:3]:  # Limit to 3 for context brevity
                item_type = d["type"]
                if item_type in ["STIG", "SRG"]:
                    context += f"- {cid} ({item_type}): {d['title'][:100]}...\n"
                elif item_type == "CCI":
                    context += f"- {cid} ({item_type}): {d['definition'][:100]}...\n"
        else:
            return f"No matches found for '{keyword}'"
    else:
        context += f"Total items loaded: {len(compliance_data)}\n"

    full_prompt = f"{context}\nUser Query: {prompt}\nProvide a concise, accurate response based on the context."
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
    print("You can query specific items using 'get <ID>', e.g., 'get CCI-000001'.")
    print("You can also search keywords using 'search <keyword>', e.g., 'search access control'.")
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
