# mitre_work
This repository hosts python scripts that will allow a user to retrieve the unclassified Security Requirements Guides (SRGs) and Security Technical Implementation Guides (STIGs) from public.cyber.mil.

## Highlights
- Retrieves the updated zip file
- Unzips the file to a temp location
- Sorts the zipped SRG's and STIG's to their appropriate folders
- Unzips all packages
- Moves the xccdf files to their final location
- Cleans up (deletes) all temp files that are not needed

## Requirements
- Python 3.8 or higher
- Git (to clone the repo)
- Internet access (for initial data download)

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/clem-field/mitre_work.git
   ```

2. **Run the Script**:
   - Use `get_srg_stig.py`
        - example: `python3 get_srg_stig.py` in terminal of your choice and from `mitre_work` folder

## Dependencies
Specified in `requirements.txt`:
- `requests`
- `bs4`
- `urllib`
- `ZipFile`
- `os`
- `Path`
- `shutil`
- `colorama`
- `datetime`
- `sys`


## File Structure
mitre_work
|   
|   catalogs
|   |
|   -   test.sh - This is a place holder until control catalogs are imported
|   |
|   file-imports
|   |
|   |   *** Various temp files and folders during import and file parsing ***
|   |   *** Files stored here will be deleted when executing clean_repo   ***
|   |
|   modules
|   |
|   -   clean_repo.py - module that cleans the file-imports, srgs and stigs folders
|   -   data_fetcher.py - retrieves and stores files from various sources
|   -   extract_data.py - extracts zip files to srgs and stigs then moves xccdf files
|   |
|   srgs
|   |
|   |   *** Stores the Security Requirement Guides in xccdf.xml ***
|   |
|   stigs
|   |
|   |   *** Stores the Security Technical Implementation Guides (STIGs) in xccdf.xml ****
|   |
|   venv - folders and resources for setting up a virtual environment
|   |
|   -   bin
|   -   include
|   -   lib
|   -   share
|   -   .gitignore
|   -   pyvenv.cfg
|   |
-   config.json
-   get_srg_stig.py - performs all functions of the individual scripts in `/modules`
-   data_fetcher_ky.py
-   license
-   README.MD (You are Here)
-   requirements.txt - required libraries for running python
-   setup_demo.py
-   setup_environment.py

## Contributing
Contributions are welcome! Open issues or submit pull requests to enhance features, fix bugs, or optimize performance.

## License
This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.

