# Automated Backup and Rotation Script with Google Drive Integration
## Overview
This Python script provides a robust solution for automating project backups, implementing a rotational backup strategy, and integrating with Google Drive for off-site storage. It's designed for projects hosted on GitHub or any local directory that requires regular, structured backups.

## Features
**Automated Archiving:** Creates .zip archives of your specified project directory.

**Timestamped Backups:** Names archives with a clear `ProjectName_YYYYMMDD_HHMMSS.zip` format.

**Structured Local Storage:** Organizes backups in `~/backups/ProjectName/YYYY/MM/DD/` directories.

**Google Drive Integration:** Uploads backups to a designated Google Drive folder using rclone.

**Rotational Backup Policy:** Automatically manages and deletes older backups based on configurable daily, weekly, and monthly retention settings.

**Process Logging:** Maintains a backup.log file with details on backup time, file name, upload status, and deletion summary.

**Notification System:** Sends a POST cURL request to a specified webhook URL upon successful (or failed) backup, with an option to disable it.

**Configurable:** All key settings are managed via a config.json file.

## Prerequisites
**Python 3:** Ensure Python 3 is installed on your system.
```
python3 --version
```
**requests library:** This Python library is used for sending the webhook notification. Install it using pip (preferably within a virtual environment):
```
pip install requests
```
**`rclone` CLI Tool:** This script relies on rclone for Google Drive integration.

## Installation and Configuration of rclone
`rclone` is a powerful command-line program to manage files on cloud storage.

**Install rclone:**
The recommended way to install rclone on Linux/macOS is using the install script:
```
curl https://rclone.org/install.sh | sudo bash
```
Alternatively, for Debian/Ubuntu based systems (like WSL2 Ubuntu):
```
sudo apt update
sudo apt install rclone
```
For other operating systems or manual installation, refer to the official rclone documentation: https://rclone.org/install/

**Configure Google Drive with rclone:**
You need to configure rclone to connect to your Google Drive account.
```
rclone config
```
**Follow the interactive prompts:**

- Choose n for new remote.

- Give it a name (e.g., gdrive or automatedBackup as used in this project). This name should match the `rclone_remote_name` in your `config.json`.

- Select drive (usually option 18 or similar) for Google Drive.

- Leave `client_id` and `client_secret` blank unless you have your own.

- Choose 1 for Full access all files, including application data.

- Leave `root_folder_id` and `service_account_fil`e blank.

- Choose `n` for Edit advanced config?.

- Choose `y` for Use auto config?. This will open a browser window for authentication. Authenticate with your Google account.

- Choose `n` for Configure this as a team drive?.

- Confirm your configuration by typing `y`.

**Once configured, you can test it by listing your Google Drive folders:**
```
rclone lsd <your_rclone_remote_name>:
# Example: rclone lsd automatedBackup:
```
## Script Setup
Download the script:
1. Save the provided Python script as backup.py.

2. Create `config.json`:
Create a file named config.json in the same directory as backup.py (or specify its path with --config).
```
{
  "project_name": "MyGitHubProject",
  "local_backup_base_dir": "~/backups",
  "rclone_remote_name": "automatedBackup",
  "google_drive_folder_name": "ProjectBackups",
  "retention": {
    "daily": 7,
    "weekly": 4,
    "monthly": 3
  },
  "webhook_url": "https://webhook.site/your-unique-url-here"
}
```
- `project_name`: A unique name for your project (e.g., MyWebsite, BackendAPI). This will be used in backup filenames and local directory structure.

- `local_backup_base_dir`: The base directory where all backups will be stored locally. Defaults to ~/backups.

- `rclone_remote_name`: The name you gave your Google Drive remote when configuring rclone (e.g., automatedBackup).

- `google_drive_folder_name`: The name of the folder in your Google Drive where backups will be uploaded. This folder will be created by rclone if it doesn't exist.

- **retention:**

  - `daily`: Number of daily backups to keep. The script keeps the daily most recent backups overall.

  - `weekly`: Number of weekly backups (only Sundays) to keep.

  - `monthly`: Number of monthly backups (latest for each of the last X distinct months) to keep.

- `webhook_url`: Your unique URL for receiving POST notifications. You can use services like webhook.site for testing. Remember to replace your-unique-url-here with your actual webhook URL.

## How to Run the Script
**Manual Execution**
- Navigate to the directory containing `backup.py` and `config.json`. Ensure your Python virtual environment is activated (source venv/bin/activate).
```
python3 backup.py --config /path/to/your/config.json --project-path /path/to/your/github/project
```
- Replace `/path/to/your/config.json` with the absolute path to your `config.json` file.

- Replace `/path/to/your/github/project` with the actual absolute path to the directory you want to back up.

**Disabling Notifications**
To run the script without sending the cURL notification:
```
python3 backup.py --config /path/to/your/config.json --project-path /path/to/your/github/project --no-notify
```
**Example Usage and Expected Output**
When you run the script, you will see output in your terminal (and logged to `~/backups/ProjectName/backup.log`).
```
Sample Terminal Output:

2023-10-27 10:30:00,123 - INFO - Starting backup process for project: MyGitHubProject
2023-10-27 10:30:00,123 - INFO - Project path: /home/user/my_github_project
2023-10-27 10:30:00,123 - INFO - Creating backup of '/home/user/my_github_project' to '/home/user/backups/MyGitHubProject/2023/10/27/MyGitHubProject_20231027_103000.zip'...
2023-10-27 10:30:05,456 - INFO - Backup created successfully: /home/user/backups/MyGitHubProject/2023/10/27/MyGitHubProject_20231027_103000.zip (Contains X files).
2023-10-27 10:30:05,456 - INFO - Uploading '/home/user/backups/MyGitHubProject/2023/10/27/MyGitHubProject_20231027_103000.zip' to Google Drive folder 'automatedBackup:ProjectBackups'...
2023-10-27 10:30:10,789 - INFO - Google Drive upload successful. Output:
Transferred:        1.234 MiB / 1.234 MiB, 100%, 245.67 KiB/s, ETA 0s
Transferred:            1 / 1, 100%
Elapsed time:         5.3s
2023-10-27 10:30:10,789 - INFO - Backup successfully created and uploaded.
2023-10-27 10:30:10,789 - INFO - Applying retention policy...
2023-10-27 10:30:11,100 - INFO - Deleted old backup: /home/user/backups/MyGitHubProject/2023/10/20/MyGitHubProject_20231020_030000.zip
2023-10-27 10:30:11,100 - INFO - Retention policy applied. Total deleted: 1 files.
2023-10-27 10:30:11,100 - INFO - Sending notification to https://webhook.site/your-unique-url-here with status: BackupSuccessful...
2023-10-27 10:30:11,500 - INFO - Notification sent successfully. Response: 200
2023-10-27 10:30:11,500 - INFO - Backup process completed.
```
Sample cURL Webhook Payload (JSON sent to your `webhook_url`):
```
{
  "project": "MyGitHubProject",
  "date": "2023-10-27T10:30:11.123456",
  "status": "BackupSuccessful"
}
```
(The date format will be an ISO timestamp of when the notification is sent, and status will be BackupSuccessful or BackupFailed.)

**Scheduling with Crontab**
To automate the script to run regularly, you can use cron (on Linux/macOS).

1. Open your crontab for editing:
```
crontab -e
```
2. Add the following line (adjust paths accordingly). This example runs daily at 3:00 AM.
```
# Daily backup at 3:00 AM
0 3 * * * /path/to/your/venv/bin/python3 /path/to/your/backup.py --config /path/to/your/config.json --project-path /path/to/your/github/project >> /path/to/your/backup.log 2>&1
```
## Important:

- Replace `/path/to/your/venv/bin/python3` with the actual absolute path to the Python 3 interpreter inside your virtual environment (e.g., /home/apame09/Fortunecloud-Tasks/Task-03/venv/bin/python3).

- Replace `/path/to/your/backup.py` with the absolute path to where you saved the `backup.py` script.

- Replace `/path/to/your/config.json` with the absolute path to your `config.json` file.

- Replace `/path/to/your/github/project` with the absolute path to the project directory you want to back up.

- The `>> /path/to/your/backup.log 2>&1` part redirects all script output (standard output and standard error) to a log file. This is crucial for debugging cron jobs, as cron jobs run in the background without a direct terminal. Ensure the log file path is writable by the cron user.

## Security Considerations
**1. `rclone` Configuration:** rclone stores your Google Drive credentials securely. Ensure the system where rclone is configured is secure and protected. Avoid running the script with root privileges unless absolutely necessary.

**2. Webhook URL:** Your webhook_url will receive notifications. Be mindful of what information you send and to whom. If the webhook URL is public, sensitive data should not be included in the payload.

**3. File Permissions:** Ensure the user running the script has sufficient permissions:

  - Read access to the project_path.

  - Write access to the `local_backup_base_dir` and its subdirectories where backups and logs will be stored.

**4. Deletion Policy:** The retention policy automatically deletes old backups. Double-check your retention settings in config.json to avoid accidental data loss. Always consider having multiple layers of backup (e.g., local + cloud + potentially another cloud provider) for critical data.

**5. Error Handling:** The script includes basic error handling and logging. Regularly check the backup.log file for any errors or warnings to ensure your backups are running successfully.
