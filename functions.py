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
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv
from mongoengine import Document
from obswebsocket import obsws, requests
from mongoengine import connect, disconnect_all

time_ice = 300
time_lube = 300
rate_lube = 1.25

load_dotenv()
obs_host = os.getenv("obs_host")
obs_host_test = os.getenv("obs_host_test")
obs_port = int(os.getenv("obs_port"))
obs_pass = os.getenv("obs_pass")
obs_timer_cuss = os.getenv("obs_timer_cuss")
obs_timer_ice = os.getenv("obs_timer_ice")
obs_timer_lube = os.getenv("obs_timer_lube")
obs_timer_scene = os.getenv("obs_timer_scene")
obs_timer_main = os.getenv("obs_timer_main")
obs_timer_rate = os.getenv("obs_timer_rate")
obs_timer_pause = os.getenv("obs_timer_pause")
obs_timer_countup = os.getenv("obs_timer_countup")
obs_timer_sofar = os.getenv("obs_timer_sofar")
obs_timer_systime = os.getenv("obs_timer_systime")
obs_hype_ehvent = os.getenv("obs_hype_ehvent")

mongo_login_string = os.getenv("monlog_string")  # MongoDB Login String
mongo_twitch_collection = os.getenv("montwi_string")  # Mongo Collection To Use

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal"
else:
    application_path = os.path.dirname(__file__)

data_directory = f"{application_path}\\data\\"
logs_directory = f"{application_path}\\logs\\"
archive_logs_directory = f"{logs_directory}archive_log\\"
data_bot = f"{data_directory}bot\\"
data_clock = f"{data_directory}clock\\"
data_games = f"{data_bot}games\\"
Path(data_directory).mkdir(parents=True, exist_ok=True)
Path(logs_directory).mkdir(parents=True, exist_ok=True)
Path(archive_logs_directory).mkdir(parents=True, exist_ok=True)
Path(data_bot).mkdir(parents=True, exist_ok=True)
Path(data_clock).mkdir(parents=True, exist_ok=True)

clock_reset_time = "0.0"  # STRICT value -- For timer resets
strict_pause = 1.0  # STRICT value -- For timer manipulations
countdown_rate_strict = 5.0  # Base value -- For timer rate manipulations
standard_ehvent_mult = 1.1  # Base value -- For Hype EhVents (HypeTrains)
standard_seconds = 3.6  # Base value -- For marathon related events
standard_direct_dono = 7.0  # Base value -- For marathon related events

nl = "\n"
long_dashes = "-------------------------------------------------------------------"
bot_delete_phrases = f"{data_bot}delete_phrases.txt"
bot_fish = f"{data_bot}fish_rewards"
bot_flash_frequency = f"{data_bot}flash_frequency.txt"
bot_flash_speed = f"{data_bot}flash_speed.txt"
bot_raid_mode = f"{data_bot}raid_mode.txt"
bot_mini_games = f"{data_bot}mini_games.txt"
bot_night_mode = f"{data_bot}night_mode.txt"
song_requests = f"{data_bot}song_requests.txt"

clock = f"{data_clock}main.txt"
clock_cuss = f"{data_clock}time_cuss.txt"
clock_cuss_state = f"{data_clock}state_cuss.txt"
clock_ice = f"{data_clock}time_ice.txt"
clock_ice_state = f"{data_clock}state_ice.txt"
clock_lube = f"{data_clock}time_lube.txt"
clock_lube_state = f"{data_clock}state_lube.txt"
clock_mode = f"{data_clock}mode.txt"
clock_mode_old = f"{data_clock}mode_old.txt"
clock_max = f"{data_clock}time_max.txt"
clock_pause = f"{data_clock}time_pause.txt"
clock_pause_old = f"{data_clock}time_pause_old.txt"
clock_phase = f"{data_clock}phase.txt"
clock_phase_old = f"{data_clock}phase_old.txt"
clock_phase_slow_rate = f"{data_clock}phase_slow_rate.txt"
clock_time_mode = f"{data_clock}time_mode.txt"
clock_time_phase_accel = f"{data_clock}time_phase_accel.txt"
clock_time_phase_slow = f"{data_clock}time_phase_slow.txt"
clock_sofar = f"{data_clock}time_so_far.txt"
clock_time_started = f"{data_clock}time_started.txt"
clock_total = f"{data_clock}time_total_added.txt"

game_bingo_copshow = f"{data_games}bingo-copshow.txt"
game_bingo_hellskitchen = f"{data_games}bingo-hellskitchen.txt"


class OBSWebsocketsManager:
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

    # def get_source_visibility(self, scene_name, source_name):
    #     response = self.ws.call(requests.GetSceneItemID(sceneName=scene_name, sourceName=source_name))
    #

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


def check_hype_train(channel_document: Document, time_add=None):
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


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def configure_write_to_clock(channel_document: Document, obs: OBSWebsocketsManager):
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


def configure_hype_ehvent(channel_document: Document, obs: OBSWebsocketsManager):
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
                while True:
                    user_input = input("Enter desired level to resemble\n")
                    if not user_input.isdigit():
                        print("Enter just a number")
                    else:
                        user_input = int(user_input)
                        if channel_document['data_channel']['hype_train']['current']:
                            new_value = False
                        else:
                            new_value = True
                        channel_document['data_channel']['hype_train'].update(current=new_value)
                        channel_document.save()
                        if user_input > 1:
                            mult = (user_input - 1) / 10 + standard_ehvent_mult
                        else:
                            mult = standard_ehvent_mult
                        set_hype_ehvent(obs, mult)
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
                            user_input = input(f"Enter new level\n")
                            if not user_input.isdigit():
                                print(f"You must enter a number")
                            else:
                                user_input = int(user_input)
                                channel_document['data_channel']['hype_train'].update(current_level=user_input)
                                channel_document.save()
                                print(f"Level has been set @ {user_input}")
                                if user_input > 1:
                                    mult = (user_input - 1) / 10 + standard_ehvent_mult
                                else:
                                    mult = standard_ehvent_mult
                                set_hype_ehvent(obs, mult)
                                break
                        elif user_input == 2:
                            new_level = 1
                            channel_document['data_channel']['hype_train'].update(current_level=new_level)
                            channel_document.save()
                            print(f"Level has been reset")
                            set_hype_ehvent(obs, standard_ehvent_mult)
                            break


def connect_mongo(db, alias, logger):
    try:
        client = connect(db=db, host=mongo_login_string, alias=alias)
        logger.info(f"{fortime()}: MongoDB Connected\n{long_dashes}")
        time.sleep(1)
        client.get_default_database(db)
        logger.info(f"{fortime()}: Database Loaded")
        return client
    except Exception as e:
        logger.error(f"{fortime()}: Error Connecting MongoDB -- {e}")
        return None


async def disconnect_mongo(logger):
    try:
        disconnect_all()
        logger.info(f"{long_dashes}\nDisconnected from MongoDB")
    except Exception as e:
        logger.error(f"{fortime()}: Error Disconnection MongoDB -- {e}")
        return


def define_countdown():
    add = False
    pause = read_file(clock_pause, float)
    pause_old = read_file(clock_pause_old, bool)
    countdown_up_time = read_file(clock_time_mode, float)
    countdown_slow_rate_time = read_file(clock_phase_slow_rate, float)
    old_countdown_direction = read_file(clock_mode_old, str)
    countdown_direction = read_file(clock_mode, str)
    new_countdown_direction = countdown_direction
    old_countdown_phase = read_file(clock_phase_old, str)
    countdown_phase = read_file(clock_phase, str)
    new_countdown_phase = countdown_phase
    countdown_cuss = read_file(clock_cuss, float)
    countdown_cuss_state = read_file(clock_cuss_state, bool)
    countdown_lube = read_file(clock_lube, float)
    countdown_lube_state = read_file(clock_lube_state, bool)
    return add, pause, pause_old, countdown_up_time, countdown_slow_rate_time, \
        old_countdown_direction, countdown_direction, new_countdown_direction, \
        old_countdown_phase, countdown_phase, new_countdown_phase, countdown_cuss, \
        countdown_cuss_state, countdown_lube, countdown_lube_state


def drop_zero(n: Decimal):
    """
    :param: n: number to be numberized
    :return: zero'd number

    Drop trailing 0s
    For example:
    10.100 -> 10.1
    """
    n = str(n)
    return n.rstrip('0').rstrip('.') if '.' in n else n


async def flash_window(event_type: str):
    flash_frequency = read_file(bot_flash_frequency, int)
    flash_speed = read_file(bot_flash_speed, float)
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


async def full_shutdown(logger_list):
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{logs_directory}{entry}", f"{archive_logs_directory}{entry}")
            print(f"{entry} moved to archives..")
        except Exception as e:
            print(e)
            pass


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


def numberize(n: float, decimals: int = 2) -> str:
    """
    :param n: number to be numberized
    :param decimals: number of decimal places to round to
    :return: converted number

    Converts numbers like:
    1,000 -> 1K
    1,000,000 -> 1M
    1,000,000,000 -> 1B
    1,000,000,000,000 -> 1T
    """
    is_negative_string = ""
    if n < 0:
        is_negative_string = "-"
    n = abs(Decimal(n))
    if n < 1000:
        return is_negative_string + str(drop_zero(round_num(n, decimals)))
    elif 1000 <= n < 1000000:
        if n % 1000 == 0:
            return is_negative_string + str(int(n / 1000)) + "K"
        else:
            n = n / 1000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "K"
    elif 1000000 <= n < 1000000000:
        if n % 1000000 == 0:
            return is_negative_string + str(int(n / 1000000)) + "M"
        else:
            n = n / 1000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "M"
    elif 1000000000 <= n < 1000000000000:
        if n % 1000000000 == 0:
            return is_negative_string + str(int(n / 1000000000)) + "B"
        else:
            n = n / 1000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "B"
    elif 1000000000000 <= n < 1000000000000000:
        if n % 1000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000)) + "T"
        else:
            n = n / 1000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "T"
    elif 1000000000000000 <= n < 1000000000000000000:
        if n % 1000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000)) + "Qd"
        else:
            n = n / 1000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Qd"
    elif 1000000000000000000 <= n < 1000000000000000000000:
        if n % 1000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000)) + "Qn"
        else:
            n = n / 1000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Qn"
    elif 1000000000000000000000 <= n < 1000000000000000000000000:
        if n % 1000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000)) + "Sx"
        else:
            n = n / 1000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Sx"
    elif 1000000000000000000000 <= n < 1000000000000000000000000000:
        if n % 1000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000)) + "Sp"
        else:
            n = n / 1000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Sp"
    elif 1000000000000000000000000 <= n < 1000000000000000000000000000000:
        if n % 1000000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000000)) + "Oc"
        else:
            n = n / 1000000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Oc"
    elif 1000000000000000000000000000 <= n < 1000000000000000000000000000000000:
        if n % 1000000000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000000000)) + "No"
        else:
            n = n / 1000000000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "No"
    elif 1000000000000000000000000000000 <= n < 1000000000000000000000000000000000000:
        if n % 1000000000000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000000000000)) + "De"
        else:
            n = n / 1000000000000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "De"
    else:
        return is_negative_string + str(n)


def read_file(file_name: str, return_type: any) -> bool | float | int | list | str:
    with open(file_name, "r", encoding="utf-8") as file:
        variable = file.read()
    try:
        if return_type == bool:
            if variable == "True":
                return True
            elif variable == "False":
                return False
            else:
                return f"ValueError Converting {variable} to {return_type}"
        elif type(return_type) == list:
            if return_type[1] == "split":
                variable = variable.split(return_type[2], maxsplit=return_type[3])
            elif return_type[1] == "splitlines":
                variable = variable.splitlines()
            if return_type[0] == map:
                return list(map(str, variable))
            else:
                return list(variable)
        elif return_type in (int, float):
            variable = float(variable)
            if return_type == float:
                return variable
            return int(variable)
        else:
            return str(variable)
    except ValueError:
        return f"ValueError Converting {variable} to {return_type}"


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


def reset_clock_pause(obs: OBSWebsocketsManager = None):
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
                        try:
                            user_time = float(user_time.removeprefix("+"))
                        except ValueError:
                            print("ValueError.. Try again")
                            break
                        write_clock_pause(user_time)
                        set_timer_pause(obs, True)
                        break
                    elif user_time.startswith("-"):
                        try:
                            user_time = float(user_time)
                        except ValueError:
                            print("ValueError.. Try again")
                            break
                        write_clock_pause(user_time)
                        break
                    else:
                        print("Not Valid, try again..")


def reset_clock_accel_rate(obs: OBSWebsocketsManager = None):
    while True:
        user_input = input(f"Enter 1 to add to ACCEL rate timer\nEnter 2 to remove from ACCEL rate timer\nEnter 0 to go back\n")
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
                        new_total = write_clock_time_phase_accel(float(new_rate))
                        write_clock_phase("accel")
                        if obs is not None:
                            set_timer_rate(obs, "accel")
                        print(f"Added {new_rate}.{f' {str(datetime.timedelta(seconds=new_total)).title()} remaining' if new_total != float(new_rate) else ''}")
                        break
                    else:
                        print(f"Invalid Input -- You put {new_rate} -- which is a {type(new_rate)}")
            elif user_input == 2:
                while True:
                    new_rate = input("Enter take away seconds;\n")
                    if new_rate.isdigit():
                        new_total = write_clock_time_phase_accel(-abs(float(new_rate)))
                        if new_total > 0:
                            phase = "accel"
                        elif read_file(clock_time_phase_slow, float) > 0:
                            phase = "slow"
                        else:
                            phase = "norm"
                        write_clock_phase(phase)
                        if obs is not None:
                            set_timer_rate(obs, phase)
                        print(f"Removed {new_rate} seconds, f'{str(datetime.timedelta(seconds=new_total)).title()} remaining. CurrentPhase; {phase}")
                    else:
                        print(f"Invalid Input -- You put {new_rate} which is a {type(new_rate)}")

            else:
                print(f"You must enter a number, you put {user_input} which is a {type(user_input)}")


def reset_clock_slow_rate(obs: OBSWebsocketsManager = None):
    while True:
        user_input = input(f"Enter 1 to add to countdown SLOW rate timer\nEnter 2 to remove from SLOW rate timer\nEnter 0 to go back\n")
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
                        new_total = write_clock_time_phase_slow(float(new_rate))
                        write_clock_phase("slow")
                        if obs is not None:
                            set_timer_rate(obs, "slow")
                        print(f"Added {new_rate}.{f' {str(datetime.timedelta(seconds=new_total)).title()} remaining' if new_total != float(new_rate) else ''}")
                        break
                    else:
                        print(f"Invalid Input -- You put {new_rate} -- which is a {type(new_rate)}")
            elif user_input == 2:
                while True:
                    new_rate = input("Enter take away seconds;\n")
                    if new_rate.isdigit():
                        new_total = write_clock_time_phase_slow(-abs(float(new_rate)))
                        if new_total > 0:
                            phase = "slow"
                        elif read_file(clock_time_phase_accel, float) > 0:
                            phase = "accel"
                        else:
                            phase = "norm"
                        write_clock_phase(phase)
                        if obs is not None:
                            set_timer_rate(obs, phase)
                        print(f"Removed {new_rate} seconds, f'{str(datetime.timedelta(seconds=new_total)).title()} remaining. CurrentPhase; {phase}")
                    else:
                        print(f"Invalid Input -- You put {new_rate} which is a {type(new_rate)}")
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
                current_state = read_file(bot_night_mode, bool)
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
                            file.write(new_total_time)
                        print(f"New Total Time Set @ {new_total_time_formatted}")
                        break
            elif user_input == 2:
                with open(clock_total, "w") as file:
                    file.write(clock_reset_time)
                print(f"Total Clock Reset to {clock_reset_time}")
            else:
                print(f"You must enter just a number -- you put -- {user_input} which is a {type(user_input)}")


def round_num(n: Decimal, decimals: int = 2):
    """
    :param: n: number to round
    :param: decimals: number of decimal places to round number
    :return: rounded number

    For example:
    10.0 -> 10
    10.222 -> 10.22
    """
    return n.to_integral() if n == n.to_integral() else round(n.normalize(), decimals)


def set_timer_cuss(obs: OBSWebsocketsManager, countdown_cuss: float):
    obs.set_text(obs_timer_cuss, f"No Cussing; {str(datetime.timedelta(seconds=countdown_cuss)).title()}")


def set_timer_lube(obs: OBSWebsocketsManager, new_current: float):
    obs.set_text(obs_timer_lube, f"Lube Applied {rate_lube}x; {str(datetime.timedelta(seconds=new_current)).title()}")


def set_timer_count_up(obs: OBSWebsocketsManager, time_left: float):
    obs.set_text(obs_timer_countup, f"CountUp; {str(datetime.timedelta(seconds=time_left)).title()}")


def set_timer_pause(obs: OBSWebsocketsManager, show=None):
    obs.set_text(obs_timer_pause, f"Paused; {str(datetime.timedelta(seconds=read_file(clock_pause, int))).title()}")
    if show is not None:
        obs.set_source_visibility(obs_timer_scene, obs_timer_pause, show)


def set_timer_rate(obs: OBSWebsocketsManager, phase: str = "norm"):
    if phase == "slow":
        time_left = read_file(clock_time_phase_slow, int)
    elif phase == "accel":
        time_left = read_file(clock_time_phase_accel, int)
    else:
        time_left = 0
    obs.set_text(obs_timer_rate, f"{int(countdown_rate_strict) if phase == 'slow' else int(float(strict_pause))} Real Sec/{int(float(strict_pause)) if phase == 'slow' else int(countdown_rate_strict)} Timer Sec; {str(datetime.timedelta(seconds=time_left)).title()}")


def set_timer_so_far(obs: OBSWebsocketsManager, current_sofar: int = None):
    if current_sofar is None:
        current_sofar = read_file(clock_sofar, int)
    time_now = datetime.datetime.now()
    obs.set_text(obs_timer_sofar, f"{str(datetime.timedelta(seconds=current_sofar)).title()}")
    obs.set_text(obs_timer_systime, f"{str(time_now.strftime(f'%b %d')).capitalize()}, {str(time_now.strftime('%I:%M:%S%p')).lower().removeprefix('0')}")


def set_hype_ehvent(obs: OBSWebsocketsManager, mult: float, status: str = "Enabled"):
    value = True
    obs.set_text(obs_hype_ehvent, f"HypeEhVent {status} @ {mult:.1f}X")
    if status == "Disabled":
        value = False
    obs.set_source_visibility(obs_timer_scene, obs_hype_ehvent, value)


def setup_logger(name: str, log_file: str, logger_list: list, level=logging.INFO):
    try:
        local_logger = logging.getLogger(name)
        handler = logging.FileHandler(f"{logs_directory}{log_file}", mode="w", encoding="utf-8")
        if name in ("logger", "countdown_logger"):  #, "bingo_logger"):
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


def write_bot_raid(value: bool):
    with open(bot_raid_mode, "w") as file:
        file.write(str(value))


def write_clock_cuss(value: float):
    if not read_file(clock_cuss_state, bool):
        with open(clock_cuss_state, "w") as file:
            file.write("True")
    new_current = read_file(clock_cuss, float) + value
    with open(clock_cuss, "w") as file:
        file.write(str(new_current))
    return new_current


def write_clock_lube(value: float):
    if not read_file(clock_lube_state, bool):
        with open(clock_lube_state, "w") as file:
            file.write("True")
    new_current = read_file(clock_lube, float) + value
    with open(clock_lube, "w") as file:
        file.write(str(new_current))
    return new_current


def write_clock_up_time(value: float):
    new_direction_time = read_file(clock_time_mode, float) + value
    with open(clock_time_mode, "w") as file:
        file.write(str(new_direction_time))
    return new_direction_time


def write_clock_time_phase_accel(value: float):
    new_accel_time = read_file(clock_time_phase_accel, float) + value
    if new_accel_time <= 0:
        new_accel_time = 0.0
    with open(clock_time_phase_accel, "w") as file:
        file.write(str(new_accel_time))
    return new_accel_time


def write_clock_time_phase_slow(value: float):
    new_slow_time = read_file(clock_time_phase_slow, float) + value
    if new_slow_time <= 0:
        new_slow_time = 0.0
    with open(clock_time_phase_slow, "w") as file:
        file.write(str(new_slow_time))
    return new_slow_time


def write_clock_phase_slow_rate(seconds: float):
    with open(clock_phase_slow_rate, "w") as file:
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
    with open(f"{data_bot}flash_frequency.txt", "w") as file:
        file.write(str(new_frequency))


def write_flash_speed(new_speed: float):
    with open(f"{data_bot}flash_speed.txt", "w") as file:
        file.write(str(new_speed))


def write_night_mode(new_state: bool):
    with open(f"{data_bot}night_mode.txt", "w") as file:
        file.write(str(new_state))


def write_sofar(second: float, obs: OBSWebsocketsManager = None):
    current_sofar = read_file(clock_sofar, float) + second
    with open(clock_sofar, "w") as file:
        file.write(str(current_sofar))
    if obs is not None:
        set_timer_so_far(obs, int(current_sofar))


def write_clock(seconds: float, logger, add: bool = False, obs: OBSWebsocketsManager = None, countdown: bool = False, manual: bool = False):
    try:
        formatted_missed_seconds = None
        current_seconds = read_file(clock, float)
        if read_file(clock_lube_state, bool) and not countdown:
            seconds *= rate_lube
        if add:
            max_seconds = read_file(clock_max, float)
            total_seconds = read_file(clock_total, float) + seconds
            if total_seconds > max_seconds:
                seconds_to_subtract = abs(total_seconds - max_seconds)
                seconds -= seconds_to_subtract
                total_seconds -= seconds_to_subtract
                formatted_missed_seconds = str(datetime.timedelta(seconds=int(seconds_to_subtract))).title()
                logger.warn(f"{fortime()}: WRITE_CLOCK; Went above MAX TIME -- {formatted_missed_seconds} ({seconds_to_subtract}--{int(seconds_to_subtract)}) will NOT be added")
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
            logger.error(f"{fortime()}: WRITE_CLOCK; SOMETHING WRONG... ADD VALUE == {add}, type {type(add)}")
            return None, None
        if obs is not None:
            obs.set_text(obs_timer_main, str(datetime.timedelta(seconds=int(current_seconds))).title())
        if countdown:
            write_sofar(1, obs)
            return current_seconds
        else:
            return seconds, formatted_missed_seconds
    except ValueError:
        logger.error(f"{fortime()}: WRITE_CLOCK; ValueError detected!! Returning None, None")
        return None, None
    except Exception as e:
        logger.error(f"{fortime()}: WRITE_CLOCK; Something else went wrong -- {e}")
        return None, None
