from flask import Flask, render_template, request
import os
import requests
import shutil
import zipfile
import json
from colorama import Fore, Style
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data_fetcher', methods=['POST'])
def run_python():
    if request.method == 'POST':
        def load_config(config_file="config.json"):
            """Load configuration settings from a JSON file.

            Args:
                config_file (str): Path to the configuration file. Defaults to 'config.json'.

            Returns:
                dict: Configuration settings.

            Raises:
                FileNotFoundError: If the config file is not found.
                json.JSONDecodeError: If the config file contains invalid JSON.
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

        def get_previous_month(month, year, steps_back):
            """Calculate the month and year a specified number of months before the given date.

            Args:
                month (str): Full month name (e.g., "October").
                year (str): Four-digit year (e.g., "2023").
                steps_back (int): Number of months to go back.

            Returns:
                tuple: (month, year) of the previous month as strings.
            """
            date = datetime.strptime(f"{month} {year}", "%B %Y")
            for _ in range(steps_back):
                date = date.replace(day=1) - timedelta(days=1)
            return date.strftime("%B"), date.strftime("%Y")

        def fetch_disa_data(config, base_path):
            """Fetch DISA data from a URL and save it locally, with fallback to previous months.

            Args:
                config (dict): Configuration settings from the config file.
                base_path (str): Base directory path for file operations.

            Returns:
                str: Path to the downloaded DISA file.

            Raises:
                ValueError: If no valid ZIP file is found after trying the current and previous months.
            """
            disa_url_template = config["disa_url"]
            month = datetime.now().strftime('%B')
            year = datetime.now().strftime('%Y')
            
            # Try current month and two previous months
            for i in range(3):
                disa_url = disa_url_template.format(month=month, year=year)
                print(f"Attempting to retrieve file from {disa_url}")
                response = requests.get(disa_url)
                
                # Validate HTTP response and content type
                if response.status_code == 200 and 'application/zip' in response.headers.get('Content-Type', ''):
                    disa_file = disa_url.split('/')[-1]
                    with open(disa_file, 'wb') as output_file:
                        output_file.write(response.content)
                    print(f"Stored {disa_file} in {base_path}")
                    return disa_file
                
                # If retrieval fails, try the previous month
                month, year = get_previous_month(month, year, 1)
            
            raise ValueError("No valid ZIP file found in the last 3 months")

        def extract_and_sort_files(config, disa_file, base_path):
            """Extract the DISA ZIP file and sort contents into SRG and STIG directories.

            Args:
                config (dict): Configuration settings from the config file.
                disa_file (str): Path to the downloaded DISA ZIP file.
                base_path (str): Base directory path for file operations.
            """
            file_location = os.path.join(base_path, config["file_imports_dir"]) + '/'
            srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
            stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

            # Extract files from the ZIP
            print(Fore.MAGENTA + f"Extracting files to: {file_location}")
            with zipfile.ZipFile(disa_file, 'r') as zObject:
                zObject.extractall(path=file_location)

            # Sort SRGs and STIGs into respective folders
            print(Fore.CYAN + f"Checking for SRGs and STIGs in: {file_location}")
            files = os.listdir(file_location)
            for f in files:
                if f.endswith(config["srg_zip_suffix"]):
                    print(Fore.CYAN + f"Moving {f} to {srg_folder}")
                    shutil.move(file_location + f, srg_folder + f)
                elif f.endswith(config["zip_suffix"]):
                    print(Fore.CYAN + f"Moving {f} to {stig_folder}")
                    shutil.move(file_location + f, stig_folder + f)

            # Extract nested ZIPs and move XML files
            for folder, suffix in [(srg_folder, "SRG"), (stig_folder, "STIG")]:
                for item in os.listdir(folder):
                    if not item.endswith(config["zip_suffix"]):
                        continue
                    file_name = os.path.abspath(folder + item)
                    with zipfile.ZipFile(file_name, 'r') as zip_ref:
                        zip_ref.extractall(folder)
                    os.remove(file_name)

                for subdir, _, files in os.walk(folder):
                    for f in files:
                        if f.endswith(config["xml_suffix"]):
                            print(Fore.LIGHTYELLOW_EX + f"Moving {f} to {folder}")
                            shutil.move(os.path.join(subdir, f), folder + f)

        def clean_up_files(config, disa_file, base_path):
            """Remove temporary files and directories, keeping only XML files.

            Args:
                config (dict): Configuration settings from the config file.
                disa_file (str): Path to the downloaded DISA ZIP file.
                base_path (str): Base directory path for file operations.
            """
            srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
            stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

            # Remove the downloaded ZIP file
            if os.path.exists(disa_file):
                os.remove(disa_file)
                print(Fore.RED + f"Removed {disa_file} from {base_path}")
            else:
                print("File does not exist")

            # Clean up non-XML files and empty directories
            for folder in [srg_folder, stig_folder]:
                for subdir, dirs, files in os.walk(folder):
                    for f in files:
                        if not f.endswith(config["xml_suffix"]):
                            file_path = os.path.join(subdir, f)
                            print(Fore.RED + f"Deleting {f} from {folder}")
                            os.remove(file_path)

                for root, dirs, _ in os.walk(folder, topdown=False):
                    for directory in dirs:
                        dirpath = os.path.join(root, directory)
                        if not os.listdir(dirpath):
                            os.rmdir(dirpath)
                            print(Fore.RED + f"Deleting: {dirpath}")

        def main():
            """Main function to fetch, extract, and clean DISA data.

            Guide for Developers:
                - Modify 'config.json' to change URLs, directories, or file suffixes.
                - Ensure required directories exist and have write permissions.
                - Dependencies: requests, colorama (see requirements.txt).
                - Runs in the current working directory; adjust paths if needed.
            """
            base_path = os.getcwd()
            config = load_config()

            # Create required directories if they don't exist
            for dir_key in ["file_imports_dir", "srg_dir", "stig_dir"]:
                os.makedirs(os.path.join(base_path, config[dir_key]), exist_ok=True)

            # Execute the workflow
            disa_file = fetch_disa_data(config, base_path)
            extract_and_sort_files(config, disa_file, base_path)
            clean_up_files(config, disa_file, base_path)
            print(Style.RESET_ALL)

        if __name__ == "__main__":
            main()

        return 'Python code executed successfully!'

if __name__ == '__main__':
    app.run(debug=True)