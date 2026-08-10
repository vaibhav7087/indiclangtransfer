# Project Agent Rules

## Phone Notifications
Whenever you need to alert the user, get their attention, or let them know a long task has finished, send a push notification to their phone by sending an HTTP POST request to `https://ntfy.sh/vaibhav_indic_agent_8821`. 
- **Method 1**: If you have terminal access, you can run a python script or a `curl`/`Invoke-RestMethod` command to send this POST request.
- **Method 2**: If you are blocked by terminal permissions (waiting for approval), you cannot run a command. In this case, ask the user to start a file-watchdog notifier, and then trigger it by creating a file.
