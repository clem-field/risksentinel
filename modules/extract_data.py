### required libs
import requests
from bs4 import BeautifulSoup as bs
import urllib.request
from zipfile import ZipFile as zf
import zipfile
import os
from pathlib import Path
import shutil
from colorama import Fore, Back, Style
from datetime import datetime
import sys

##################################################
###           Extract and move files           ###
##################################################

# Extract files
print(Fore.MAGENTA + f'Extracting files to: {file_location}')
print(Style.RESET_ALL)
with zf(disa_file, 'r') as zObject:
    zObject.extractall(
       path=file_location)

# Move SRGs and STIGs
print(Fore.CYAN + f"Checking for SRGs and STIGs in: {file_location}")
files = os.listdir(file_location)
for f in files:
    if (f.endswith('SRG.zip')):
        print(Fore.CYAN + f'Moving {f} to {srg_folder}')
        shutil.move(file_location + f, srg_folder + f)
    elif (f.endswith('zip')):
        print(Fore.CYAN + f'Moving {f} to {stig_folder}')
        shutil.move(file_location + f, stig_folder + f)
print(Style.RESET_ALL)

# Unzip SRGs
for item in os.listdir(srg_folder):
    if not item.endswith('zip'):
        continue
    else:
        file_name = os.path.abspath(srg_folder + item)
        zip_ref = zipfile.ZipFile(file_name)
        zip_ref.extractall(srg_folder)
        zip_ref.close()
        os.remove(file_name)

# Unzip STIGs
for item in os.listdir(stig_folder):
    if not item.endswith('zip'):
        continue
    else:
        file_name = os.path.abspath(stig_folder + item)
        zip_ref = zipfile.ZipFile(file_name)
        zip_ref.extractall(stig_folder)
        zip_ref.close()
        os.remove(file_name)

# Sort actual SRG's 
for subdir, dirs, files in os.walk(srg_folder):
    for f in files:
        if (f.endswith('xml')):
            print(Fore.LIGHTYELLOW_EX + f'Moving {f} to {srg_folder}')
            file_path = os.path.join(subdir, f)
            shutil.move(file_path, srg_folder + f)

# Sort actual STIGs 
for subdir, dirs, files in os.walk(stig_folder):
    for f in files:
        if (f.endswith('xml')):
            print(Fore.LIGHTYELLOW_EX + f'Moving {f} to {stig_folder}')
            file_path = os.path.join(subdir, f)
            shutil.move(file_path, stig_folder + f)
print(Style.RESET_ALL)
