##################################################
###             Get data from DISA             ###
##################################################

### required libs
import requests
from colorama import Fore, Back, Style
from datetime import datetime
import json

def load_config(config_file="config.json"):
    """Load configuration settings from a JSON file.

    Args:
        config_file (str): Path to the configuration file. Defaults to 'config.json'.

    Returns:
        dict: Configuration settings.

    Raises:
        FileNotFoundError: If the config file is not found.
        json.JSONDecodeError: If the config file is invalid JSON.
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(Fore.RED + f"Error: Config file '{config_file}' not found.")
        raise
    except json.JSONDecodeError:
        print(Fore.RED + f"Error: Invalid JSON in '{config_file}'.")
        raise

def fetch_disa_data(config, base_path):
    """Fetch DISA data from the specified URL and save it locally.

    Args:
        config (dict): Configuration settings from config file.
        base_path (str): Base directory path for file operations.

    Returns:
        str: Path to the downloaded DISA file.
    """
    month = datetime.now().strftime('%B')
    year = datetime.now().strftime('%Y')
    disa_url = config["disa_url"]
    print(Back.YELLOW + f"Retrieving file from {disa_url}")
    get_disa_file = requests.get(disa_url)
    disa_file = disa_url.split('/')[-1]
    print(f"File {disa_file} was retrieved")

    with open(disa_file, 'wb') as output_file:
        output_file.write(get_disa_file.content)
    print(Fore.GREEN + f"Stored {disa_file} in {base_path}")
    return disa_file

print(Style.RESET_ALL)
