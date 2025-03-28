# pdf_parser.py
import os
import glob
import logging
import pdfplumber

# Configure logging
logging.basicConfig(
    filename='pdf_parser.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_acronym_mapping(docs_dir=None):
    """Load acronym mappings from the latest _STIG_Acronym_List_*.pdf in docs_dir."""
    acronym_map = {}
    if docs_dir is None:
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")

    acronym_files = glob.glob(os.path.join(docs_dir, "_STIG_Acronym_List_*.pdf"))
    if not acronym_files:
        logging.warning(f"No _STIG_Acronym_List_*.pdf found in {docs_dir}")
        return acronym_map

    # Use the latest file based on modification time
    latest_file = max(acronym_files, key=os.path.getmtime)
    logging.info(f"Loading acronym mapping from {latest_file}")

    try:
        with pdfplumber.open(latest_file) as pdf:
            for page in pdf.pages:
                # Extract tables from the page
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if len(row) >= 2 and row[0] and row[1]:  # Ensure row has acronym and meaning
                            acronym = row[0].strip()
                            meaning = row[1].strip().replace('\n', ' ')
                            acronym_map[acronym] = meaning
        logging.info(f"Loaded {len(acronym_map)} acronyms from {latest_file}")
    except Exception as e:
        logging.error(f"Failed to parse {latest_file}: {e}")

    return acronym_map

if __name__ == "__main__":
    # For testing standalone
    acronym_map = load_acronym_mapping()
    print(f"Loaded {len(acronym_map)} acronyms:")
    for acronym, meaning in list(acronym_map.items())[:5]:  # Show first 5 for brevity
        print(f"{acronym}: {meaning}")
