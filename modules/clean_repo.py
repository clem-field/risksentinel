##################################################
###             Clean up Files                 ###
##################################################

### required libs
import os
from colorama import Fore, Style
import json
import sys

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

def clean_up_files(config, disa_file, base_path):
    """Clean up temporary files and directories, keeping only XML files.

    Args:
        config (dict): Configuration settings from config file.
        disa_file (str): Path to the downloaded DISA zip file.
        base_path (str): Base directory path for file operations.
    """
    srg_folder = os.path.join(base_path, config["srg_dir"]) + '/'
    stig_folder = os.path.join(base_path, config["stig_dir"]) + '/'

    # Remove downloaded zip
    if os.path.exists(disa_file):
        os.remove(disa_file)
        print(Fore.RED + f"Removed {disa_file} from {base_path}")
    else:
        print("File does not exist")

    # Clean non-XML files and empty directories
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

print(Style.RESET_ALL)


# ---- Old Code ---

# file_location = os.getcwd() + '/file-imports/'
# srg_folder = os.getcwd() + '/srgs/'
# stig_folder = os.getcwd() + '/stigs/'
# base_path = os.getcwd()



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