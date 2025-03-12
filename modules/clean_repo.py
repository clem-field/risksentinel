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


file_location = os.getcwd() + '/file-imports/'
srg_folder = os.getcwd() + '/srgs/'
stig_folder = os.getcwd() + '/stigs/'
base_path = os.getcwd()

##################################################
###             Clean up Files                 ###
##################################################

# Clean up File Download
if os.path.exists(disa_file):
    os.remove(disa_file)
    print(Fore.RED + f'Removed {disa_file} from {base_path}')
else:
    print('File does not exist')

# Clean up Files / Folders in SRG and STIG Directories
# Remove non-xml files from SRG directories
for subdir, dirs, files in os.walk(srg_folder):
    for f in files:
        if not (f.endswith('xml')):
            print(Fore.RED + f'deleting {f} from {srg_folder}')
            file_path = os.path.join(subdir, f)
            os.remove(file_path)

# Remove empty SRG directories
for root, dirs, files in os.walk(srg_folder, topdown=False):
        for directory in dirs:
            dirpath = os.path.join(root, directory)
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                print(Fore.RED + f'Deleting: {dirpath}')

# Remove non-xml files from STIG directories
for subdir, dirs, files in os.walk(stig_folder):
    for f in files:
        if not (f.endswith('xml')):
            print(Fore.RED + f'deleting {f} from {stig_folder}')
            file_path = os.path.join(subdir, f)
            os.remove(file_path)

# Remove empty STIG directories
for root, dirs, files in os.walk(stig_folder, topdown=False):
        for directory in dirs:
            dirpath = os.path.join(root, directory)
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                print(Fore.RED + f'Deleting: {dirpath}')

print(Style.RESET_ALL)