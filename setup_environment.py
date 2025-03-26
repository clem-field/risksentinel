import os
import subprocess
import sys
import platform

# Define paths and settings
VENV_DIR = "venv"  # Name of the virtual environment directory
REQUIREMENTS_FILE = "requirements.txt"
DATA_FETCHER_SCRIPT = "modules/data_fetcher.py"  # Script to load data
COMPLIANCE_LLM_SCRIPT = "modules/compliance_llm.py"  # Script to run LLM

def is_venv_active():
    """Check if a virtual environment is currently active.

    Returns:
        bool: True if a virtual environment is active, False otherwise.
    """
    return sys.prefix != sys.base_prefix

def create_venv():
    """Create a virtual environment if it doesn't exist.

    Raises:
        subprocess.CalledProcessError: If venv creation fails.
    """
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in '{VENV_DIR}'...")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
        print("Virtual environment created.")
    else:
        print(f"Virtual environment '{VENV_DIR}' already exists.")

def get_pip_path():
    """Get the path to pip in the virtual environment based on OS.

    Returns:
        str: Path to pip executable.

    Guide for Developers:
        - Modify VENV_DIR at the top if you want a different venv name.
    """
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "pip")

def get_python_path():
    """Get the path to python in the virtual environment based on OS.

    Returns:
        str: Path to python executable.
    """
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def install_requirements():
    """Install dependencies from requirements.txt.

    Raises:
        FileNotFoundError: If requirements.txt is missing.
        subprocess.CalledProcessError: If pip install fails.
    """
    if not os.path.exists(REQUIREMENTS_FILE):
        print(f"Error: '{REQUIREMENTS_FILE}' not found. Please create it with required dependencies.")
        sys.exit(1)

    pip_path = get_pip_path()
    print(f"Installing dependencies from '{REQUIREMENTS_FILE}'...")
    subprocess.check_call([pip_path, "install", "-r", REQUIREMENTS_FILE])
    print("Dependencies installed.")

def run_script(script_path):
    """Run a specified script in the virtual environment.

    Args:
        script_path (str): Path to the script to execute.

    Raises:
        subprocess.CalledProcessError: If the script execution fails.
    """
    if not os.path.exists(script_path):
        print(f"Error: '{script_path}' not found. Skipping execution.")
        return False

    python_path = get_python_path()
    print(f"Running '{script_path}'...")
    try:
        subprocess.check_call([python_path, script_path])
        print(f"Finished running '{script_path}'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running '{script_path}': {e}")
        return False

def main():
    """Main function to set up environment, load data, and run scripts.

    Guide for Developers:
        - Ensure Python 3.6+ is installed.
        - Place 'requirements.txt' and 'config.json' in the same directory.
        - Customize VENV_DIR, REQUIREMENTS_FILE, DATA_FETCHER_SCRIPT, or COMPLIANCE_LLM_SCRIPT at the top if needed.
        - Run with: python setup_environment.py
    """
    if is_venv_active():
        print("Virtual environment is already active.")
    else:
        create_venv()

    install_requirements()

    # Prompt to run data_fetcher.py to load compliance data
    run_data_fetcher = input(f"Do you want to run '{DATA_FETCHER_SCRIPT}' to load compliance data now? (y/n): ").strip().lower()
    data_fetcher_success = False
    if run_data_fetcher == 'y':
        data_fetcher_success = run_script(DATA_FETCHER_SCRIPT)
    else:
        print(f"You can activate the virtual environment and run '{DATA_FETCHER_SCRIPT}' manually:")
        if platform.system() == "Windows":
            print(f"  {VENV_DIR}\\Scripts\\activate")
        else:
            print(f"  source {VENV_DIR}/bin/activate")
        print(f"Then run: python {DATA_FETCHER_SCRIPT}")

    # Prompt to run compliance_llm.py if data_fetcher.py ran successfully or user opts to proceed
    if data_fetcher_success or run_data_fetcher != 'y':
        run_compliance_llm = input(f"Do you want to run '{COMPLIANCE_LLM_SCRIPT}' to use the Compliance LLM now? (y/n): ").strip().lower()
        if run_compliance_llm == 'y':
            run_script(COMPLIANCE_LLM_SCRIPT)
        else:
            print(f"You can activate the virtual environment and run '{COMPLIANCE_LLM_SCRIPT}' manually:")
            if platform.system() == "Windows":
                print(f"  {VENV_DIR}\\Scripts\\activate")
            else:
                print(f"  source {VENV_DIR}/bin/activate")
            print(f"Then run: python {COMPLIANCE_LLM_SCRIPT}")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user.")
        sys.exit(0)
