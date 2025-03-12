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
   - Use `data_fetcher.py`
    - example: `python3 data_fetcher.py` in terminal of your choice and from `mitre_work` folder

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

## Contributing
Contributions are welcome! Open issues or submit pull requests to enhance features, fix bugs, or optimize performance.

## License
This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.

