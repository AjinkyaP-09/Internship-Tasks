import os
import zipfile
import datetime
import json
import subprocess
import logging
import argparse
import requests
from pathlib import Path

# --- Configuration Loading ---
def load_config(config_path):
    """
    Loads configuration settings from a specified JSON file.

    Args:
        config_path (str): The path to the configuration JSON file.

    Returns:
        dict: A dictionary containing the configuration settings.
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        exit(1)
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from configuration file: {config_path}")
        exit(1)

# --- Logging Setup ---
def setup_logging(log_file):
    """
    Configures the logging system to write messages to a file and the console.

    Args:
        log_file (Path): The path to the log file.
    """
    logging.basicConfig(
        level=logging.DEBUG, # Changed to DEBUG for more verbose output during troubleshooting
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler() # Also log to console
        ]
    )

# --- Backup Creation ---
def create_backup(project_path, local_backup_base_dir, project_name):
    """
    Creates a ZIP archive of the specified project directory.

    Args:
        project_path (str): The absolute path to the project directory to back up.
        local_backup_base_dir (str): The base directory for local backups (e.g., '~/backups').
        project_name (str): The name of the project, used for naming and structuring backups.

    Returns:
        Path or None: The path to the created backup file if successful, None otherwise.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{project_name}_{timestamp}.zip"

    # Construct the target backup directory: ~/backups/ProjectName/YYYY/MM/DD/
    today = datetime.datetime.now()
    year_dir = today.strftime("%Y")
    month_dir = today.strftime("%m")
    day_dir = today.strftime("%d")

    # Resolve the base directory (e.g., expand '~') and append project/date structure
    target_dir = Path(local_backup_base_dir).expanduser() / project_name / year_dir / month_dir / day_dir
    target_dir.mkdir(parents=True, exist_ok=True) # Create directories if they don't exist

    backup_filepath = target_dir / backup_filename

    try:
        logging.info(f"Creating backup of '{project_path}' to '{backup_filepath}'...")
        file_count = 0
        # Create a zip file and add all contents of the project_path
        with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(project_path):
                for file in files:
                    file_path = Path(root) / file
                    # arcname is the path inside the zip file, relative to the project_path
                    arcname = file_path.relative_to(project_path)
                    logging.debug(f"Adding file to zip: {file_path} as {arcname}") # Added debug log
                    zipf.write(file_path, arcname)
                    file_count += 1
        
        if file_count == 0:
            logging.warning(f"No files were found in '{project_path}' to add to the backup. The created zip might be empty.")
        logging.info(f"Backup created successfully: {backup_filepath} (Contains {file_count} files).") # Updated log
        return backup_filepath
    except FileNotFoundError:
        logging.error(f"Project path '{project_path}' not found. Cannot create backup.")
        return None
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return None

# --- Google Drive Integration ---
def upload_to_gdrive(local_path, rclone_remote, google_drive_folder_name):
    """
    Uploads a local file to Google Drive using rclone.

    Args:
        local_path (Path): The path to the local file to upload.
        rclone_remote (str): The name of the rclone remote configured for Google Drive.
        google_drive_folder_name (str): The name of the folder in Google Drive to upload to.

    Returns:
        bool: True if upload is successful, False otherwise.
    """
    if not local_path:
        logging.warning("No local backup file to upload to Google Drive.")
        return False

    # Construct the rclone destination path
    destination = f"{rclone_remote}:{google_drive_folder_name}"
    
    logging.info(f"Uploading '{local_path}' to Google Drive folder '{destination}'...")
    try:
        # Execute rclone copy command
        result = subprocess.run(
            ["rclone", "copy", str(local_path), destination],
            capture_output=True, # Capture stdout and stderr
            text=True,           # Decode stdout/stderr as text
            check=True           # Raise CalledProcessError if command returns non-zero exit code
        )
        logging.info(f"Google Drive upload successful. Output:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Google Drive upload failed. Error:\n{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error("rclone command not found. Please ensure rclone is installed and in your system's PATH.")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during rclone upload: {e}")
        return False

# --- Rotational Backup Strategy ---
def apply_retention_policy(local_backup_base_dir, project_name, retention_settings):
    """
    Applies the rotational backup policy to delete old backups based on retention settings.

    Args:
        local_backup_base_dir (str): The base directory for local backups.
        project_name (str): The name of the project.
        retention_settings (dict): A dictionary with 'daily', 'weekly', and 'monthly' retention counts.
    """
    logging.info("Applying retention policy...")
    backup_root_dir = Path(local_backup_base_dir).expanduser() / project_name
    
    if not backup_root_dir.exists():
        logging.info(f"Backup root directory '{backup_root_dir}' does not exist. No retention to apply.")
        return

    all_backups = []
    # Walk through the directory structure to find all backup files
    for root, _, files in os.walk(backup_root_dir):
        for file in files:
            # Check if it's a zip file and matches the project naming convention
            if file.endswith(".zip") and file.startswith(project_name):
                try:
                    # Extract timestamp from filename: ProjectName_YYYYMMDD_HHMMSS.zip
                    parts = file.split('_')
                    if len(parts) >= 3:
                        date_str = parts[1] # YYYYMMDD
                        time_str = parts[2].split('.')[0] # HHMMSS
                        backup_datetime = datetime.datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                        all_backups.append({'path': Path(root) / file, 'datetime': backup_datetime})
                except ValueError:
                    logging.warning(f"Could not parse timestamp from filename: {file}")
                    continue

    # Sort all backups by datetime, from newest to oldest
    all_backups.sort(key=lambda x: x['datetime'], reverse=True)

    retained_files = set() # Use a set to store paths of files to be retained, avoiding duplicates
    deleted_count = 0

    # 1. Daily Retention: Keep the 'daily' most recent backups overall
    logging.info(f"Applying daily retention (keeping last {retention_settings['daily']} backups overall)...")
    for i, backup in enumerate(all_backups):
        if i < retention_settings['daily']:
            retained_files.add(backup['path'])
        else:
            # Once daily limit is met, no more files are automatically retained by this policy
            break 

    # 2. Weekly Retention: Keep the 'weekly' most recent Sunday backups
    logging.info(f"Applying weekly retention (keeping last {retention_settings['weekly']} Sundays)...")
    weekly_backups = [b for b in all_backups if b['datetime'].weekday() == 6] # Sunday is 6
    for i, backup in enumerate(weekly_backups):
        if i < retention_settings['weekly']:
            retained_files.add(backup['path'])
        else:
            break

    # 3. Monthly Retention: Keep the latest backup for each of the last 'monthly' distinct months
    logging.info(f"Applying monthly retention (keeping latest for last {retention_settings['monthly']} months)...")
    monthly_retained_map = {} # Key: (year, month), Value: latest_backup_path for that month
    for backup in all_backups:
        year_month = (backup['datetime'].year, backup['datetime'].month)
        # If this month is not yet in the map, or if this backup is newer than the one currently mapped for this month
        if year_month not in monthly_retained_map or backup['datetime'] > monthly_retained_map[year_month]['datetime']:
            monthly_retained_map[year_month] = backup

    # Sort the months from newest to oldest and select the latest for the last X months
    sorted_months = sorted(monthly_retained_map.keys(), reverse=True)
    for i, (year, month) in enumerate(sorted_months):
        if i < retention_settings['monthly']:
            retained_files.add(monthly_retained_map[(year, month)]['path'])
        else:
            break

    # Delete files that are not in the retained_files set
    logging.info("Identifying and deleting old backups...")
    for backup in all_backups:
        if backup['path'] not in retained_files:
            try:
                os.remove(backup['path'])
                logging.info(f"Deleted old backup: {backup['path']}")
                deleted_count += 1
                # Attempt to remove empty parent directories (YYYY/MM/DD)
                current_dir = backup['path'].parent
                # Walk up the directory tree until backup_root_dir or a non-empty directory is found
                while current_dir != backup_root_dir and not list(current_dir.iterdir()):
                    os.rmdir(current_dir)
                    logging.info(f"Removed empty directory: {current_dir}")
                    current_dir = current_dir.parent
            except OSError as e:
                logging.error(f"Error deleting backup {backup['path']}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred during deletion of {backup['path']}: {e}")
    
    logging.info(f"Retention policy applied. Total deleted: {deleted_count} files.")
    if deleted_count > 0:
        logging.info("Deletion summary: See log for details on deleted files.")
    else:
        logging.info("No old backups found to delete based on current policy.")


# --- Notification ---
def send_notification(webhook_url, project_name, backup_date, success_status):
    """
    Sends a POST cURL request to a specified webhook URL.

    Args:
        webhook_url (str): The URL to send the POST request to.
        project_name (str): The name of the project.
        backup_date (str): The timestamp of the backup (ISO format).
        success_status (bool): True if the backup was successful, False otherwise.
    
    Returns:
        bool: True if notification was sent successfully, False otherwise.
    """
    if not webhook_url:
        logging.warning("Webhook URL not configured. Skipping notification.")
        return False

    payload = {
        "project": project_name,
        "date": backup_date,
        "status": "BackupSuccessful" if success_status else "BackupFailed"
    }
    headers = {"Content-Type": "application/json"}

    logging.info(f"Sending notification to {webhook_url} with status: {payload['status']}...")
    try:
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        logging.info(f"Notification sent successfully. Response: {response.status_code}")
        return True
    except requests.exceptions.Timeout:
        logging.error(f"Notification request timed out after 10 seconds to {webhook_url}.")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending notification to {webhook_url}: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending notification: {e}")
        return False

# --- Main Script Logic ---
def main():
    """
    Main function to parse arguments, load config, and orchestrate the backup process.
    """
    parser = argparse.ArgumentParser(description="Automated Backup and Rotation Script with Google Drive Integration.")
    parser.add_argument("--config", required=True, help="Path to the configuration JSON file.")
    parser.add_argument("--project-path", required=True, help="Path to the project directory to be backed up.")
    parser.add_argument("--no-notify", action="store_true", help="Disable sending cURL notification.")
    args = parser.parse_args()

    config = load_config(args.config)

    project_name = config.get("project_name")
    local_backup_base_dir = config.get("local_backup_base_dir", str(Path.home() / "backups")) # Default to ~/backups
    rclone_remote_name = config.get("rclone_remote_name")
    google_drive_folder_name = config.get("google_drive_folder_name")
    retention_settings = config.get("retention", {"daily": 7, "weekly": 4, "monthly": 3})
    webhook_url = config.get("webhook_url")

    # Validate essential configuration parameters
    if not all([project_name, rclone_remote_name, google_drive_folder_name]):
        logging.error("Missing essential configuration parameters (project_name, rclone_remote_name, google_drive_folder_name). Please check your config.json.")
        exit(1)

    # Setup logging. The log file will be inside the project's backup base directory.
    log_file_path = Path(local_backup_base_dir).expanduser() / project_name / "backup.log"
    log_file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure the directory for the log file exists
    setup_logging(log_file_path)
    
    logging.info(f"Starting backup process for project: {project_name}")
    logging.info(f"Project path: {args.project_path}")

    backup_filepath = None
    backup_success = False
    
    try:
        backup_filepath = create_backup(args.project_path, local_backup_base_dir, project_name)
        
        if backup_filepath:
            upload_status = upload_to_gdrive(backup_filepath, rclone_remote_name, google_drive_folder_name)
            if upload_status:
                logging.info("Backup successfully created and uploaded.")
                backup_success = True
            else:
                logging.error("Backup created but failed to upload to Google Drive.")
        else:
            logging.error("Backup creation failed. Skipping upload and notification.")
    except Exception as e:
        logging.critical(f"A critical error occurred during backup or upload: {e}")
        backup_success = False # Ensure status is failed if critical error occurs

    # Apply retention policy regardless of backup/upload success, as it cleans up old files.
    try:
        apply_retention_policy(local_backup_base_dir, project_name, retention_settings)
    except Exception as e:
        logging.error(f"Error applying retention policy: {e}")

    # Send notification if not disabled by flag
    if not args.no_notify:
        current_date_str = datetime.datetime.now().isoformat()
        send_notification(webhook_url, project_name, current_date_str, backup_success)
    else:
        logging.info("Notification disabled by --no-notify flag.")

    logging.info("Backup process completed.")

if __name__ == "__main__":
    main()


