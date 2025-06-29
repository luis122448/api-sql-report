from fastapi import APIRouter
from typing import List, Dict, Any
from scheduling.scheduler import scheduler

router = APIRouter()

@router.get("/scheduler/jobs", response_model=List[Dict[str, Any]])
async def get_scheduled_jobs():
    # Returns a list of all currently scheduled jobs.
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "args": job.args,
            "kwargs": job.kwargs,
            "pending": job.pending
        })
    return jobs_info