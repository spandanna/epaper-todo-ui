# epaper-todo-ui
Simple UI for displaying data from my todo api onto an epaper display.
It's ran on a raspberry pi using a cron scheduler.

## To run with crontab

Make a virtual environment (mine uses python 3.9.2):  
`python -m virtualenv -p 3.9.2 .venv`

Activate environment:  
`source .venv/bin.activate`

Install requirements:  
`pip install -r requirements.txt`

To edit your cron schedules:  
`crontab -e`

Then add the following line to refresh the display every 30 minutes between the hours of 6am and 11pm:  
`*/30 6-23 * * * cd ~/dev/epaper-todo-ui && ~/dev/epaper-todo-ui/.venv/bin/python app.py`
Update the filepath with your own value.