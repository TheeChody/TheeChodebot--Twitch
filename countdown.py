import logging
import os
import time
import datetime
from functions import clock, clock_max, clock_pause, clock_reset_pause, clock_total, clock_reset_time, read_clock, \
    write_clock, reset_max_time, reset_total_time, reset_current_time, loop_get_user_input_clock, reset_sofar_time, clock_sofar, \
    read_pause, reset_pause, WebsocketsManager, max_read_clock, fortime, setup_logger, logs_directory

logger_list = []


def countdown(total_seconds: float):
    pause = float(read_pause())
    start_time = time.monotonic()
    while total_seconds >= 1.0:
        try:
            if float(read_pause()) != pause:
                start_time = time.monotonic()  # Thinking this will eventually lose time butt I don't know for sure, it seems really on point still... Tis seem still accurate to thee 1,000,000,000,000,000 decimal point...
                pause = float(read_pause())
            total_seconds = write_clock(1, obs=obs, countdown=True)
            logger.info(f"{total_seconds} -- {str(datetime.timedelta(seconds=int(total_seconds))).title()} -- {datetime.datetime.now().strftime('%H:%M:%S')} -- {pause} -- {pause - ((time.monotonic() - start_time) % pause)}")
            time.sleep(pause - ((time.monotonic() - start_time) % pause))
        except KeyboardInterrupt:
            break
    logger.info(f"{str(datetime.timedelta(seconds=int(float(read_clock())))).title()} {total_seconds} TESTING STUFFS")
    if total_seconds <= 0:
        logger.info("Thee countdown has reached zero seconds! Writing Reset Time!")
        with open(clock, "w") as file:
            file.write(clock_reset_time)
        obs.set_text("TwitchTimer", f"Thee Timer Has Hit Zero. Much Love To All <3")
        shutdown()


def shutdown():
    obs.disconnect()
    logger.info(f"Disconnected from OBS")
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{logs_directory}{entry}", f"{logs_directory}\\archive_log\\{entry}")
        except Exception as e:
            print(e)
            pass
    print(f"Shutdown Sequence Completed")
    quit(420)


if __name__ == "__main__":
    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger('countdown_logger', f'{init_time}-countdown_log.log', logger_list)
    try:
        if not os.path.exists(clock):
            with open(clock, "w") as file:
                file.write(clock_reset_time)
            logger.info("File 'clock.txt' created first time run")
        if not os.path.exists(clock_total):
            with open(clock_total, "w") as file:
                file.write(clock_reset_time)
            logger.info("File 'clock_total.txt' created first time run")
        if not os.path.exists(clock_sofar):
            with open(clock_sofar, "w") as file:
                file.write(clock_reset_time)
                logger.info("File 'clock_sofar.txt' created first time run")
        if not os.path.exists(clock_pause):
            with open(clock_pause, "w") as file:
                file.write(clock_reset_pause)
                logger.info("File 'clock_pause.txt' created first time run")
        if not os.path.exists(clock_max):
            while True:
                max_seconds = input(f"Max Time File Not Found! Enter Max Time in SECONDS\n")
                if not max_seconds.isdigit():
                    print(f"You didn't enter a number")
                else:
                    max_seconds = float(max_seconds)
                    with open(clock_max, "w") as file:
                        file.write(str(max_seconds))
                    print(f"Max time set successfully as {str(datetime.timedelta(seconds=int(max_seconds))).title()} - {max_seconds}")
                    break
        else:
            if float(max_read_clock()) == 0.0:
                while True:
                    max_seconds = input(f"Enter new max time for marathon\n")
                    if not max_seconds.isdigit():
                        print("You must enter a number")
                    else:
                        max_seconds = float(max_seconds)
                        with open(clock_max, "w") as file:
                            file.write(str(max_seconds))
                        print(f"Max time set successfully as {str(datetime.timedelta(seconds=int(max_seconds))).title()} - {max_seconds}")
    except Exception as e:
        logger.error(f"Error in data check -- {e}")
        quit()
    try:
        obs = WebsocketsManager()
        obs.connect()
        logger.info(f"OBS Connection Established")
    except Exception as e:
        logger.error(f"Error establishing OBS connection -- {e}")
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
                    while True:
                        user_seconds, add = loop_get_user_input_clock()
                        try:
                            if user_seconds.isdigit():
                                write_clock(float(user_seconds), add, obs=obs, manual=True)
                                input("Hit ENTER To Start Thee Timer!\n")
                                total_seconds = float(read_clock())
                                logger.info(f"{str(datetime.timedelta(seconds=int(total_seconds))).title()} {total_seconds}")  # DEBUGGING -- ++ 2 lines above -- otherwise countdown(float(read_clock()))
                                countdown(total_seconds)
                                # countdown(float(read_clock()))  # For Run
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
    shutdown()
