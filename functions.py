import os
import sys
import datetime
from pathlib import Path

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

countdown_path = f"{Path(__file__).parent.absolute()}\\"
data_directory = f"{application_path}\\data\\"
logs_directory = f"{application_path}\\logs\\"
chat_log = f"{logs_directory}chat_log.log"
clock = f"{data_directory}clock.txt"
clock_reset_time = "0:00:00"
Path(data_directory).mkdir(parents=True, exist_ok=True)
Path(logs_directory).mkdir(parents=True, exist_ok=True)
long_dashes = "-------------------------------------------------"

# print(f"App -- {application_path} --- path__file__ -- {countdown_path}")  # ToDo: Figure out if I want to use Path(__file__) as thee determining app_path...


def get_sec(time_str: str):
    if "Day" in time_str:
        d, hms = time_str.split(",")
        d = d.replace("Day", "")
        if "s" in d:
            d = d.replace("s", "")
        h, m, s = hms.split(":")
        return int(d) * 86400 + int(h) * 3600 + int(m) * 60 + int(s)
    else:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)


def read_clock():
    with open(clock, "r") as file:
        timer = file.read()
        return timer


def write_clock(seconds: int, add: bool = False):
    try:
        with open(clock, "r") as file_read:
            timer = file_read.read()
        total_seconds = get_sec(timer)
        total_seconds = int(total_seconds)
        if add:
            total_seconds += seconds
            timer = datetime.timedelta(seconds=total_seconds)
            timer = str(timer)
            with open(clock, "w") as file:
                file.write(timer.title())
        elif not add:
            total_seconds -= seconds
            timer = datetime.timedelta(seconds=total_seconds)
            timer = str(timer)
            with open(clock, "w") as file:
                file.write(timer.title())
    except Exception as e:
        if ValueError:
            print(f"Attempted to go negative time. -- {e}")
            with open(clock, "r") as read:
                old_time = read.read()
            with open(clock, "w") as file:
                file.write(clock_reset_time)
            print(f"Overwrote to prevent issues. old time was:: {old_time}")
            return
        else:
            print(f"Something else went wrong -- {e}")
            return