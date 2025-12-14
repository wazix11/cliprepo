from app import create_app, apscheduler
from app.scheduler.tasks.update_clips import update_clips
from datetime import datetime, timezone, timedelta
import os, subprocess
from dotenv import load_dotenv

load_dotenv(override=True)
CLIPS_START_DATE = os.environ.get("CLIPS_START_DATE")

app = create_app()

def update_clips_job():
    with app.app_context():
        latest_clip_file = './app/scheduler/latest_clip_created_at.txt'
        if os.path.exists(latest_clip_file):
            with open(latest_clip_file, 'r') as f:
                latest_clip_time = f.read().strip()
            if latest_clip_time:
                # reset to start once latest clip created_at is current within 6 days
                six_days_ago = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(timespec='seconds').replace('+00:00', 'Z')
                if latest_clip_time > six_days_ago:
                    with open(latest_clip_file, 'w') as f:
                        f.write(CLIPS_START_DATE)
        update_clips()

def update_recent_clips_job():
    with app.app_context():
        six_days_ago = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(timespec='seconds').replace('+00:00', 'Z')
        update_clips(started_at=six_days_ago, save_to_file=False)

def update_goaccess_report():
    try:
        subprocess.run([
            '/usr/bin/goaccess',
            '-f', '/var/log/cliprepo_access.log',
            '-o', '/home/ubuntu/cliprepo/app/static/report.html',
            '--log-format=COMBINED'
        ])
    except Exception as e:
        print(f"Error updating GoAccess report: {e}", 'error')

apscheduler.add_job(update_clips_job, 'interval', minutes=5, misfire_grace_time=30)
apscheduler.add_job(update_recent_clips_job, 'interval', minutes=1, misfire_grace_time=15)
apscheduler.add_job(update_goaccess_report, 'interval', minutes=5, misfire_grace_time=30)

apscheduler.start()
print("Scheduler started. Press Ctrl+C to exit.")

try:
    import time
    while True:
        time.sleep(60)
except (KeyboardInterrupt, SystemExit):
    apscheduler.shutdown()