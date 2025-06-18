from app import create_app, apscheduler
from app.scheduler.tasks.update_clips import update_clips

app = create_app()

def update_clips_job():
    with app.app_context():
        update_clips()

apscheduler.add_job(update_clips_job, 'interval', seconds=30)

apscheduler.start()
print("Scheduler started. Press Ctrl+C to exit.")

try:
    import time
    while True:
        time.sleep(60)
except (KeyboardInterrupt, SystemExit):
    apscheduler.shutdown()