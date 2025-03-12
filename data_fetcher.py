### required libs
import requests
from bs4 import BeautifulSoup as bs
import urllib.request
from zipfile import ZipFile as zf
import os
import shutil

##################################################
###             Get data from DISA             ###
##################################################
# Get OS Path
# print(os.getcwd())

# Set storage locations
file_location = os.getcwd() + '/file-imports/'
srg_folder = os.getcwd() + '/srg/'
stig_folder = os.getcwd() + '/stigs/'
base_path = os.getcwd()

# Set up link
disa_url = 'https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_SRG-STIG_Library_January_2025.zip'

# Retrieve File
get_disa_file = requests.get(disa_url)

# Set file name
disa_file = disa_url.split('/')[-1]

# Store File
with open(disa_file,'wb') as output_file:
    output_file.write(get_disa_file.content)
print ('STIG Zip retrieved')

# Extract files
with zf(disa_file, 'r') as zObject:
    zObject.extractall(
       path=file_location)
print(f'Files extracted to: {file_location}')

# Clean up File Download
if os.path.exists(disa_file):
    os.remove(disa_file)
    print(f'Removed {disa_file} from {base_path}')
else:
    print('File does not exist')

# Move SRGs
print(f"Checking for SRG's in: {file_location}")
for top, dirs, files in os.walk(file_location):
    for filename in files:
        if not filename.endswith('SRG.zip'):
            continue
        file_path = os.path.join(top, filename)
        with open(file_path, 'r') as f:
            if '* Test Outcome : FAIL' in f.read():
                print(f"Moving file: {filename} to {srg_folder}")
                shutil.move(file_path, os.path.join(srg_folder, filename))