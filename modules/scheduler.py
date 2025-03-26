import schedule
import time
import subprocess
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='data_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_data_fetcher():
    """Run the data_fetcher.py script and log the outcome."""
    script_path = os.path.join("modules", "data_fetcher.py")
    python_path = os.path.join("venv", "bin", "python") if os.name != "nt" else os.path.join("venv", "Scripts", "python.exe")
    
    if not os.path.exists(script_path):
        logging.error(f"Script not found: {script_path}")
        return
    
    try:
        result = subprocess.run([python_path, script_path], check=True, capture_output=True, text=True)
        logging.info("Data fetcher ran successfully.")
        logging.debug(f"Output: {result.stdout}")
        if result.stderr:
            logging.warning(f"Errors/Warnings: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Data fetcher failed with exit code {e.returncode}: {e.stderr}")
    except Exception as e:
        logging.error(f"Unexpected error running data fetcher: {str(e)}")

def schedule_updates():
    """Schedule periodic updates."""
    # schedule.every().day.at("02:00").do(run_data_fetcher). # Every day at 2am
    # schedule.every().hour.do(run_data_fetcher)  # Hourly
    schedule.every().monday.at("09:00").do(run_data_fetcher)  # Weekly on Monday
    # schedule.every(2).days.at("03:00").do(run_data_fetcher)  # Every 2 days

    logging.info("Scheduler started. Waiting for scheduled tasks...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        schedule_updates()
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user.")
    except Exception as e:
        logging.error(f"Scheduler crashed: {str(e)}")