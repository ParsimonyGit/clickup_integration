## Clickup Integration

ClickUp Integration with ERPNext to sync Tasks, Projects, Comments, and Attachments.

## Features 
- Syncs Tasks, Projects, comments, Attachments from ClickUp
- Button to sync all Tasks from ClickUp
- Fetches files and attaches them to relevant Tasks

## Installation

1. Clone the `clickup_integration` repository locally.
	```sh
	git clone https://github.com/ParsimonyGit/clickup_integration
	```

2. Install Arena Integration on the site
	```sh
	bench --site {site_name} install-app clickup_integration
	```

 ## Setup

 - Get Client ID and Client Secret from ClickUp Settings.
 - Open `ClickUp Settings` and set Client ID, Client Secret, and Redirect URL.

 ## To Sync Tasks

 - Click on `Sync Tasks` under `Clickup Settings`.
     - `This will create a background job to fetch tasks, projects, comments, and attachments.`
