"""
All times are considered off variables and any currency related information is assumed USD
Set base seconds in 'standard_seconds'
Times Below are for normal times based on a 50/50 split
If your split is different, these numbers are not going to be accurate
(Hype EhVent seconds/cent go up, $value goes down) (default mult == 2, up by .10 per HypeTrain Level)
------------------------------------------------------------------------------------------------------------------------
0.5 second per cent is   == $72.00/60 minutes for you, $144.00/60 minutes spent by viewers to keep you live
1 second per cent is     == $36.00/60 minutes for you, $72.00/60 minutes spent by viewers to keep you live
1.5 seconds per cent is  == $27.00/60 minutes for you, $54.00/60 minutes spent by viewers to keep you live
2 seconds per cent is    == $18.00/60 minutes for you, $36.00/60 minutes spent by viewers to keep you live
2.5 seconds per cent is  == $14.40/60 minutes for you, $28.80/60 minutes spent by viewers to keep you live
3 seconds per cent is    == $12.00/60 minutes for you, $24.00/60 minutes spent by viewers to keep you live
3.5 seconds per cent is  == $10.29/60 minutes for you, $20.58/60 minutes spent by viewers to keep you live
------------------------------------------------------------------------------------------------------------------------
"""
import os
import sys
import datetime
import time
import logging
from dotenv import load_dotenv
from pathlib import Path
from mongoengine import Document
from obswebsocket import obsws, requests

load_dotenv()
obs_host = os.getenv("obs_host")
obs_host_test = os.getenv("obs_host_test")
obs_port = int(os.getenv("obs_port"))
obs_pass = os.getenv("obs_pass")

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

standard_ehvent_mult = 2
standard_seconds = 1.0  # Base value -- For marathon related events
data_directory = f"{application_path}\\data\\"
alerts = f"{data_directory}audio\\alerts\\"
logs_directory = f"{application_path}\\logs\\"
chat_log = f"{logs_directory}chat_log.log"
clock = f"{data_directory}clock.txt"
clock_sofar = f"{data_directory}clock_sofar.txt"
clock_total = f"{data_directory}clock_total_time.txt"
clock_max = f"{data_directory}clock_max_time.txt"
clock_pause = f"{data_directory}clock_pause.txt"
clock_reset_pause = "1.0"
clock_reset_time = "0.0"
Path(data_directory).mkdir(parents=True, exist_ok=True)
Path(logs_directory).mkdir(parents=True, exist_ok=True)
long_dashes = "-------------------------------------------------"


class WebsocketsManager:
    ws = None

    def __init__(self):
        self.ws = obsws(obs_host, obs_port, obs_pass)

    def connect(self):
        try:
            self.ws.connect()
            return True
        except Exception as e:
            print(f"Error connecting to OBS -- {e}")
            return False
            # quit()

    def disconnect(self):
        self.ws.disconnect()

    def set_scene(self, new_scene):
        self.ws.call(requests.SetCurrentProgramScene(sceneName=new_scene))

    def set_filter_visibility(self, source_name, filter_name, filter_enabled=True):
        self.ws.call(requests.SetSourceFilterEnabled(sourceName=source_name, filterName=filter_name,
                                                     filterEnabled=filter_enabled))

    def set_source_visibility(self, scene_name, source_name, source_visible=True):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=item_id, sceneItemEnabled=source_visible))

    def get_text(self, source_name):
        response = self.ws.call(requests.GetInputSettings(inputName=source_name))
        return response.datain["inputSettings"]["text"]

    def set_text(self, source_name, new_text):
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings={'text': new_text}))

    def get_source_transform(self, scene_name, source_name):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        # print(response)
        item_id = response.datain['sceneItemId']
        response = self.ws.call(requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=item_id))
        # print(response)
        transform = {"positionX": response.datain["sceneItemTransform"]["positionX"],
                     "positionY": response.datain["sceneItemTransform"]["positionY"],
                     "scaleX": response.datain["sceneItemTransform"]["scaleX"],
                     "scaleY": response.datain["sceneItemTransform"]["scaleY"],
                     "rotation": response.datain["sceneItemTransform"]["rotation"],
                     "sourceWidth": response.datain["sceneItemTransform"]["sourceWidth"],
                     "sourceHeight": response.datain["sceneItemTransform"]["sourceHeight"],
                     "width": response.datain["sceneItemTransform"]["width"],
                     "height": response.datain["sceneItemTransform"]["height"],
                     "cropLeft": response.datain["sceneItemTransform"]["cropLeft"],
                     "cropRight": response.datain["sceneItemTransform"]["cropRight"],
                     "cropTop": response.datain["sceneItemTransform"]["cropTop"],
                     "cropBottom": response.datain["sceneItemTransform"]["cropBottom"]}
        return transform

    def set_source_transform(self, scene_name, source_name, new_transform):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemTransform(sceneName=scene_name, sceneItemId=item_id,
                                                    sceneItemTransform=new_transform))

    def get_input_settings(self, input_name):
        return self.ws.call(requests.GetInputSettings(inputName=input_name))

    def set_input_settings(self, input_name, new_input_setting):
        return self.ws.call(requests.SetInputSettings(inputName=input_name, inputSettings=new_input_setting))

    def get_input_kind_list(self):
        return self.ws.call(requests.GetInputKindList())

    def get_scene_items(self, scene_name):
        return self.ws.call(requests.GetSceneItemList(sceneName=scene_name))


def fortime():
    try:
        return str(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'))
    except Exception as e:
        print(f"Error creating formatted_time -- {e}")
        return None


def setup_logger(name: str, log_file: str, logger_list: list, level: logging = logging.INFO):
    try:
        local_logger = logging.getLogger(name)
        if name == "chat_logger":
            handler = logging.FileHandler(f"{logs_directory}{log_file}", mode="w", encoding="utf-8")
        else:
            handler = logging.FileHandler(f"{logs_directory}{log_file}")
        # if name != "chat_logger":
        if name not in ("chat_logger", "special_logger"):
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


def full_shutdown(logger_list):
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{logs_directory}{entry}", f"{logs_directory}\\archive_log\\{entry}")
        except Exception as e:
            print(e)
            pass
    quit(420)


def configure_write_to_clock(channel_document: Document, obs: WebsocketsManager):
    if channel_document['data_channel']['writing_clock']:
        new_value = False
    else:
        new_value = True
    channel_document['data_channel'].update(writing_clock=new_value)
    channel_document.save()
    obs.set_source_visibility("NS-Marathon", "TwitchTimer", new_value)
    # try:  # ToDo: FIGURE OUT WHY THIS TELLS ME REWARD ID IS FOR ANOTHER CHANNEL OR MY CHANNEL DOESN'T HAVE REWARDS ENABLED.....
    #     for reward_id in marathon_rewards:
    #         await bot.update_custom_reward(id_streamer, reward_id, is_enabled=channel_document['data_channel']['writing_clock'])
    #         special_logger.info(f"{reward_id} is now {'EN' if channel_document['data_channel']['writing_clock'] else 'DIS'}ABLED")
    # except Exception as f:
    #     logger.error(f"Error switching rewards on/off for channel_document['data_channel']['writing_clock'] -- bot loop -- {f}")
    #     pass
    print(f"Writing to clock is now {'EN' if new_value else 'DIS'}ABLED")


def configure_hype_ehvent(channel_document: Document, obs: WebsocketsManager):
    while True:
        user_input = input(
            f"Enter 1 to EN/DIS Able HypeEhVent\nEnter 2 to Configure HypeEhVent Level\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"Must enter a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going Back")
                break
            elif user_input == 1:
                if channel_document['data_channel']['hype_train']['current']:
                    new_value = False
                else:
                    new_value = True
                obs.set_text("HypeEhVent", f"Hype EhVent {'En' if new_value else 'Dis'}abled -- 2X")
                obs.set_source_visibility("NS-Marathon", "HypeEhVent", new_value)
                channel_document['data_channel']['hype_train'].update(current=new_value)
                channel_document.save()
                print(f"Thee Hype EhVent(TRAIN_VARIABLE) is now {'EN' if new_value else 'DIS'}ABLED")
                break
            elif user_input == 2:
                while True:
                    user_input = input(f"Enter 1 to change level\nEnter 2 to reset level\n")
                    if not user_input.isdigit():
                        print(f"You must enter a number")
                    else:
                        user_input = int(user_input)
                        if user_input == 1:
                            new_level = input(f"Enter new level\n")
                            if not new_level.isdigit():
                                print(f"You must enter a number")
                            else:
                                new_level = int(new_level)
                                channel_document['data_channel']['hype_train'].update(current_level=new_level)
                                channel_document.save()
                                print(f"Level has been set @ {new_level}")
                                if new_level > 1:
                                    mult = (new_level - 1) / 10 + standard_ehvent_mult
                                else:
                                    mult = standard_ehvent_mult
                                obs.set_text("HypeEhVent", f"Hype EhVent Enabled -- {mult:.1f}X")
                                break
                        elif user_input == 2:
                            new_level = 1
                            channel_document['data_channel']['hype_train'].update(current_level=new_level)
                            channel_document.save()
                            print(f"Level has been reset")
                            obs.set_text("HypeEhVent", f"Hype EhVent Enabled -- {standard_ehvent_mult}X")
                            break


def reset_pause(obs: WebsocketsManager = None):
    while True:
        user_input = input(f"Enter 1 to change current pause\nEnter 2 to reset current pause\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                break
            elif user_input == 1:
                while True:
                    new_pause_time = input("Enter new speed in SECONDS\n")
                    if new_pause_time.isdigit():
                        new_pause_time = float(new_pause_time)
                        with open(clock_pause, "w") as file:
                            file.write(str(new_pause_time))
                        print(f"New pause time set @ {new_pause_time}")
                        if obs is not None:
                            if new_pause_time == 2.0:
                                obs.set_source_visibility("NS-Marathon", "TimerSpeed", True)
                            else:
                                obs.set_source_visibility("NS-Marathon", "TimerSpeed", False)
                        break
                    else:
                        print(f"Invalid Input -- You put {new_pause_time} -- which is a {type(new_pause_time)}")
            elif user_input == 2:
                with open(clock_pause, "w") as file:
                    file.write(clock_reset_pause)
                    print(f"Pause Time Reset to {clock_reset_pause}")
                    if obs is not None:
                        obs.set_source_visibility("NS-Marathon", "TimerSpeed", False)
            else:
                print(f"You must enter a number, you put {user_input} which is a {type(user_input)}")


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
        if "." in s:
            s, ms = s.split(".")
            ms = f"0.{ms}"
        else:
            ms = 0
        return float(d) * 86400 + float(h) * 3600 + float(m) * 60 + float(s) + float(ms)
    else:
        h, m, s = timer.split(':')
        if "." in s:
            s, ms = s.split(".")
            ms = f"0.{ms}"
        else:
            ms = 0
        return float(h) * 3600 + float(m) * 60 + float(s) + float(ms)


def read_clock():
    with open(clock, "r") as file:
        return file.read()


def max_read_clock():
    with open(clock_max, "r") as file:
        return file.read()


def read_pause():
    with open(clock_pause, "r") as file:
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
                        new_time_formatted = str(datetime.timedelta(seconds=new_time)).title()
                        with open(clock, "w") as file:
                            file.write(new_time_formatted)
                        print(f"New current time set @ {new_time_formatted}")
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
                        new_max_formatted = str(datetime.timedelta(seconds=new_max_seconds)).title()
                        with open(clock_max, "w") as file:
                            file.write(new_max_formatted)
                        print(f"New max time set @ {new_max_formatted}")
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


def write_sofar(second: float, obs: WebsocketsManager = None):
    with open(clock_sofar, "r") as read:
        current_sofar = float(read.read())
    with open(clock_sofar, "w") as file:
        file.write(str(current_sofar + second))
    if obs is not None and (current_sofar + second) % 86400.0 == 0.0:
        obs.set_text("Day", f"Day {str(int(((current_sofar + second) / 86400.0) + 1))}")


def write_clock(seconds: float, add: bool = False, channel_document: Document = None, obs: WebsocketsManager = None, countdown: bool = False, manual: bool = False):
    try:
        formatted_missed_seconds = None
        current_seconds = float(read_clock())
        if add:
            max_seconds = float(max_read_clock())
            total_seconds = float(total_read_clock())
            if channel_document is not None:
                if channel_document['data_channel']['hype_train']['current']:
                    if channel_document['data_channel']['hype_train']['current_level'] > 1:
                        seconds *= ((channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult)
                    else:
                        seconds *= standard_ehvent_mult
            total_seconds += seconds
            if total_seconds > max_seconds:
                seconds_to_subtract = abs(total_seconds - max_seconds)
                seconds -= seconds_to_subtract
                total_seconds -= seconds_to_subtract
                formatted_missed_seconds = str(datetime.timedelta(seconds=int(seconds_to_subtract))).title()
                print(f"Went above MAX TIME -- {formatted_missed_seconds} ({seconds_to_subtract}--{int(seconds_to_subtract)}) will NOT be added")
            current_seconds += seconds
            with open(clock, "w") as file:
                file.write(str(current_seconds))
            if not manual:
                with open(clock_total, "w") as file:
                    file.write(str(total_seconds))
        elif not add:
            if seconds >= current_seconds != 1:  # This SHOULD Work to Counter Timer Going Below 0 or minus seconds haha.
                seconds = current_seconds - 1
            current_seconds -= seconds
            with open(clock, "w") as file:
                file.write(str(current_seconds))
        else:
            print(f"SOMETHING WRONG... ADD VALUE == {add}")
            return None, None
        if obs is not None:
            obs.set_text("TwitchTimer", str(datetime.timedelta(seconds=int(current_seconds))).title())
        if countdown:
            write_sofar(seconds, obs)
            return current_seconds
        else:
            return seconds, formatted_missed_seconds
    except ValueError:
        print(f"Attempted to go negative time")
        with open(clock, "r") as read:
            old_time = read.read()
        with open(clock, "w") as file:
            file.write(clock_reset_time)
        print(f"Overwrote to prevent issues. old time was: {old_time}({datetime.timedelta(seconds=int(float(old_time)))})")
        return None, None
    except Exception as e:
        print(f"Something else went wrong -- {e}")
        return None, None
