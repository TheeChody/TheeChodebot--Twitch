import os
import sys
import time
# import asyncio
# import keyboard
import datetime
import threading
from pathlib import Path
# from chodebot import data_directory


if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

timer = None
total_seconds = None
clock_reset_time = "0:00:00"
data_directory = f"{application_path}\\data\\"
clock = f"{data_directory}clock.txt"
Path(data_directory).mkdir(parents=True, exist_ok=True)


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


# def countdown(total_seconds, paused=False):
#     time.sleep(1)
#     while total_seconds >= 1:
#         try:
#             write_clock(1)
#             timer = read_clock()
#             total_seconds = get_sec(timer)
#             print(timer), time.sleep(1)
#         except KeyboardInterrupt:
#             paused = True
#             break
#     if not paused:
#         print("Bzzzt! The countdown is at zero seconds!")
#         with open(clock, "w") as file:
#             file.write(clock_reset_time)


class CountDown:  # ToDo: Try This With A CustomTkinter App?????????????????????????????????????????????????
    def __init__(self):
        # self.was_paused = False
        self.is_running = False
        self.timer = f"0:00:00"
        self.total_seconds = 0

        # print(self.timer, self.total_seconds)
        # self.initiate()
        # print(self.timer, self.total_seconds)
        # time.sleep(1)
        # while self.total_seconds >= 1 and self.is_running:
        #     write_clock(1)
        #     self.timer = read_clock()
        #     self.total_seconds = get_sec(self.timer)
        #     print(timer), time.sleep(1)
        #     if not self.is_running:
        #         break
        # if total_seconds <= 0:
        #     print("Bzzzt! The countdown is at zero seconds!")
        #     with open(clock, "w") as file:
        #         file.write(clock_reset_time)

    def countdown(self):
        print(self.timer, self.total_seconds)
        self.initiate()
        print(self.timer, self.total_seconds)
        time.sleep(1)
        while self.total_seconds >= 1:
            write_clock(1)
            self.timer = read_clock()
            self.total_seconds = get_sec(self.timer)
            print(self.timer), time.sleep(1)
            if not self.is_running:
                break
        if total_seconds <= 0:
            print("Bzzzt! The countdown is at zero seconds!")
            with open(clock, "w") as file:
                file.write(clock_reset_time)

    def initiate(self):
        with open(clock, "r") as file:
            self.timer = file.read()
        self.total_seconds = get_sec(self.timer)

    def start(self):
        # self.initiate()
        if not self.is_running:
            self.is_running = True
            # threading.Thread(target=self.countdown()).run()
            self.countdown()

    def stop(self):
        if self.is_running:
            # self.was_paused = True
            self.is_running = False


try:
    if not os.path.exists(clock):
        with open(clock, "w") as file:
            file.write(clock_reset_time)
            print("File 'clock.txt' created first time run")
    elif os.path.exists(clock):
        print("File already exists")
except Exception as e:
    print(f"Something wrong, cannot locate clock.txt file. path looking in is: {clock} -- {e}")
    exit()

with open(clock, "r") as file:  # DEBUGGING
    print(file.read())

# while True:
#     user_seconds = input(f"+seconds to start thee timer\n")
#     if user_seconds.startswith("+"):
#         seconds = user_seconds.lstrip("+")
#         if seconds.isdigit():
#             seconds = int(seconds)
#             write_clock(seconds, True)
#             input("Hit ENTER To Start Thee Timer!\n")
#             break
#         else:
#             print(f"{seconds} isn't valid, try just numbers.")
#     else:
#         print(f"input not valid, yours was: -- {user_seconds} --")
#         continue


# paused = False
timer = read_clock()
total_seconds = get_sec(timer)
print(timer, total_seconds, f"WHAT THEE FUCK")  # DEBUGGING
# countdown(total_seconds)

# def main_loop():
#     timer = CountDown()
#     keyboard.add_hotkey("s", timer.start)
#     keyboard.add_hotkey("p", timer.stop)

    # keyboard.wait("s")
    # keyboard.wait("p")


# main_loop()

# CountDown().start()

# countdown(timer)
# countdown(total_seconds)
# count_down = threading.Thread(target=countdown(total_seconds)).start()
# user_input = input("Hit Enter To STOP Thee Timer")
# if user_input == "":
#     countdown.__setattr__("paused", True)  #paused = True
