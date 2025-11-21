import os
import sys
import time
import logging
import datetime
from pathlib import Path
from dotenv import load_dotenv
from obswebsocket import obsws, requests

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal"
else:
    application_path = os.path.dirname(__file__)

logger_list = []
logs_directory = f"{application_path}\\logs\\"
archive_logs_directory = f"{logs_directory}archive_log\\"
Path(logs_directory).mkdir(parents=True, exist_ok=True)
Path(archive_logs_directory).mkdir(parents=True, exist_ok=True)

load_dotenv()
timer_scene = os.getenv("obs_mini_timer_scene_name")
mini_timer = os.getenv("obs_mini_timer_source_name")
obs_host = os.getenv("obs_host")
obs_port = int(os.getenv("obs_port"))
obs_pass = os.getenv("obs_pass")
skip_setup = False


class OBSWebsocketsManager:
    ws = None

    def __init__(self):
        self.ws = obsws(obs_host, obs_port, obs_pass)

    def connect(self):
        try:
            self.ws.connect()
            return True
        except Exception as e:
            logger.error(f"Error connecting to OBS -- {e}")
            return False
            # quit()

    def disconnect(self):
        self.ws.disconnect()

    def set_source_visibility(self, scene_name, source_name, source_visible=True):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=item_id, sceneItemEnabled=source_visible))

    def set_text(self, source_name, new_text):
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings={'text': new_text}))


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def delete_last_line():
    sys.stdout.write('\x1b[1A')
    sys.stdout.write('\x1b[2K')


def define_date():
    event_name = define_event_name()
    if event_name is not None:
        cls()
        while True:
            try:
                event_time_end = input("Enter Event End Time (yyyy/mm/dd hh:mm:ss)\nExample for January 9, 2000 @ 6:03pm\n2000/01/09 18:03:00\n")
                if event_time_end == "":
                    print("Event Time Can't Be Empty")
                else:
                    try:
                        event_time_end = datetime.datetime.strptime(event_time_end, "%Y/%m/%d %H:%M:%S")
                        if obs is not None and obs_connect:
                            obs.set_text(mini_timer, set_obs_text(event_name, str(event_time_end)))
                        break
                    except Exception as e:
                        logger.error(f"Error formatting time -- {e}")
            except KeyboardInterrupt:
                return None, None
        return event_name, event_time_end
    else:
        return event_name, None


def define_event_name():
    cls()
    while True:
        try:
            event_name = input("Enter Event Name\n")
            if event_name == "":
                print("Event Name Can't Be Empty")
            else:
                if obs is not None and obs_connect:
                    obs.set_text(mini_timer, set_obs_text(event_name, "00:00:00"))
                    obs.set_source_visibility(timer_scene, mini_timer, True)
                break
        except KeyboardInterrupt:
            return None
    return event_name


def define_timer():
    event_name = define_event_name()
    if event_name is not None:
        cls()
        while True:
            try:
                timer_time = input("Enter a desired length for thee timer in SECONDS\n")
                if timer_time.isdigit():
                    event_time_end = int(timer_time)
                    if obs is not None and obs_connect:
                        obs.set_text(mini_timer, set_obs_text(event_name, str(datetime.timedelta(seconds=event_time_end))))
                    break
                else:
                    print("Invalid Entry")
            except KeyboardInterrupt:
                return None, None
        return event_name, event_time_end

    else:
        return event_name, None


def fortime():
    try:
        return str(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error creating formatted_time -- {e}")
        return None


def shutdown(logger_list):
    print("\n\n\n\n")
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{logs_directory}{entry}", f"{archive_logs_directory}{entry}")
            print(f"{entry} moved to archives..")
        except Exception as e:
            print(e)
            pass


def set_obs_text(event_name: str, new_time: str):
    return f"{event_name}\n{new_time}"


def setup_logger(name: str, log_file: str, logger_list: list, level=logging.ERROR):
    try:
        local_logger = logging.getLogger(name)
        handler = logging.FileHandler(f"{logs_directory}{log_file}", mode="w", encoding="utf-8")
        console_handler = logging.StreamHandler()
        local_logger.addHandler(console_handler)
        local_logger.setLevel(level)
        local_logger.addHandler(handler)
        logger_list.append(f"{log_file}")
        return local_logger
    except Exception as e:
        formatted_time = fortime()
        print(f"{formatted_time}: ERROR in setup_logger - {name}/{log_file}/{level} -- {e}")
        return None


if __name__ == "__main__":
    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger("logger", f"mini_timer_log--{init_time}.log", logger_list)

    while True:
        try:
            timer_type = input("Enter 1 for 'Timer by Date'\nEnter 2 for 'Timer by Time'\n")
            if timer_type.isdigit():
                timer_type = int(timer_type)
                if timer_type in (1, 2):
                    break
                else:
                    print(f"Invalid Entry!")
            else:
                print(f"Invalid Entry!")
        except KeyboardInterrupt:
            print("Exiting App")
            skip_setup = True
            timer_type = None
            break

    obs = OBSWebsocketsManager()
    obs_connect = False
    if not skip_setup:
        if obs is None:
            obs_connect = False
            logger.error(f"{fortime()}: Error setting up OBS OBSWebsocketsManager")
            time.sleep(2)
        else:
            obs_connect = obs.connect()
            if not obs_connect:
                logger.error(f"{fortime()}: Error connecting to OBS, disabling that functionality")
                time.sleep(2)

    if timer_type == 1:
        event_name, event_time_end = define_date()
    elif timer_type == 2:
        event_name, event_time_end = define_timer()
    else:
        event_name, event_time_end = None, None

    if event_name is not None:
        cls()
        print(f"{event_name} in\n")
        if type(event_time_end) == datetime.datetime:
            current_time = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            event_time_end_seconds = int(event_time_end.timestamp())
        else:
            current_time = 0
            event_time_end_seconds = int(event_time_end)
        start_time = time.perf_counter()

        while current_time < event_time_end_seconds:
            try:
                delete_last_line()
                new_time = str(datetime.timedelta(seconds=event_time_end_seconds - current_time))
                print(new_time)
                if obs is not None and obs_connect:
                    obs.set_text(mini_timer, set_obs_text(event_name, new_time))
                current_time += 1
                time.sleep(1 - ((time.perf_counter() - start_time) % 1))
            except KeyboardInterrupt:
                print("EXITING LOOP")
                # obs.disconnect()
                break
            except Exception as e:
                logger.error(f"ERROR IN LOOP -- {e}")
                # obs.disconnect()
                break

        if current_time >= event_time_end_seconds:
            delete_last_line()
            print(f"{event_name} timer ended!")
            if obs is not None and obs_connect:
                obs.set_text(mini_timer, set_obs_text(event_name, "timer ended!"))
            try:
                time.sleep(current_time)
            except KeyboardInterrupt:
                # obs.set_source_visibility(timer_scene, mini_timer, False)
                # obs.disconnect()
                print("Exited OBS\nExiting App")

    if obs is not None and obs_connect:
        obs.set_source_visibility(timer_scene, mini_timer, False)
        obs.disconnect()
    shutdown(logger_list)
