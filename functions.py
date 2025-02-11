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
3.6 seconds per cent is  == $10.00/60 minutes for you, $20.00/60 minutes spent by viewers to keep you live
------------------------------------------------------------------------------------------------------------------------
"""
import os
import sys
import datetime
import time
import logging
import asyncio
from dotenv import load_dotenv
from pathlib import Path
from mongoengine import Document
from obswebsocket import obsws, requests

load_dotenv()
obs_host = os.getenv("obs_host")
obs_host_test = os.getenv("obs_host_test")
obs_port = int(os.getenv("obs_port"))
obs_pass = os.getenv("obs_pass")
obs_timer_scene = os.getenv("obs_timer_scene")
obs_timer_main = os.getenv("obs_timer_main")
obs_timer_rate = os.getenv("obs_timer_rate")
obs_timer_pause = os.getenv("obs_timer_pause")
obs_timer_countup = os.getenv("obs_timer_countup")
obs_timer_sofar = os.getenv("obs_timer_sofar")
obs_hype_ehvent = os.getenv("obs_hype_ehvent")

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal"
else:
    application_path = os.path.dirname(__file__)

clock_reset_time = "0.0"
strict_pause = 1.0
countdown_rate_strict = 5.0
standard_ehvent_mult = 1.1
standard_seconds = 3.6  # Base value -- For marathon related events
standard_direct_dono = 7.0  # Base value -- For marathon related events
data_directory = f"{application_path}\\data\\"
alerts = f"{data_directory}audio\\alerts\\"
logs_directory = f"{application_path}\\logs\\"
bot_raid_mode = f"{data_directory}bot_raid_mode.txt"
bot_mini_games = f"{data_directory}bot_mini_games.txt"  # ToDo: Implement this on bot side to allow for toggleable mini-game usage
chat_log = f"{logs_directory}chat_log.log"
clock_slow_rate_time = f"{data_directory}clock_slow_rate_time.txt"
clock_accel_time = f"{data_directory}clock_accel_time.txt"
clock_direction = f"{data_directory}clock_direction.txt"
clock_direction_time = f"{data_directory}clock_direction_time.txt"
clock_slow_time = f"{data_directory}clock_slow_time.txt"
clock = f"{data_directory}clock.txt"
clock_sofar = f"{data_directory}clock_sofar.txt"
clock_total = f"{data_directory}clock_total_time.txt"
clock_max = f"{data_directory}clock_max_time.txt"
clock_pause = f"{data_directory}clock_pause.txt"
clock_phase = f"{data_directory}clock_phase.txt"
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


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


async def flash_window(event_type: str):
    flash_frequency = int(read_flash_frequency())
    flash_speed = float(read_flash_speed())
    if event_type == "twitch":
        colour = "57"
    elif event_type == "attn":
        colour = "47"
    else:
        colour = "27"
    os.system(f"color {colour}")
    await asyncio.sleep(flash_speed)
    for x in range(1, flash_frequency):
        os.system(f"color 07")
        await asyncio.sleep(flash_speed)
        os.system(f"color {colour}")
        await asyncio.sleep(flash_speed)
    os.system(f"color 07")


def fortime():
    try:
        return str(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'))
    except Exception as e:
        print(f"Error creating formatted_time -- {e}")
        return None


def setup_logger(name: str, log_file: str, logger_list: list, level: logging = logging.INFO):
    try:
        local_logger = logging.getLogger(name)
        handler = logging.FileHandler(f"{logs_directory}{log_file}", mode="w", encoding="utf-8")
        if name not in ("chat_logger", "special_logger", "gamble_log"):
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


async def full_shutdown(logger_list):
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{logs_directory}{entry}", f"{logs_directory}\\archive_log\\{entry}")
        except Exception as e:
            print(e)
            pass
    quit(420)


def check_hype_train(channel_document: Document, time_add: any):
    if time_add is None:
        if channel_document['data_channel']['hype_train']['current_level'] > 1:
            return (channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult
        else:
            return standard_ehvent_mult
    else:
        if channel_document['data_channel']['hype_train']['current']:
            if channel_document['data_channel']['hype_train']['current_level'] > 1:
                time_add *= (channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult
            else:
                time_add *= standard_ehvent_mult
        return time_add


def configure_write_to_clock(channel_document: Document, obs: WebsocketsManager):
    if channel_document['data_channel']['writing_clock']:
        new_value = False
    else:
        new_value = True
    channel_document['data_channel'].update(writing_clock=new_value)
    channel_document.save()
    obs.set_source_visibility("NS-Marathon", "TwitchTimer", new_value)
    obs.set_source_visibility("NS-Marathon", "TwitchTimerSoFar", new_value)
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
        user_input = input(f"Enter 1 to EN/DIS Able HypeEhVent\nEnter 2 to Configure HypeEhVent Level\nEnter 0 to go back\n")
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


def read_bot_raid():
    with open(bot_raid_mode, "r") as file:
        return file.read()


def read_clock_slow_rate_time():
    with open(clock_slow_rate_time, "r") as file:
        return file.read()


def read_clock_accel_time():
    with open(clock_accel_time, "r") as file:
        return file.read()


def read_clock_slow_time():
    with open(clock_slow_time, "r") as file:
        return file.read()


def read_clock_direction():
    with open(clock_direction, "r") as file:
        return file.read()


def read_clock_up_time():
    with open(clock_direction_time, "r") as file:
        return file.read()


def read_clock():
    with open(clock, "r") as file:
        return file.read()


def read_clock_max():
    with open(clock_max, "r") as file:
        return file.read()


def read_clock_pause():
    with open(clock_pause, "r") as file:
        return file.read()


def read_clock_phase():
    with open(clock_phase, "r") as file:
        return file.read()


def read_clock_total():
    with open(clock_total, "r") as file:
        return file.read()


def read_clock_sofar():
    with open(clock_sofar, "r") as file:
        return file.read()


def read_flash_frequency():
    with open(f"{data_directory}flash_frequency.txt", "r") as file:
        return file.read()


def read_flash_speed():
    with open(f"{data_directory}flash_speed.txt", "r") as file:
        return file.read()


def read_night_mode():
    with open(f"{data_directory}night_mode.txt", "r") as file:
        state = file.read()
    if state == "True":
        return True
    elif state == "False":
        return False
    else:
        print(f"{fortime()}: Error in read_night_mode -- '{state}' is NOT True or False!!! {type(state)}")
        return False


def reset_bot_raid():
    while True:
        user_input = input("Enter 1 to ENABLE bot protection mode\nEnter 2 to DISABLE bot protection mode\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print("You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print("Going back..")
                break
            elif user_input == 1:
                write_bot_raid(True)
                print("Bot Raid Protection ENABLED")
            elif user_input == 2:
                write_bot_raid(False)
                print("Bot Raid Protection DISABLED")
            else:
                print("That wasn't valid")


def reset_clock_pause(obs: WebsocketsManager = None):
    while True:
        user_input = input("Enter 1 to add/remove time from countdown pause\nEnter 2 to reset current countdown pause\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print("Going back")
                break
            elif user_input == 1:
                while True:
                    user_time = input("Enter +/- number to add/remove time\n")
                    if user_time.startswith("+"):
                        user_time = float(user_time.removeprefix("+"))
                        write_clock_pause(user_time)
                        set_timer_pause(obs, True)
                        break
                    elif user_time.startswith("-"):
                        user_time = float(user_time)
                        write_clock_pause(user_time)
                        break
                    else:
                        print("Not Valid, try again..")


def reset_clock_accel_rate(obs: WebsocketsManager = None):
    while True:
        user_input = input(f"Enter 1 to add to ACCEL rate timer\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                break
            elif user_input == 1:
                while True:
                    new_rate = input("Enter additional seconds;\n")
                    if new_rate.isdigit():
                        new_total = write_clock_accel_time(float(new_rate))
                        write_clock_phase("accel")
                        if obs is not None:
                            set_timer_rate(obs, new_total)
                        print(f"Added {new_rate}.{f' {str(datetime.timedelta(seconds=new_total)).title()} remaining' if new_total != float(new_rate) else ''}")
                        break
                    else:
                        print(f"Invalid Input -- You put {new_rate} -- which is a {type(new_rate)}")
            else:
                print(f"You must enter a number, you put {user_input} which is a {type(user_input)}")


def reset_clock_slow_rate(obs: WebsocketsManager = None):
    while True:
        user_input = input(f"Enter 1 to change current countdown SLOW rate\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print(f"You must enter just a number")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print(f"Going back")
                break
            elif user_input == 1:
                while True:
                    new_rate = input("Enter new speed in SECONDS\n")
                    if new_rate.isdigit():
                        new_total = write_clock_slow_time(float(new_rate))
                        write_clock_phase("slow")
                        if obs is not None:
                            set_timer_rate(obs, new_total)
                        print(f"Added {new_rate}.{f' {str(datetime.timedelta(seconds=new_total)).title()} remaining' if new_total != float(new_rate) else ''}")
                        break
                    else:
                        print(f"Invalid Input -- You put {new_rate} -- which is a {type(new_rate)}")
            else:
                print(f"You must enter a number, you put {user_input} which is a {type(user_input)}")


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
                        new_time_formatted = str(datetime.timedelta(seconds=int(new_time))).title()
                        with open(clock, "w") as file:
                            # file.write(new_time_formatted)
                            file.write(new_time)
                        print(f"New current time set @ {new_time_formatted}")
                        break
            elif user_input == 2:
                with open(clock, "w") as file:
                    file.write(clock_reset_time)
                    print(f"Current Clock Reset to {clock_reset_time}")
            else:
                print(f"You must enter a number, you put {user_input} which is a {type(user_input)}")


def reset_flash_settings():
    while True:
        user_input = input("Enter 1 to change Frequency\nEnter 2 to change Speed\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print("You must enter a number!!")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print("Going back..")
                break
            elif user_input == 1:
                while True:
                    user_input = input("Enter new Frequency setting\n")
                    if not user_input.isdigit():
                        print("You must enter a number!!")
                    else:
                        write_flash_frequency(int(user_input))
                        break
            elif user_input == 2:
                while True:
                    user_input = input("Enter new Speed setting\n")
                    try:
                        float(user_input)
                        write_flash_speed(float(user_input))
                        break
                    except ValueError:
                        print(f"You must enter a number")


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
                        new_max_formatted = str(datetime.timedelta(seconds=int(new_max_seconds))).title()
                        with open(clock_max, "w") as file:
                            # file.write(new_max_formatted)
                            file.write(new_max_seconds)
                        print(f"New max time set @ {new_max_formatted}")
                        break
            elif user_input == 2:
                with open(clock_max, "w") as file:
                    file.write(clock_reset_time)
                print(f"Max Clock reset to {clock_reset_time}")
            else:
                print(f"numbers only!! you put {user_input} which is a {type(user_input)}")


def reset_night_mode():
    while True:
        user_input = input(f"Enter 1 to Enable/Disable Night Mode\nEnter 0 to go back\n")
        if not user_input.isdigit():
            print("You must enter a number!!")
        else:
            user_input = int(user_input)
            if user_input == 0:
                print("Going back..")
                break
            elif user_input == 1:
                new_state = False
                current_state = read_night_mode()
                if not current_state:
                    new_state = True
                write_night_mode(new_state)
                print(f"Night mode is now {'En' if new_state else 'Dis'}abled")


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
                            # file.write(new_sofar_time_formatted)
                            file.write(new_total_time)
                        print(f"New So Far Time Set @ {new_sofar_time_formatted}")
                        break
            elif user_input == 2:
                with open(clock_sofar, "w") as file:
                    file.write(clock_reset_time)
                    print(f"So Far Clock Reset to {clock_reset_time}")
            else:
                print(f"You must enter just a number -- you put -- {user_input} which is a {type(user_input)}")


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
                            # file.write(new_total_time_formatted)
                            file.write(new_total_time)
                        print(f"New Total Time Set @ {new_total_time_formatted}")
                        break
            elif user_input == 2:
                with open(clock_total, "w") as file:
                    file.write(clock_reset_time)
                    print(f"Total Clock Reset to {clock_reset_time}")
            else:
                print(f"You must enter just a number -- you put -- {user_input} which is a {type(user_input)}")


def write_bot_raid(value: bool):
    with open(bot_raid_mode, "w") as file:
        file.write(str(value))


def write_clock_up_time(value: float):
    with open(clock_direction_time, "r") as file:
        current_direction_time = float(file.read())
    new_direction_time = current_direction_time + value
    with open(clock_direction_time, "w") as file:
        file.write(str(new_direction_time))
    return new_direction_time


def write_clock_accel_time(value: float):
    with open(clock_accel_time, "r") as file:
        current_accel_time = float(file.read())
    new_accel_time = current_accel_time + value
    with open(clock_accel_time, "w") as file:
        file.write(str(new_accel_time))
    return new_accel_time


def write_clock_slow_time(value: float):
    with open(clock_slow_time, "r") as file:
        current_slow_time = float(file.read())
    new_slow_time = current_slow_time + value
    with open(clock_slow_time, "w") as file:
        file.write(str(new_slow_time))
    return new_slow_time


def write_clock_slow_rate_time(seconds: float):
    with open(clock_slow_rate_time, "w") as file:
        file.write(str(seconds))


def write_clock_pause(seconds: float):
    with open(clock_pause, "r") as file:
        current_pause = float(file.read())
    new_pause = current_pause + seconds
    with open(clock_pause, "w") as file:
        file.write(str(new_pause))
    return new_pause


def write_clock_phase(phase: str):
    with open(clock_phase, "w") as file:
        file.write(phase)


def write_flash_frequency(new_frequency: int):
    with open(f"{data_directory}flash_frequency.txt", "w") as file:
        file.write(str(new_frequency))


def write_flash_speed(new_speed: float):
    with open(f"{data_directory}flash_speed.txt", "w") as file:
        file.write(str(new_speed))


def write_night_mode(new_state: bool):
    with open(f"{data_directory}night_mode.txt", "w") as file:
        file.write(str(new_state))


def set_timer_count_up(obs: WebsocketsManager, time_left: float):
    obs.set_text("TimerCountUp", f"CountUp; {str(datetime.timedelta(seconds=time_left)).title()}")


def set_timer_pause(obs: WebsocketsManager, show: any = None):
    obs.set_text("TwitchTimerPause", f"Paused; {str(datetime.timedelta(seconds=int(float(read_clock_pause())))).title()}")
    if show is not None:
        obs.set_source_visibility("NS-Marathon", "TwitchTimerPause", show)


def set_timer_rate(obs: WebsocketsManager, time_left: float):
    phase = read_clock_phase()
    obs.set_text("TimerSpeed", f"Timer Rate @ {int(countdown_rate_strict) if phase == 'slow' else int(float(strict_pause))} Real Sec/{int(float(strict_pause)) if phase == 'slow' else int(countdown_rate_strict)} Timer Sec; {str(datetime.timedelta(seconds=time_left)).title()}")


def set_timer_so_far(obs: WebsocketsManager, current_sofar: float = float(read_clock_sofar())):
    time_now = datetime.datetime.now()
    obs.set_text("TwitchTimerSoFar", f"{str(datetime.timedelta(seconds=int(current_sofar))).title()} | {str(time_now.strftime(f'%b %d')).capitalize()}, {str(time_now.strftime('%I:%M:%S%p')).lower().removeprefix('0')}")


def set_hype_ehvent(obs: WebsocketsManager, mult: float, status: str = "Enabled"):
    value = True
    obs.set_text("HypeEhVent", f"HypeEhVent {status} @ {mult:.1f}X")
    if status == "Disabled":
        value = False
    obs.set_source_visibility("NS-Marathon", "HypeEhVent", value)


def write_sofar(second: float, obs: WebsocketsManager = None):
    current_sofar = float(read_clock_sofar()) + second
    with open(clock_sofar, "w") as file:
        file.write(str(current_sofar))
    if obs is not None:
        set_timer_so_far(obs, current_sofar)


def write_clock(seconds: float, add: bool = False, obs: WebsocketsManager = None, countdown: bool = False, manual: bool = False):  #,logger: logging = None):
    try:
        formatted_missed_seconds = None
        current_seconds = float(read_clock())
        if add:
            max_seconds = float(read_clock_max())
            total_seconds = float(read_clock_total())
            # if channel_document is not None:
            #     if channel_document['data_channel']['hype_train']['current']:
            #         if channel_document['data_channel']['hype_train']['current_level'] > 1:
            #             seconds *= ((channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult)
            #         else:
            #             seconds *= standard_ehvent_mult
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
            if seconds == 0:
                pass
            else:
                if seconds >= current_seconds != 1:  # This SHOULD Work to Counter Timer Going Below 0 or minus seconds haha.
                    seconds = current_seconds - 1
                current_seconds -= seconds
                with open(clock, "w") as file:
                    file.write(str(current_seconds))
        else:
            print(f"SOMETHING WRONG... ADD VALUE == {add}, type {type(add)}")
            return None, None
        if obs is not None:
            obs.set_text("TwitchTimer", str(datetime.timedelta(seconds=int(current_seconds))).title())
            if seconds == 0 and (countdown or not manual):
                set_timer_pause(obs)
        if countdown:
            write_sofar(1, obs)
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
