import os
import subprocess
import sys

# Define the virtual environment directory
VENV_DIR = "venv"

def create_virtual_env():
    """Create a virtual environment if it doesn't exist."""
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in {VENV_DIR}...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    else:
        print(f"Virtual environment already exists in {VENV_DIR}.")

def get_python_cmd():
    """Get the Python executable path from the virtual environment."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")

def install_requirements():
    """Install dependencies from requirements.txt in the virtual environment."""
    requirements_file = "requirements.txt"
    python_cmd = get_python_cmd()

    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found. Creating it with default dependencies.")
        with open(requirements_file, 'w') as f:
            f.write("requests\nsentence-transformers\nfaiss-cpu\nnumpy\npdfplumber\ntqdm\n")
    
    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.run([python_cmd, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([python_cmd, "-m", "pip", "install", "-r", requirements_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)