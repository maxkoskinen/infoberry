import re
from pathlib import Path
from crontab import CronTab

REGEX = re.compile(r"^Serial\s+:\s+([0-9a-f]+)$", re.MULTILINE)

# with regex
def get_serial() -> str:
    cpuinfo = Path("/proc/cpuinfo").read_text()
    match = REGEX.search(cpuinfo)
    if not match:
        raise RuntimeError("This is not a Raspberry Pi")
    serial = match.group(1)
    return serial


def time_to_cron(time_str: str):
    """Convert HH:mm to cron schedule"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return f'{minute} {hour} * * *'
    except Exception as e:
        print(f"error converting time: {e}")


class ScheduleManager:
    def __init__(self) -> None:
        self.cron = CronTab(user=True)
        # remove all existing cron jobs
        self.cron.remove_all()
        self.cron.write()

    def add_job(self, command: str, schedule: str):
        job = self.cron.new(command=command)
        job.setall(schedule)
        self.cron.write()
    
    def update_schedule_job(self, job_command: str, new_schedule: str) -> bool:
        job = None
        for existing_job in self.cron:
            if existing_job.command == job_command:
                job = existing_job
                break
        if job:
            job.setall(new_schedule)
            self.cron.write()
            return True
        else:
            self.add_job(command=job_command, schedule=new_schedule)
        return False

    def remove_job(self, job_command: str) -> bool:
        job = None
        for existing_job in self.cron:
            if existing_job.command == job_command:
                job = existing_job
                self.cron.remove(job)
                self.cron.write()
                return True
        return False
    
    def remove_all_jobs(self) -> bool:
        exit_code = self.cron.remove_all()
        if exit_code == 1:
            return True
        return False