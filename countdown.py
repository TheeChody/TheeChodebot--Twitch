import os
import time
import asyncio
import datetime
from functions import clock, clock_max, clock_pause, clock_total, clock_time_started, clock_reset_time, \
    write_clock, reset_max_time, reset_total_time, reset_current_time, loop_get_user_input_clock, reset_sofar_time, \
    clock_sofar, reset_clock_slow_rate, reset_clock_pause, OBSWebsocketsManager, fortime, setup_logger, \
    full_shutdown, cls, write_clock_phase_slow_rate, reset_clock_accel_rate, clock_time_mode, \
    clock_phase, strict_pause, countdown_rate_strict, clock_time_phase_accel, \
    clock_time_phase_slow, set_timer_rate, set_timer_count_up, set_timer_pause, obs_timer_main, obs_timer_sofar, obs_timer_scene, \
    obs_timer_rate, obs_timer_countup, clock_mode, define_countdown, write_sofar, clock_phase_old, clock_mode_old, clock_pause_old, \
    obs_timer_pause, clock_phase_slow_rate, clock_cuss_state, clock_lube_state, obs_timer_cuss, obs_timer_lube, clock_lube, clock_cuss, \
    set_timer_lube, set_timer_cuss, read_file, connect_mongo, disconnect_mongo, mongo_twitch_collection
from mongoengine import DEFAULT_CONNECTION_NAME
from mondocs import Channels

logger_list = []
slash_list = ["\\", "|", "/", "|"]


def countdown(total_seconds: float):
    def define_slash(rotation: int):
        if rotation + 1 > len(slash_list):
            rotation = 0
        slash = slash_list[rotation]
        rotation += 1
        return slash, rotation

    if read_file(clock_sofar, float) == 0.0:
        with open(clock_time_started, "w") as file:
            file.write(str(datetime.datetime.now()))

    keyboard_interrupt = False
    rotation = 0
    start_time = time.perf_counter()
    while True:
        try:
            if keyboard_interrupt:
                logger.info(f"{fortime()}: KeyBoard Interrupt Detected.. Exiting Countdown...")
                break
            add, pause, pause_old, countdown_up_time, countdown_slow_rate_time, old_countdown_direction, countdown_direction, \
                new_countdown_direction, old_countdown_phase, countdown_phase, new_countdown_phase, countdown_cuss, countdown_cuss_state, \
                countdown_lube, countdown_lube_state = define_countdown()
            if total_seconds <= 0.0 and pause == 0:
                logger.info(f"{fortime()}: Timer Reached 0 and No Pause Time!! -- total_seconds; {total_seconds} -- pause; {pause}")
                break
            if countdown_phase != old_countdown_phase:
                with open(clock_phase_old, "w") as file:
                    file.write(countdown_phase)
                if countdown_phase == "norm":
                    obs.set_source_visibility(obs_timer_scene, obs_timer_rate, False)
                else:
                    set_timer_rate(obs, countdown_phase)
            if countdown_direction == "down" != old_countdown_direction:
                with open(clock_mode_old, "w") as file:
                    file.write(countdown_direction)
                obs.set_source_visibility(obs_timer_scene, obs_timer_countup, False)
            if pause_old:
                with open(clock_pause_old, "w") as file:
                    file.write("False")
                obs.set_source_visibility(obs_timer_scene, obs_timer_pause, False)
            if pause == 0:
                if countdown_direction == "up":
                    add = True
                    countdown_up_time -= strict_pause
                    if countdown_up_time <= 0:
                        countdown_up_time = 0
                        new_countdown_direction = "down"
                    with open(clock_time_mode, "w") as file:
                        file.write(str(countdown_up_time))
                    set_timer_count_up(obs, countdown_up_time)
                if countdown_phase == "slow":
                    phase = "Slow"
                    countdown_slow_time = read_file(clock_time_phase_slow, float) - strict_pause
                    if countdown_slow_time <= 0:
                        countdown_slow_time = 0
                        if read_file(clock_time_phase_accel, float) > 0:
                            new_countdown_phase = "accel"
                        else:
                            new_countdown_phase = "norm"
                    with open(clock_time_phase_slow, "w") as file:
                        file.write(str(countdown_slow_time))
                    set_timer_rate(obs, countdown_phase)
                    if countdown_slow_rate_time <= 1.0:
                        sec_manip = strict_pause
                        countdown_slow_rate_time = countdown_rate_strict
                        write_clock_phase_slow_rate(countdown_rate_strict)
                    else:
                        countdown_slow_rate_time -= strict_pause
                        write_clock_phase_slow_rate(countdown_slow_rate_time)
                        sec_manip = 0.0
                elif countdown_phase == "accel":
                    phase = "Xcel"
                    sec_manip = countdown_rate_strict
                    countdown_accel_time = read_file(clock_time_phase_accel, float) - strict_pause
                    if countdown_accel_time <= 0:
                        countdown_accel_time = 0
                        if read_file(clock_time_phase_slow, float) > 0:
                            new_countdown_phase = "slow"
                        else:
                            new_countdown_phase = "norm"
                    with open(clock_time_phase_accel, "w") as file:
                        file.write(str(countdown_accel_time))
                    set_timer_rate(obs, countdown_phase)
                else:
                    sec_manip = strict_pause
                    phase = "Norm"
                total_seconds = write_clock(sec_manip, logger, add, obs, True, False)
                if total_seconds is None:
                    logger.error(f"{fortime()}: ValueError/Another Error Occurred in write_clock, exiting CountDown to preserve data")
                    shutdown()
                if countdown_phase != new_countdown_phase:
                    with open(clock_phase_old, "w") as file:
                        file.write(countdown_phase)
                    with open(clock_phase, "w") as file:
                        file.write(new_countdown_phase)
                if countdown_direction == "up" and new_countdown_direction == "down":
                    with open(clock_mode_old, "w") as file:
                        file.write(countdown_direction)
                    with open(clock_mode, "w") as file:
                        file.write(new_countdown_direction)
            else:
                total_seconds = read_file(clock, float)
                phase = "Pauz"
                pause -= strict_pause
                if pause <= 0:
                    pause = 0.0
                    with open(clock_pause_old, "w") as file:
                        file.write("True")
                with open(clock_pause, "w") as file:
                    file.write(str(pause))
                write_sofar(1, obs)
                set_timer_pause(obs)
            if countdown_cuss_state and countdown_cuss == 0:
                with open(clock_cuss_state, "w") as file:
                    file.write("False")
                obs.set_source_visibility(obs_timer_scene, obs_timer_cuss, False)
            elif countdown_cuss > 0:
                countdown_cuss -= 1
                if countdown_cuss <= 0:
                    countdown_cuss = 0
                with open(clock_cuss, "w") as file:
                    file.write(str(countdown_cuss))
                set_timer_cuss(obs, countdown_cuss)
            if countdown_lube_state and countdown_lube == 0:
                with open(clock_lube_state, "w") as file:
                    file.write("False")
                obs.set_source_visibility(obs_timer_scene, obs_timer_lube, False)
            elif countdown_lube > 0:
                countdown_lube -= 1
                if countdown_lube <= 0:
                    countdown_lube = 0
                with open(clock_lube, "w") as file:
                    file.write(str(countdown_lube))
                set_timer_lube(obs, countdown_lube)
            time_now = datetime.datetime.now()
            time_sofar = read_file(clock_sofar, float)
            slash, rotation = define_slash(rotation)
            logger.info(f"{total_seconds:.2f}{slash}{str(datetime.timedelta(seconds=int(total_seconds))).title()} | {phase}{slash}{f'{int(countdown_slow_rate_time)}{slash}{str(datetime.timedelta(seconds=read_file(clock_time_phase_slow, int))).title()}' if phase == 'Slow' else f'{int(countdown_rate_strict)}{slash}{str(datetime.timedelta(seconds=read_file(clock_time_phase_accel, int))).title()}' if phase == 'Xcel' else f'1{slash}{str(datetime.timedelta(seconds=int(pause))).title()}' if phase == 'Pauz' else f'1{slash}0:00:00'} | {f'Up{slash}{str(datetime.timedelta(seconds=int(countdown_up_time))).title()}' if countdown_direction == 'up' else f'Dn{slash}0:00:00'} | Cu{slash}{str(datetime.timedelta(seconds=countdown_cuss)).title()} | Lu{slash}{str(datetime.timedelta(seconds=countdown_lube)).title()} | {time_sofar}{slash}{str(datetime.timedelta(seconds=time_sofar)).title()} | {str(time_now.strftime(f'%b %d')).capitalize()}, {str(time_now.strftime('%I:%M:%S%p')).lower().removeprefix('0')} | {f'{strict_pause - ((time.perf_counter() - start_time) % strict_pause):.40f}'.removeprefix('0')}")
            time.sleep(strict_pause - ((time.perf_counter() - start_time) % strict_pause))
        except ValueError:
            logger.error(f"{fortime()}: Error in countdown -- ValueError detected!! Shutting down to preserve data")
            shutdown()
        except KeyboardInterrupt:
            keyboard_interrupt = True
            continue
    logger.info(f"{str(datetime.timedelta(seconds=read_file(clock, float))).title()} {total_seconds} TESTING STUFFS")
    if total_seconds <= 0:
        logger.info("Thee countdown has reached zero seconds! Writing Reset Time!")
        with open(clock, "w") as file:
            file.write(clock_reset_time)
        obs.set_text(obs_timer_main, f"Thee Timer Has Hit Zero. Much Love To All <3")
        try:
            logger.info(f"{fortime()}: Attempting to update channel document 'writing_clock' to 'False'")
            connect_mongo(mongo_twitch_collection, DEFAULT_CONNECTION_NAME, logger)
            channel_document = Channels.objects.get(_id="268136120")
            channel_document['data_channel']['writing_clock'] = False
            channel_document.save()
            logger.info(f"{fortime()}: Channel Document Updated -- 'writing_clock' set to 'False'")
            asyncio.run(disconnect_mongo(logger))
        except Exception as channel_doc_fail:
            logger.error(f"{fortime()}: Error updating channel document -- {channel_doc_fail}")
            pass
        shutdown()


def shutdown(obs_connected: bool = True):
    if obs_connected:
        obs.disconnect()
        logger.info(f"Disconnected from OBS")
    asyncio.run(full_shutdown(logger_list))
    print(f"Shutdown Sequence Completed")
    quit(666)


if __name__ == "__main__":
    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger('countdown_logger', f'countdown_log--{init_time}.log', logger_list)
    try:
        if not os.path.exists(clock):
            with open(clock, "w") as file:
                file.write(clock_reset_time)
            logger.info(f"File '{clock}' created first time run")
        if not os.path.exists(clock_mode):
            with open(clock_mode, "w") as file:
                file.write("down")
            logger.info(f"File '{clock_mode}' created first time run")
        if not os.path.exists(clock_mode_old):
            with open(clock_mode_old, "w") as file:
                file.write("down")
            logger.info(f"File '{clock_mode_old}' created first time run")
        if not os.path.exists(clock_pause):
            with open(clock_pause, "w") as file:
                file.write(clock_reset_time)
            logger.info(f"File '{clock_pause}' created first time run")
        if not os.path.exists(clock_pause_old):
            with open(clock_pause_old, "w") as file:
                file.write("False")
            logger.info(f"File '{clock_pause_old}' created first time run")
        if not os.path.exists(clock_phase):
            with open(clock_phase, "w") as file:
                file.write("norm")
            logger.info(f"File '{clock_phase}' created first time run")
        if not os.path.exists(clock_phase_old):
            with open(clock_phase_old, "w") as file:
                file.write("norm")
            logger.info(f"File '{clock_phase_old}' created first time run")
        if not os.path.exists(clock_phase_slow_rate):
            with open(clock_phase_slow_rate, "w") as file:
                file.write("5.0")
            logger.info(f"File '{clock_phase_slow_rate}' created first time run")
        if not os.path.exists(clock_time_mode):
            with open(clock_time_mode, "w") as file:
                file.write("0")
            logger.info(f"File '{clock_time_mode}' created first time run")
        if not os.path.exists(clock_time_phase_accel):
            with open(clock_time_phase_accel, "w") as file:
                file.write("0")
            logger.info(f"File '{clock_time_phase_accel}' created first time run")
        if not os.path.exists(clock_time_phase_slow):
            with open(clock_time_phase_slow, "w") as file:
                file.write("0")
            logger.info(f"File '{clock_time_phase_slow}' created first time run")
        if not os.path.exists(clock_sofar):
            with open(clock_sofar, "w") as file:
                file.write(clock_reset_time)
                logger.info(f"File '{clock_sofar}' created first time run")
        if not os.path.exists(clock_total):
            with open(clock_total, "w") as file:
                file.write(clock_reset_time)
            logger.info(f"File '{clock_total}' created first time run")

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
            if read_file(clock_max, float) == 0.0:
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
    obs = OBSWebsocketsManager()
    try:
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
                            user_seconds = float(user_seconds)
                            if user_seconds != 0:
                                write_clock(user_seconds, logger, add, obs=obs, manual=True)
                            obs.set_text(obs_timer_sofar, str(datetime.timedelta(seconds=read_file(clock_sofar, int))).title())
                            input("Hit ENTER To Start Thee Timer!\n")
                            cls()
                            total_seconds = read_file(clock, float)
                            logger.info(f"{total_seconds} -- {str(datetime.timedelta(seconds=int(total_seconds))).title()}")  # DEBUGGING -- ++ 2 lines above -- otherwise countdown(float(read_clock()))
                            countdown(total_seconds)
                            # countdown(read_file(clock, float))  # For Run
                        except ValueError:
                            logger.error(f"ValueError!! {user_seconds} is not floatable")
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
