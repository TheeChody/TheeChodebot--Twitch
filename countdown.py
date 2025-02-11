import os
import time
import logging
import datetime
from functions import clock, clock_max, clock_pause, clock_total, clock_reset_time, read_clock, \
    write_clock, reset_max_time, reset_total_time, reset_current_time, loop_get_user_input_clock, reset_sofar_time, \
    clock_sofar, read_clock_pause, reset_clock_slow_rate, reset_clock_pause, WebsocketsManager, read_clock_max, \
    fortime, setup_logger, logs_directory, read_clock_sofar, read_clock_slow_rate_time, cls, write_clock_slow_rate_time, \
    reset_clock_accel_rate, read_clock_up_time, clock_direction_time, read_clock_phase, read_clock_accel_time, \
    read_clock_slow_time, write_clock_phase, strict_pause, countdown_rate_strict, clock_accel_time, clock_slow_time, \
    set_timer_rate, set_timer_count_up, set_timer_pause, obs_timer_main, obs_timer_sofar, obs_timer_scene, obs_timer_rate, \
    obs_timer_countup, read_clock_direction, clock_direction

logger_list = []


def countdown(total_seconds: float):
    def check_pause(pause: float, rate: float = 1.0, direction: str = "down"):
        pause_remainder = 0.0
        second_take = 1.0
        if pause != 0.0:
            if direction == "down":
                pause -= rate
                if pause < 0.0:
                    pause_remainder = abs(pause)
                    pause = 0.0
                    set_timer_pause(obs, False)
                with open(clock_pause, "w") as file:
                    file.write(str(pause))
                second_take = 0.0 + pause_remainder
            else:
                pause += rate
                with open(clock_pause, "w") as file:
                    file.write(str(pause))
                second_take = 0.0
        return second_take, pause
    start_time = time.monotonic()
    while total_seconds >= 1.0:
        try:
            add = False
            countdown_direction = read_clock_direction()
            new_countdown_direction = read_clock_direction()
            pause = float(read_clock_pause())
            countdown_phase = read_clock_phase()
            old_countdown_phase = read_clock_phase()
            countdown_up_time = float(read_clock_up_time())
            countdown_slow_rate_time = float(read_clock_slow_rate_time())
            if countdown_direction == "up":  #countdown_up_time > 0:
                add = True
                with open(clock_direction, "w") as file:
                    file.write(countdown_direction)
                countdown_up_time -= strict_pause
                with open(clock_direction_time, "w") as file:
                    file.write(str(countdown_up_time))
                set_timer_count_up(obs, countdown_up_time)
                if countdown_up_time == 0:
                    new_countdown_direction = "down"
            if countdown_phase == "slow":
                phase = "S"
                countdown_slow_time = float(read_clock_slow_time()) - strict_pause
                if countdown_slow_time <= 0:
                    countdown_slow_time = 0
                    if float(read_clock_accel_time()) > 0:
                        countdown_phase = "accel"
                    else:
                        countdown_phase = "norm"
                    write_clock_phase(countdown_phase)
                with open(clock_slow_time, "w") as file:
                    file.write(str(countdown_slow_time))
                set_timer_rate(obs, countdown_slow_time)
                if countdown_slow_rate_time <= 1.0:
                    countdown_slow_rate_time = countdown_rate_strict
                    write_clock_slow_rate_time(countdown_rate_strict)
                    second_take, pause = check_pause(pause, direction=countdown_direction)
                else:
                    countdown_slow_rate_time -= strict_pause
                    write_clock_slow_rate_time(countdown_slow_rate_time)
                    second_take = 0.0
            elif countdown_phase == "accel":
                phase = "A"
                countdown_accel_time = float(read_clock_accel_time()) - strict_pause
                if countdown_accel_time <= 0:
                    countdown_accel_time = 0
                    if float(read_clock_slow_time()) > 0:
                        countdown_phase = "slow"
                    else:
                        countdown_phase = "norm"
                    write_clock_phase(countdown_phase)
                with open(clock_accel_time, "w") as file:
                    file.write(str(countdown_accel_time))
                set_timer_rate(obs, countdown_accel_time)
                second_take, pause = check_pause(pause, countdown_rate_strict, countdown_direction)
                if second_take == 1.0:
                    second_take = countdown_rate_strict
            else:
                phase = "N"
                second_take, pause = check_pause(pause, direction=countdown_direction)
            if countdown_phase == "norm" and old_countdown_phase != "norm":
                obs.set_source_visibility(obs_timer_scene, obs_timer_rate, False)
            if countdown_direction == "up" and new_countdown_direction == "down":
                with open(clock_direction, "w") as file:
                    file.write(new_countdown_direction)
                obs.set_source_visibility(obs_timer_scene, obs_timer_countup, False)
            total_seconds = write_clock(second_take, add, obs, True)
            time_now = datetime.datetime.now()
            time_sofar = float(read_clock_sofar())
            logger.info(f"{total_seconds:.2f} | {str(datetime.timedelta(seconds=int(total_seconds))).title()} | Pa;{int(pause)};{str(datetime.timedelta(seconds=pause)).title()} -- Ph;{phase};{f'{int(countdown_slow_rate_time)};{int(float(read_clock_slow_time()))}' if phase == 'S' else f'{int(countdown_rate_strict)};{int(float(read_clock_accel_time()))}' if phase == 'A' else '1;0'} | Di;{f'U;{int(countdown_up_time)}' if add else 'D;0'} -- {time_sofar} | {str(datetime.timedelta(seconds=time_sofar)).title()} -- {str(time_now.strftime(f'%b %d')).capitalize()}, {str(time_now.strftime('%I:%M:%S%p')).lower().removeprefix('0')} -- {strict_pause - ((time.monotonic() - start_time) % strict_pause)}")
            time.sleep(strict_pause - ((time.monotonic() - start_time) % strict_pause))
        except KeyboardInterrupt:
            break
    logger.info(f"{str(datetime.timedelta(seconds=float(read_clock()))).title()} {total_seconds} TESTING STUFFS")
    if total_seconds <= 0:
        logger.info("Thee countdown has reached zero seconds! Writing Reset Time!")
        with open(clock, "w") as file:
            file.write(clock_reset_time)
        obs.set_text(obs_timer_main, f"Thee Timer Has Hit Zero. Much Love To All <3")
        shutdown()


def shutdown(obs_connected: bool = True):
    if obs_connected:
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
        if not os.path.exists(clock_max):
            while True:
                cls()
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
            if float(read_clock_max()) == 0.0:
                while True:
                    cls()
                    max_seconds = input(f"Enter new max time for marathon\n")
                    if not max_seconds.isdigit():
                        print("You must enter a number")
                    else:
                        max_seconds = float(max_seconds)
                        with open(clock_max, "w") as file:
                            file.write(str(max_seconds))
                        print(f"Max time set successfully as {str(datetime.timedelta(seconds=int(max_seconds))).title()} - {max_seconds}")
                        break
        cls()
    except Exception as e:
        logger.error(f"Error in data check -- {e}")
        quit()
    try:
        obs = WebsocketsManager()
        connected = obs.connect()
        if not connected:
            logger.error(f"OBS Connection NOT Established")
            shutdown(False)
        logger.info(f"OBS Connection Established")
    except Exception as e:
        logger.error(f"Error establishing OBS connection -- {e}")
        exit()
    while True:
        cls()
        try:
            user_input = input(f"Enter 1 to enter countdown\nEnter 2 to configure countdown\nEnter 0 to quit countdown\n")
            cls()
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    print(f"Exiting countdown")
                    break
                elif user_input == 1:
                    while True:
                        user_seconds, add = loop_get_user_input_clock()
                        cls()
                        try:
                            if user_seconds.isdigit():
                                write_clock(float(user_seconds), add, obs=obs, manual=True)
                                obs.set_text(obs_timer_sofar, str(datetime.timedelta(seconds=float(read_clock_sofar()))).title())
                                input("Hit ENTER To Start Thee Timer!\n")
                                total_seconds = float(read_clock())
                                cls()
                                logger.info(f"{total_seconds} -- {str(datetime.timedelta(seconds=int(total_seconds))).title()}")  # DEBUGGING -- ++ 2 lines above -- otherwise countdown(float(read_clock()))
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
                        user_input = input(f"Enter 1 to change current time\nEnter 2 to change max time\nEnter 3 to change total time\nEnter 4 to change sofar time\nEnter 5 to change clock ACCEL rate\nEnter 6 to change clock SLOW rate\nEnter 7 to change clock pause\nEnter 0 to go back\n")
                        cls()
                        if user_input.isdigit():
                            user_input = int(user_input)
                            if user_input == 0:
                                print(f"Going back")
                                time.sleep(1)
                                break
                            elif user_input == 1:
                                reset_current_time()
                                time.sleep(2)
                            elif user_input == 2:
                                reset_max_time()
                                time.sleep(2)
                            elif user_input == 3:
                                reset_total_time()
                                time.sleep(2)
                            elif user_input == 4:
                                reset_sofar_time()
                                time.sleep(2)
                            elif user_input == 5:
                                reset_clock_accel_rate(obs)
                                time.sleep(2)
                            elif user_input == 6:
                                reset_clock_slow_rate(obs)
                                time.sleep(2)
                            elif user_input == 7:
                                reset_clock_pause()
                                time.sleep(2)
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
