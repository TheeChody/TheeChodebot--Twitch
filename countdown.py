import os
import time
from functions import clock, clock_reset_time, read_clock, write_clock, get_sec


def countdown(total_seconds):
    time.sleep(1)
    while total_seconds >= 1:
        try:
            write_clock(1)
            total_seconds = get_sec(read_clock())
            print(read_clock()), time.sleep(1)
        except KeyboardInterrupt:
            break
    total_seconds = get_sec(read_clock())
    print(total_seconds, f"TESTING STUFFS")
    if total_seconds <= 0:
        print("Bzzzt! The countdown is at zero seconds!")
        with open(clock, "w") as file:
            file.write(clock_reset_time)


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

while True:
    try:
        user_input = input(f"Enter 1 to enter countdown\nEnter 0 to quit countdown\n")
        if user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                print(f"Exiting countdown")
                break
            elif user_input == 1:
                while True:
                    while True:
                        try:
                            user_seconds = input(f"+/-seconds to start thee timer\n")
                            if user_seconds.startswith("+"):
                                add = True
                                break
                            elif user_seconds.startswith("-"):
                                add = False
                                break
                            else:
                                print(f"input not valid, yours was: -- {user_seconds} --")
                        except KeyboardInterrupt:
                            print(f"Exiting countdown")
                            add = None
                            user_seconds = None
                            break
                    if None in (add, user_seconds):
                        break
                    try:
                        user_seconds = user_seconds.lstrip("-").lstrip("+")
                        if user_seconds.isdigit():
                            user_seconds = int(user_seconds)
                            write_clock(user_seconds, add)
                            input("Hit ENTER To Start Thee Timer!\n")
                            timer = read_clock()
                            total_seconds = get_sec(timer)
                            print(timer, total_seconds)  # DEBUGGING -- ++ 2 lines above -- otherwise countdown(get_sec(read_clock()))
                            countdown(total_seconds)
                            # countdown(get_sec(read_clock()))  # For Run
                        else:
                            print(f"{user_seconds} isn't valid, try just numbers.")
                    except KeyboardInterrupt:
                        print(f"Exiting countdown")
                        break
            else:
                print(f"Invalid Input -- You put {user_input}")
        else:
            print(f"Invalid Input -- You put {user_input} -- which is a {type(user_input)}")
    except KeyboardInterrupt:
        print("Exiting countdown")
        break
