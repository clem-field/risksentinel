##################################################
###           Extract and move files           ###
##################################################
### required libs
import zipfile
import os
import shutil
from colorama import Fore, Style
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

def extract_and_sort_files(config, disa_file, base_path):
    """Extract the DISA zip file and sort contents into SRG and STIG directories.

    Args:
        config (dict): Configuration settings from config file.
        disa_file (str): Path to the downloaded DISA zip file.
        base_path (str): Base directory path for file operations.
    """
    file_location = os.path.join(base_path, config["file_imports_dir"]) + '/'
    srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
    stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

    # Extract files
    print(Fore.MAGENTA + f"Extracting files to: {file_location}")
    with zipfile.ZipFile(disa_file, 'r') as zObject:
        zObject.extractall(path=file_location)

    # Move SRGs and STIGs
    print(Fore.CYAN + f"Checking for SRGs and STIGs in: {file_location}")
    files = os.listdir(file_location)
    for f in files:
        if f.endswith(config["srg_zip_suffix"]):
            print(Fore.CYAN + f"Moving {f} to {srg_folder}")
            shutil.move(file_location + f, srg_folder + f)
        elif f.endswith(config["zip_suffix"]):
            print(Fore.CYAN + f"Moving {f} to {stig_folder}")
            shutil.move(file_location + f, stig_folder + f)

    # Unzip SRGs and STIGs, then sort XML files
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
print(Style.RESET_ALL)

# ---- Old Code ---

# # Extract files
# print(Fore.MAGENTA + f'Extracting files to: {file_location}')
# print(Style.RESET_ALL)
# with zf(disa_file, 'r') as zObject:
#     zObject.extractall(
#        path=file_location)

# # Move SRGs and STIGs
# print(Fore.CYAN + f"Checking for SRGs and STIGs in: {file_location}")
# files = os.listdir(file_location)
# for f in files:
#     if (f.endswith('SRG.zip')):
#         print(Fore.CYAN + f'Moving {f} to {srg_folder}')
#         shutil.move(file_location + f, srg_folder + f)
#     elif (f.endswith('zip')):
#         print(Fore.CYAN + f'Moving {f} to {stig_folder}')
#         shutil.move(file_location + f, stig_folder + f)
# print(Style.RESET_ALL)

# # Unzip SRGs
# for item in os.listdir(srg_folder):
#     if not item.endswith('zip'):
#         continue
#     else:
#         file_name = os.path.abspath(srg_folder + item)
#         zip_ref = zipfile.ZipFile(file_name)
#         zip_ref.extractall(srg_folder)
#         zip_ref.close()
#         os.remove(file_name)

# # Unzip STIGs
# for item in os.listdir(stig_folder):
#     if not item.endswith('zip'):
#         continue
#     else:
#         file_name = os.path.abspath(stig_folder + item)
#         zip_ref = zipfile.ZipFile(file_name)
#         zip_ref.extractall(stig_folder)
#         zip_ref.close()
#         os.remove(file_name)

# # Sort actual SRG's 
# for subdir, dirs, files in os.walk(srg_folder):
#     for f in files:
#         if (f.endswith('xml')):
#             print(Fore.LIGHTYELLOW_EX + f'Moving {f} to {srg_folder}')
#             file_path = os.path.join(subdir, f)
#             shutil.move(file_path, srg_folder + f)

# # Sort actual STIGs 
# for subdir, dirs, files in os.walk(stig_folder):
#     for f in files:
#         if (f.endswith('xml')):
#             print(Fore.LIGHTYELLOW_EX + f'Moving {f} to {stig_folder}')
#             file_path = os.path.join(subdir, f)
#             shutil.move(file_path, stig_folder + f)
# print(Style.RESET_ALL)
