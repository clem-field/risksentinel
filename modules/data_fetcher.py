##################################################
###             Get data from DISA             ###
##################################################

### required libs
import requests
# from zipfile import ZipFile as zf
# import zipfile
# import os
# import shutil
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

# --- Old code ---

# # Set storage locations
# file_location = os.getcwd() + '/file-imports/'
# srg_folder = os.getcwd() + '/srgs/'
# stig_folder = os.getcwd() + '/stigs/'
# base_path = os.getcwd()

# # Set up link
# month = datetime.now().strftime('%B')
# year = datetime.now().strftime('%Y')
# # disa_url = f'https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_SRG-STIG_Library_{month}_{year}.zip'
# # Demo URL
# disa_url ='https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_SRG-STIG_Library_January_2025.zip'

# # Retrieve File
# try:
#     print(Back.YELLOW + f"Looking for file at: {disa_url}")
#     get_disa_file = requests.get(disa_url)
#     print(Style.RESET_ALL)
# except:
#     print(Back.RED + f'No updated file found at {disa_url}')
#     print(Style.RESET_ALL)
#     exit()
# else:
#     print('Success')


# # Set file name
# disa_file = disa_url.split('/')[-1]
# print(f'File {disa_file} was retrieved')

# # Store File
# with open(disa_file,'wb') as output_file:
#     output_file.write(get_disa_file.content)
# print (Fore.GREEN + f'Stored {disa_file} in {base_path}')
# print(Style.RESET_ALL)

# ##################################################
# ###           Extract and move files           ###
# ##################################################

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

# ##################################################
# ###             Clean up Files                 ###
# ##################################################

# # Clean up File Download
# if os.path.exists(disa_file):
#     os.remove(disa_file)
#     print(Fore.RED + f'Removed {disa_file} from {base_path}')
# else:
#     print('File does not exist')

# # Clean up Files / Folders in SRG and STIG Directories
# # Remove non-xml files from SRG directories
# for subdir, dirs, files in os.walk(srg_folder):
#     for f in files:
#         if not (f.endswith('xml')):
#             print(Fore.RED + f'deleting {f} from {srg_folder}')
#             file_path = os.path.join(subdir, f)
#             os.remove(file_path)

# # Remove empty SRG directories
# for root, dirs, files in os.walk(srg_folder, topdown=False):
#         for directory in dirs:
#             dirpath = os.path.join(root, directory)
#             if not os.listdir(dirpath):
#                 os.rmdir(dirpath)
#                 print(Fore.RED + f'Deleting: {dirpath}')

# # Remove non-xml files from STIG directories
# for subdir, dirs, files in os.walk(stig_folder):
#     for f in files:
#         if not (f.endswith('xml')):
#             print(Fore.RED + f'deleting {f} from {stig_folder}')
#             file_path = os.path.join(subdir, f)
#             os.remove(file_path)

# # Remove empty STIG directories
# for root, dirs, files in os.walk(stig_folder, topdown=False):
#         for directory in dirs:
#             dirpath = os.path.join(root, directory)
#             if not os.listdir(dirpath):
#                 os.rmdir(dirpath)
#                 print(Fore.RED + f'Deleting: {dirpath}')

# print(Style.RESET_ALL)
