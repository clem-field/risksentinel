### required libs
import requests
from bs4 import BeautifulSoup as bs
import urllib.request
from zipfile import ZipFile as zf
import zipfile
import os
import shutil

##################################################
###             Get data from DISA             ###
##################################################
# Get OS Path
# print(os.getcwd())

# Set storage locations
file_location = os.getcwd() + '/file-imports/'
srg_folder = os.getcwd() + '/srgs/'
stig_folder = os.getcwd() + '/stigs/'
base_path = os.getcwd()

# Set up link
disa_url = 'https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_SRG-STIG_Library_January_2025.zip'

# Retrieve File
print(f"Retrieving file from {disa_url}")
get_disa_file = requests.get(disa_url)

# Set file name
disa_file = disa_url.split('/')[-1]
print(f'File {disa_file} was retrieved')

# Store File
with open(disa_file,'wb') as output_file:
    output_file.write(get_disa_file.content)
print (f'Stored {disa_file} in {base_path}')

# Extract files
print(f'Extracting files to: {file_location}')
with zf(disa_file, 'r') as zObject:
    zObject.extractall(
       path=file_location)

# Move SRGs and STIGs
print(f"Checking for SRGs and STIGs in: {file_location}")
files = os.listdir(file_location)
for f in files:
    if (f.endswith('SRG.zip')):
        print(f'Moving {f} to {srg_folder}')
        shutil.move(file_location + f, srg_folder + f)
    elif (f.endswith('zip')):
        print(f'Moving {f} to {stig_folder}')
        shutil.move(file_location + f, stig_folder + f)

# Clean up File Download
if os.path.exists(disa_file):
    os.remove(disa_file)
    print(f'Removed {disa_file} from {base_path}')
else:
    print('File does not exist')

# Unzip SRGs and STIGs
for item in os.listdir(srg_folder):
    if not item.endswith('zip'):
        continue
    else:
        file_name = os.path.abspath(srg_folder + item)
        zip_ref = zipfile.ZipFile(file_name)
        zip_ref.extractall(srg_folder)
        zip_ref.close()
        os.remove(file_name)

for item in os.listdir(stig_folder):
    if not item.endswith('zip'):
        continue
    else:
        file_name = os.path.abspath(stig_folder + item)
        zip_ref = zipfile.ZipFile(file_name)
        zip_ref.extractall(stig_folder)
        zip_ref.close()
        os.remove(file_name) 