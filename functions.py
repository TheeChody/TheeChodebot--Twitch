import os
import sys
import datetime
import time
from pathlib import Path
from mongoengine import Document

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

standard_ehvent_mult = 2
# countdown_path = f"{Path(__file__).parent.absolute()}\\"
data_directory = f"{application_path}\\data\\"
logs_directory = f"{application_path}\\logs\\"
chat_log = f"{logs_directory}chat_log.log"
clock = f"{data_directory}clock.txt"
clock_sofar = f"{data_directory}clock_sofar.txt"
clock_total = f"{data_directory}clock_total_time.txt"
clock_max = f"{data_directory}clock_max_time.txt"
clock_reset_time = "0:00:00"
Path(data_directory).mkdir(parents=True, exist_ok=True)
Path(logs_directory).mkdir(parents=True, exist_ok=True)
long_dashes = "-------------------------------------------------"

# print(f"App -- {application_path} --- path__file__ -- {countdown_path}")  # ToDo: Figure out if I want to use Path(__file__) as thee determining app_path...


def loop_get_user_input_clock():
    try:
        while True:
            number = input(f"Enter +/-number to add/subtract\n")
            if number.startswith("+"):
                prefix = "+"
                add = True
                break
            elif number.startswith("-"):
                prefix = "-"
                add = False
                break
            else:
                print(f"Invalid Input -- You put '{number}'")
        number = number.removeprefix(prefix)
        return number, add
    except Exception as e:
        if KeyboardInterrupt:
            time.sleep(1)
            print("Breaking loop")
            return None, None
        else:
            print(f"Error in get_user_input_clock -- {e}")
            return None, None


def get_sec(timer: str):
    if "Day" in timer:
        d, hms = timer.split(",")
        d = d.replace("Day", "")
        if "s" in d:
            d = d.replace("s", "")
        h, m, s = hms.split(":")
        return int(d) * 86400 + int(h) * 3600 + int(m) * 60 + int(s)
    else:
        h, m, s = timer.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)


def read_clock():
    with open(clock, "r") as file:
        return file.read()


def max_read_clock():
    with open(clock_max, "r") as file:
        return file.read()


def total_read_clock():
    with open(clock_total, "r") as file:
        return file.read()


def sofar_read_clock():
    with open(clock_sofar, "r") as file:
        return file.read()


def reset_current_time():
    while True:
        user_input = input(f"Enter 1 to change current time\nEnter 2 to reset current time\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                break
            elif user_input == 1:
                while True:
                    new_time = input(f"Enter a new current time in SECONDS\n")
                    if not new_time.isdigit():
                        print(f"Must enter just a number")
                    else:
                        new_time = int(new_time)
                        new_time_formatted = str(
                            datetime.timedelta(seconds=new_time))  # .title()  ToDo Try that <<<<<<<<<<<<<<<
                        with open(clock, "w") as file:
                            file.write(new_time_formatted.title())
                        print(f"New current time set @ {new_time_formatted.title()}")
                        break
            elif user_input == 2:
                with open(clock, "w") as file:
                    file.write(clock_reset_time)
                    print(f"Current Clock Reset to {clock_reset_time}")
            else:
                print(f"You must enter a number, you put {user_input} which is a {type(user_input)}")


def reset_max_time():
    while True:
        user_input = input(f"Enter 1 to change max time\nEnter 2 to reset max time\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                break
            elif user_input == 1:
                while True:
                    new_max_seconds = input(f"Enter a new max time in SECONDS\n")
                    if not new_max_seconds.isdigit():
                        print(f"Must enter just a number")
                    else:
                        new_max_seconds = int(new_max_seconds)
                        new_max_formatted = str(datetime.timedelta(seconds=new_max_seconds))
                        with open(clock_max, "w") as file:
                            file.write(new_max_formatted.title())
                        print(f"New max time set @ {new_max_formatted.title()}")
                        break
            elif user_input == 2:
                with open(clock_max, "w") as file:
                    file.write(clock_reset_time)
                print(f"Max Clock reset to {clock_reset_time}")
            else:
                print(f"numbers only!! you put {user_input} which is a {type(user_input)}")


def reset_total_time():
    while True:
        user_input = input(f"Enter 1 to change total time\nEnter 2 to reset total time\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                break
            elif user_input == 1:
                while True:
                    new_total_time = input(f"Enter new total time in SECONDS\n")
                    if not new_total_time.isdigit():
                        print(f"You must enter just a number")
                    else:
                        new_total_time_formatted = str(datetime.timedelta(seconds=int(new_total_time))).title()
                        with open(clock_total, "w") as file:
                            file.write(new_total_time_formatted)
                        print(f"New Total Time Set @ {new_total_time_formatted}")
                        break
            elif user_input == 2:
                with open(clock_total, "w") as file:
                    file.write(clock_reset_time)
                    print(f"Total Clock Reset to {clock_reset_time}")
            else:
                print(f"You must enter just a number -- you put -- {user_input} which is a {type(user_input)}")


def reset_sofar_time():
    while True:
        user_input = input(f"Enter 1 to change so far time\nEnter 2 to reset so far time\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                break
            elif user_input == 1:
                while True:
                    new_total_time = input(f"Enter new so far time in SECONDS\n")
                    if not new_total_time.isdigit():
                        print(f"You must enter just a number")
                    else:
                        new_sofar_time_formatted = str(datetime.timedelta(seconds=int(new_total_time))).title()
                        with open(clock_sofar, "w") as file:
                            file.write(new_sofar_time_formatted)
                        print(f"New So Far Time Set @ {new_sofar_time_formatted}")
                        break
            elif user_input == 2:
                with open(clock_sofar, "w") as file:
                    file.write(clock_reset_time)
                    print(f"So Far Clock Reset to {clock_reset_time}")
            else:
                print(f"You must enter just a number -- you put -- {user_input} which is a {type(user_input)}")


def reset_level_const(level_const):
    while True:
        user_input = input(f"Enter 1 to Change Level Constant\nEnter 2 to Reset Level Constant\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"Must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                return level_const
            elif user_input == 1:
                while True:
                    new_level_const = input(f"Input new Level Constant\n")
                    if not new_level_const.isdigit():
                        print(f"Must enter just a number")
                    else:
                        level_const = int(new_level_const)
                        print(f"New Level Const set @ {new_level_const}")
                        return level_const
            elif user_input == 2:
                level_const = 100
                print(f"Level Const reset @ {level_const}")
                return level_const
            else:
                print(f"You must enter just a number, you put {user_input} which is a {type(user_input)}")


def write_sofar(second):
    with open(clock_sofar, "r") as read:
        current_sofar = read.read()
        if current_sofar == "":
            current_sofar = clock_reset_time
    with open(clock_sofar, "w") as file:
        file.write(str(datetime.timedelta(seconds=get_sec(current_sofar) + second)).title())


def write_clock(seconds: int, add: bool = False, channel_document: Document = None, countdown: bool = False):
    try:
        formatted_missed_seconds = None
        current_seconds = int(get_sec(read_clock()))
        if add:
            max_seconds = int(get_sec(max_read_clock()))
            total_seconds = int(get_sec(total_read_clock()))
            if channel_document is not None:
                if channel_document['hype_train_current']:
                    if channel_document['hype_train_current_level'] > 1:
                        seconds *= (channel_document['hype_train_current_level'] / 10) + standard_ehvent_mult
                    else:
                        seconds *= standard_ehvent_mult
            total_seconds += seconds
            if total_seconds > max_seconds:
                seconds_to_subtract = abs(total_seconds - max_seconds)
                seconds -= seconds_to_subtract
                total_seconds -= seconds_to_subtract
                formatted_missed_seconds = str(datetime.timedelta(seconds=seconds_to_subtract)).title()
                print(f"Went above MAX TIME -- {formatted_missed_seconds} ({seconds_to_subtract}) will NOT be added")
            current_seconds += seconds
            with open(clock, "w") as file:
                file.write(str(datetime.timedelta(seconds=current_seconds)).title())
            with open(clock_total, "w") as file:
                file.write(str(datetime.timedelta(seconds=total_seconds)).title())
        elif not add:
            if seconds >= current_seconds != 1:  # This SHOULD Work to Counter Timer Going Below 0 or minus seconds haha
                seconds = current_seconds - 1
            current_seconds -= seconds
            with open(clock, "w") as file:
                file.write(str(datetime.timedelta(seconds=current_seconds)).title())
            if countdown:
                write_sofar(seconds)
        return seconds, formatted_missed_seconds
    except Exception as e:
        if ValueError:
            print(f"Attempted to go negative time, or something else went wrong. -- {e}")
            with open(clock, "r") as read:
                old_time = read.read()
            with open(clock, "w") as file:
                file.write(clock_reset_time)
            print(f"Overwrote to prevent issues. old time was:: {old_time}({get_sec(old_time)})")
            return None, None
        else:
            print(f"Something else went wrong -- {e}")
            return None, None
