import os
import json
import pandas as pd
from openai import OpenAI
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Make sure the config file is good to go
def validate_config(config):
    required_keys = [
        "timezone", "cci_list_dir", "srg_dir", "stig_dir",
        "nist_800_53_attack_mapping_url", "baselines",
        "nist_sp800_53_catalog_url", "cci_list_url",
        "disa_url", "xml_suffix", "srg_zip_suffix"
    ]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    logging.info("Config validated successfully.")

# Call it after loading config
validate_config(CONFIG)

# Define roles
roles = {
    "Authorizing Official": "You can ask for executive summaries or compliance dashboards.",
    "Application Development Team": (
        "This LLM can help you with:\n"
        "1. Querying specific controls and their requirements.\n"
        "2. Getting explanations of controls.\n"
        "3. Verifying if a given scenario meets a control."
    ),
    "Assessor": (
        "This LLM can help you with:\n"
        "1. Querying specific controls and their requirements.\n"
        "2. Getting explanations of controls.\n"
        "3. Verifying if a given scenario meets a control."
    ),
    "Auditor": "You can ask for compliance evidence with citations."
}

def load_compliance_data(root_dir, config):
    """Load essential compliance data from files."""
    print(Fore.CYAN + "Loading compliance data..." + Style.RESET_ALL)
    data_dir = os.path.join(root_dir, "data")
    cci_list_dir = os.path.join(root_dir, config["cci_list_dir"])

    # Load NIST SP 800-53 control catalog
    controls = {}
    control_file = os.path.join(data_dir, "sp800-53r5-control-catalog.xlsx")
    if os.path.exists(control_file):
        try:
            df = pd.read_excel(control_file)
            for _, row in df.iterrows():
                control_id = row.get('Control Identifier', '')
                if control_id:
                    controls[control_id] = str(row.get('Control Text', ''))
            print(Fore.CYAN + f"Loaded {len(controls)} NIST controls." + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"Error loading control catalog: {str(e)}" + Style.RESET_ALL)

    # Load CCI list
    cci_data = {}
    for excel_file in [f for f in os.listdir(cci_list_dir) if f.endswith('.xlsx')]:
        excel_path = os.path.join(cci_list_dir, excel_file)
        try:
            df = pd.read_excel(excel_path)
            for _, row in df.iterrows():
                cci_id = row.get('CCI', '')
                nist_control = row.get('NIST 800-53 Control', '')
                if cci_id and nist_control:
                    cci_data[cci_id] = {
                        'definition': str(row.get('CCI Definition', '')),
                        'nist_control': nist_control
                    }
            print(Fore.CYAN + f"Loaded {len(cci_data)} CCIs from {excel_file}." + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"Error loading CCI list: {str(e)}" + Style.RESET_ALL)

    return controls, cci_data

def find_stigs_for_control(control_id, controls, cci_data):
    """Find STIGs associated with a NIST control via CCIs."""
    context = ""
    if control_id in controls:
        context += f"NIST SP 800-53 Control {control_id}: {controls[control_id]}\n\n"

    related_ccis = [cci for cci, data in cci_data.items() if control_id in data['nist_control']]
    if related_ccis:
        context += "Related CCIs:\n"
        for cci in related_ccis:
            context += f"- {cci}: {cci_data[cci]['definition']}\n"
    else:
        context += f"No CCIs found directly mapping to {control_id} in the provided CCI list.\n"

    return context

def main():
    """Run the Compliance LLM Assistant with simplified data loading."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    print(Fore.CYAN + "Loading config..." + Style.RESET_ALL)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(Fore.RED + f"Error loading config: {str(e)}" + Style.RESET_ALL)
        exit(1)

    openrouter_api_key = config.get("OPENROUTER_API_KEY")
    openrouter_base_url = config.get("OPENROUTER_BASE_URL")
    deepseek_model = config.get("DEEPSEEK_MODEL")

    if not all([openrouter_api_key, openrouter_base_url, deepseek_model]):
        print(Fore.RED + "Missing OpenRouter config in config.json" + Style.RESET_ALL)
        exit(1)

    root_dir = os.path.dirname(os.path.abspath(config_path))
    controls, cci_data = load_compliance_data(root_dir, config)

    print(Fore.CYAN + "Welcome to the Compliance LLM Assistant!" + Style.RESET_ALL)
    print(f"Available roles: {', '.join(roles.keys())}")

    while True:
        role = input("Select your role: ").strip()
        if role in roles:
            print(Fore.CYAN + "\n" + roles[role] + Style.RESET_ALL)
            break
        print(Fore.RED + "Invalid role." + Style.RESET_ALL)

    print("\nAsk questions about compliance. Type 'exit' to quit.")

    client = OpenAI(api_key=openrouter_api_key, base_url=openrouter_base_url)

    while True:
        question = input("\nAsk a question: ").strip()
        if question.lower() == "exit":
            print(Fore.CYAN + "Goodbye!" + Style.RESET_ALL)
            break
        if not question:
            print(Fore.YELLOW + "Please enter a question." + Style.RESET_ALL)
            continue

        # Extract control ID from question (e.g., "What STIGs are associated with AC-3?")
        control_id = None
        if "AC-" in question.upper():
            parts = question.upper().split()
            for part in parts:
                if part.startswith("AC-"):
                    control_id = part
                    break

        try:
            if control_id:
                context = find_stigs_for_control(control_id, controls, cci_data)
            else:
                context = "No specific NIST control ID detected in the question."

            prompt = (
                "You are a compliance assistant specializing in NIST SP 800-53 and STIGs. "
                "Use the provided context from compliance documents, including NIST controls and CCI definitions, "
                "to answer the question accurately and specifically. "
                "Focus on mapping NIST controls to STIGs via CCIs when relevant. "
                "If the context lacks sufficient information, supplement with general knowledge or say 'I couldn’t find sufficient information in the provided documents to answer this question fully.'\n\n"
                f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
            )

            response = client.chat.completions.create(
                model=deepseek_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = response.choices[0].message.content
            print(Fore.GREEN + answer + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"Error: {str(e)}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
