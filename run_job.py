from prefect.deployments import Deployment
from prefect.orion.schemas.schedules import IntervalSchedule
from datetime import timedelta

from prefect2_daily_job import main_job

Deployment(
    name="beach-daily-job",
    flow_location="prefect2_daily_job.py",
    flow=main_job,
    schedule=IntervalSchedule(interval=timedelta(hours=1)),
)