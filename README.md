# mitre_work
This repository hosts python scripts that will allow a user to retrieve the unclassified Security Requirements Guides (SRGs) and Security Technical Implementation Guides (STIGs) from public.cyber.mil.

## Highlights
- Retrieves the updated zip file
   - Dynamically checks for previous 3 months
- Unzips the file to a temp location
- Sorts the zipped SRG's and STIG's to their appropriate folders
- Unzips all SRG's and STIG's
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
   - Option 1:
         - Use `get_srg_stig.py`
            - example: `python3 get_srg_stig.py` in terminal of your choice and from `mitre_work` folder
   - Option 2:
         1. Run `setup_environment.py`
            - This will check for a venv and initiate it if not
         2. Follow prompts

## Dependencies
Specified in `requirements.txt`:
- `requests`
- `colorama`
- `openai`
- `openpyxl`

These are only required if running locally. The virtual environment (venv) will install these when activated.

## File Structure
```
mitre_work/
|--catalogs/
|   |--test.sh - This is a place holder until control catalogs are imported
|--file-imports/
|   |--*** Various temp files and folders during import and file parsing ***
|   |--*** Files stored here will be deleted when executing clean_repo   ***
|--modules/
|   |--clean_repo.py - module that cleans the file-imports, srgs and stigs folders
|   |--data_fetcher.py - retrieves and stores files from various sources
|   |--extract_data.py - extracts zip files to srgs and stigs then moves xccdf files
|--srgs/
|   |--*** Stores the Security Requirement Guides in xccdf.xml ***
|--stigs/
|   |--*** Stores the Security Technical Implementation Guides (STIGs) in xccdf.xml ****
|--venv/ - folders and resources for setting up a virtual environment
|   |--bin/
|   |--include/
|   |--lib/
|   |--share/
|   |--.gitignore
|   |--pyvenv.cfg
|--config.json
|--get_srg_stig.py - performs all functions of the individual scripts in `/modules` and in local python
|--data_fetcher.py - requires venv to be running
|--license
|--README.MD (You are Here)
|--requirements.txt - required libraries for running python
|--setup_demo.py
|--setup_environment.py
```
## Contributing
Contributions are welcome! Open issues or submit pull requests to enhance features, fix bugs, or optimize performance.

Thank you to all of those that have already contributed to the features of this repo.

## License
This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.

---

## Setting Up Your `config.json`

To run this project, you need to create a `config.json` file based on the provided `config.json.template`. This file contains essential configuration settings, including an API key for OpenRouter. Follow the steps below to set it up.

### Step 1: Copy the Template
The repository includes a `config.json.template` file. Start by making a copy of it and renaming it to `config.json`:

```bash
cp config.json.template config.json
```

### Step 2: Understand the Template
The `config.json.template` looks like this:

```json
{
    "disa_url": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_SRG-STIG_Library_{month}_{year}.zip",
    "nist_800_53_attack_mapping_url": "https://center-for-threat-informed-defense.github.io/mappings-explorer/data/nist_800_53/attack-14.1/nist_800_53-rev5/enterprise/nist_800_53-rev5_attack-14.1-enterprise_json.json",
    "cci_list_url": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_CCI_List.zip",
    "file_imports_dir": "file-imports",
    "srg_dir": "srgs",
    "stig_dir": "stigs",
    "cci_list_dir": "data/cci_lists",
    "srg_zip_suffix": "_SRG.zip",
    "zip_suffix": ".zip",
    "xml_suffix": ".xml",
    "baselines": {
        "high": "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline_profile.json",
        "moderate": "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_MODERATE-baseline_profile.json",
        "low": "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_LOW-baseline_profile.json"
    },
    "nist_sp800_53_catalog_url": "https://csrc.nist.gov/files/pubs/sp/800/53/r5/upd1/final/docs/sp800-53r5-control-catalog.xlsx",
    "OPENROUTER_API_KEY": "your_openrouter_api_key_here",
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "DEEPSEEK_MODEL": "deepseek/deepseek-r1:free"
}
```

Most values can remain as they are, as they point to publicly accessible resources or define directory/file naming conventions. However, you **must** replace the `OPENROUTER_API_KEY` placeholder with your own API key.

### Step 3: Generate an OpenRouter API Key
The project uses OpenRouter to access AI models (e.g., DeepSeek). To generate your own `OPENROUTER_API_KEY`:

1. **Visit OpenRouter**:
   - Go to [https://openrouter.ai/](https://openrouter.ai/).

2. **Sign Up or Log In**:
   - Create an account or log in with an existing one (e.g., via GitHub or Google).

3. **Access API Keys**:
   - Once logged in, navigate to the "API Keys" section (usually under your account settings or dashboard).

4. **Create a New Key**:
   - Click "Generate API Key" or a similar option.
   - Give it a descriptive name (e.g., "ComplianceLLM").
   - Copy the generated key (it will look something like `sk-or-v1-...`).

5. **Secure Your Key**:
   - Do not share this key publicly. Store it securely and only use it in your `config.json`.

### Step 4: Update `config.json`
Open your `config.json` in a text editor and replace the placeholder `your_openrouter_api_key_here` with the key you generated. For example:

```json
"OPENROUTER_API_KEY": "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
```

### Step 5: Customize Other Settings (Optional)
- **Directories**: The default values (`file-imports`, `srgs`, `stigs`, `data/cci_lists`) work fine for most users. Change them only if you need custom folder names or locations.
- **Model**: The `DEEPSEEK_MODEL` is set to `deepseek/deepseek-r1:free`. If you have access to other models via OpenRouter and prefer a different one, update this field (check OpenRouter’s documentation for available models).
- **URLs**: The provided URLs are current as of March 2025. If they become outdated, update them with the latest links from NIST, DISA, or the Center for Threat-Informed Defense.

### Step 6: Save and Verify
- Save your `config.json` in the project root directory (same location as `setup_environment.py`).
- Ensure the file is valid JSON (no trailing commas, correct quotes). You can test it with a JSON validator or by running the project.

### Step 7: Run the Project
With your `config.json` ready, activate the virtual environment and run the setup script:

```bash
python3 setup_environment.py
```

Follow the prompts to install dependencies and fetch data. The `OPENROUTER_API_KEY` will be used by `compliance_llm.py` to query the LLM.

### Troubleshooting
- **API Key Error**: If you see "Missing OpenRouter config" or an authentication error, double-check your `OPENROUTER_API_KEY`.
- **URL Issues**: If a download fails (e.g., 404 error), verify the URLs in `config.json` against the latest sources.
- **Permissions**: Ensure you have write access to the directories specified in `config.json`.

Now you’re set to use the Compliance LLM Assistant with your custom configuration!

