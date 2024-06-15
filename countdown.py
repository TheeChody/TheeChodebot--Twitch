import os
import time
import datetime
from functions import clock, clock_max, clock_pause, clock_reset_pause, clock_total, clock_reset_time, read_clock, \
    write_clock, reset_max_time, reset_total_time, reset_current_time, loop_get_user_input_clock, reset_sofar_time, clock_sofar, \
    refresh_pause, reset_pause, WebsocketsManager
from timeit import default_timer as how_long


def countdown(total_seconds: float):
    pause_time = int(refresh_pause())
    time.sleep(pause_time)
    while total_seconds >= 1:
        try:
            start = how_long()
            write_clock(1, obs=obs, countdown=True)
            # timer = read_clock()
            # total_seconds = get_sec(timer)
            total_seconds = float(read_clock())
            pause_time = int(refresh_pause())
            end = how_long()
            adjust = end - start
            print(str(datetime.timedelta(seconds=round(total_seconds))).title(), total_seconds, pause_time - adjust), time.sleep(pause_time - adjust)
        except KeyboardInterrupt:
            break
    print(str(datetime.timedelta(seconds=round(float(read_clock())))).title(), f"TESTING STUFFS")
    if total_seconds <= 0:
        print("Thee countdown has reached zero seconds! Writing Reset Time!")
        with open(clock, "w") as file:
            file.write(clock_reset_time)


if __name__ == "__main__":
    try:
        obs = WebsocketsManager()
        obs.connect()
        print(f"OBS Connection Established")
        if not os.path.exists(clock):
            with open(clock, "w") as file:
                file.write(clock_reset_time)
                print("File 'clock.txt' created first time run")
        elif os.path.exists(clock):
            print("File 'clock.txt' already exists")
        if not os.path.exists(clock_max):
            with open(clock_max, "w") as file:
                file.write(clock_reset_time)
                print("File 'clock_max.txt' created first time run")
        elif os.path.exists(clock_max):
            print("File 'clock_max.txt' already exists")
        if not os.path.exists(clock_total):
            with open(clock_total, "w") as file:
                file.write(clock_reset_time)
                print("File 'clock_total.txt' created first time run")
        elif os.path.exists(clock_total):
            print("File 'clock_total.txt' already exists")
        if not os.path.exists(clock_sofar):
            with open(clock_sofar, "w") as file:
                file.write(clock_reset_time)
                print("File 'clock_sofar.txt' created first time run")
        elif os.path.exists(clock_sofar):
            print("File 'clock_sofar.txt' already exists")
        if not os.path.exists(clock_pause):
            with open(clock_pause, "w") as file:
                file.write(clock_reset_pause)
                print("File 'clock_pause.txt' created first time run")
        elif os.path.exists(clock_pause):
            print("File 'clock_pause'.txt already exists")
    except Exception as e:
        print(f"Something wrong, cannot locate clock.txt file. path looking in is: {clock} -- {e}")
        exit()

    while True:
        try:
            user_input = input(f"Enter 1 to enter countdown\nEnter 2 to configure countdown\nEnter 0 to quit countdown\n")
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    print(f"Exiting countdown")
                    break
                elif user_input == 1:
                    if not os.path.exists(clock_max):
                        while True:
                            max_seconds = input(f"Max Time File Not Found! Enter Max Time in SECONDS\n")
                            if not max_seconds.isdigit():
                                print(f"You didn't enter a number")
                            else:
                                max_seconds = float(max_seconds)
                                # max_seconds_formatted = str(datetime.timedelta(seconds=max_seconds))
                                with open(clock_max, "w") as file:
                                    # file.write(max_seconds_formatted.title())
                                    file.write(str(max_seconds))
                                print(f"Max time set successfully as {max_seconds}")
                                break
                    while True:
                        user_seconds, add = loop_get_user_input_clock()
                        try:
                            if user_seconds.isdigit():
                                user_seconds = float(user_seconds)
                                write_clock(user_seconds, add)
                                input("Hit ENTER To Start Thee Timer!\n")
                                # timer = read_clock()
                                # total_seconds = get_sec(timer)
                                total_seconds = float(read_clock())
                                print(str(datetime.timedelta(seconds=round(total_seconds))).title(), total_seconds)  # DEBUGGING -- ++ 2 lines above -- otherwise countdown(get_sec(read_clock()))
                                countdown(total_seconds)
                                # countdown(get_sec(read_clock()))  # For Run
                            else:
                                print(f"{user_seconds} isn't valid, try just numbers.")
                        except KeyboardInterrupt:
                            print(f"Exiting countdown")
                            break
                    time.sleep(1)
                elif user_input == 2:
                    while True:
                        user_input = input(f"Enter 1 to change current time\nEnter 2 to change max time\nEnter 3 to change total time\nEnter 4 to change sofar time\nEnter 5 to change speed\nEnter 0 to go back\n")
                        if user_input.isdigit():
                            user_input = int(user_input)
                            if user_input == 0:
                                print(f"Going back")
                                break
                            elif user_input == 1:
                                reset_current_time()
                            elif user_input == 2:
                                reset_max_time()
                            elif user_input == 3:
                                reset_total_time()
                            elif user_input == 4:
                                reset_sofar_time()
                            elif user_input == 5:
                                reset_pause()
                            else:
                                print(f"Invalid Input -- You put {user_input}")
                        else:
                            print(f"Invalid Input -- You put {user_input}")
                else:
                    print(f"Invalid Input -- You put {user_input}")
            else:
                print(f"Invalid Input -- You put {user_input} -- which is a {type(user_input)}")
        except KeyboardInterrupt:
            print("Exiting countdown")
            break
    obs.disconnect()
    print(f"Disconnected from OBS")
