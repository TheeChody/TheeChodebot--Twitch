import os
import sys
import datetime
import time
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
standard_seconds = 1.5  # Base value -- For marathon related events
# countdown_path = f"{Path(__file__).parent.absolute()}\\"
data_directory = f"{application_path}\\data\\"
logs_directory = f"{application_path}\\logs\\"
chat_log = f"{logs_directory}chat_log.log"
clock = f"{data_directory}clock.txt"
clock_sofar = f"{data_directory}clock_sofar.txt"
clock_total = f"{data_directory}clock_total_time.txt"
clock_max = f"{data_directory}clock_max_time.txt"
clock_pause = f"{data_directory}clock_pause.txt"
clock_reset_pause = "1"
# clock_reset_time = "0:00:00"
clock_reset_time = "0"
Path(data_directory).mkdir(parents=True, exist_ok=True)
Path(logs_directory).mkdir(parents=True, exist_ok=True)
long_dashes = "-------------------------------------------------"

# print(f"App -- {application_path} --- path__file__ -- {countdown_path}")  # ToDo: Figure out if I want to use Path(__file__) as thee determining app_path...


class WebsocketsManager:
    ws = None

    def __init__(self):
        self.ws = obsws(obs_host, obs_port, obs_pass)

    def connect(self):
        try:
            self.ws.connect()
        except Exception as e:
            print(f"Error connecting to OBS -- {e}")
            quit()

    def disconnect(self):
        self.ws.disconnect()

    # Set the current scene
    def set_scene(self, new_scene):
        self.ws.call(requests.SetCurrentProgramScene(sceneName=new_scene))

    # Set the visibility of any source's filters
    def set_filter_visibility(self, source_name, filter_name, filter_enabled=True):
        self.ws.call(requests.SetSourceFilterEnabled(sourceName=source_name, filterName=filter_name,
                                                     filterEnabled=filter_enabled))

    # Set the visibility of any source
    def set_source_visibility(self, scene_name, source_name, source_visible=True):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=item_id, sceneItemEnabled=source_visible))

    # Returns the current text of a text source
    def get_text(self, source_name):
        response = self.ws.call(requests.GetInputSettings(inputName=source_name))
        return response.datain["inputSettings"]["text"]

    # Returns the text of a text source
    def set_text(self, source_name, new_text):
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings={'text': new_text}))

    # def get_source_transform(self, scene_name, source_name):
    #     response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
    #     item_id = response.datain['sceneItemId']
    #     response = self.ws.call(requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=item_id))
    #     transform = {}
    #     transform["positionX"] = response.datain["sceneItemTransform"]["positionX"]
    #     transform["positionY"] = response.datain["sceneItemTransform"]["positionY"]
    #     transform["scaleX"] = response.datain["sceneItemTransform"]["scaleX"]
    #     transform["scaleY"] = response.datain["sceneItemTransform"]["scaleY"]
    #     transform["rotation"] = response.datain["sceneItemTransform"]["rotation"]
    #     transform["sourceWidth"] = response.datain["sceneItemTransform"]["sourceWidth"]  # original width of the source
    #     transform["sourceHeight"] = response.datain["sceneItemTransform"][
    #         "sourceHeight"]  # original width of the source
    #     transform["width"] = response.datain["sceneItemTransform"][
    #         "width"]  # current width of the source after scaling, not including cropping. If the source has been flipped horizontally, this number will be negative.
    #     transform["height"] = response.datain["sceneItemTransform"][
    #         "height"]  # current height of the source after scaling, not including cropping. If the source has been flipped vertically, this number will be negative.
    #     transform["cropLeft"] = response.datain["sceneItemTransform"][
    #         "cropLeft"]  # the amount cropped off the *original source width*. This is NOT scaled, must multiply by scaleX to get current # of cropped pixels
    #     transform["cropRight"] = response.datain["sceneItemTransform"][
    #         "cropRight"]  # the amount cropped off the *original source width*. This is NOT scaled, must multiply by scaleX to get current # of cropped pixels
    #     transform["cropTop"] = response.datain["sceneItemTransform"][
    #         "cropTop"]  # the amount cropped off the *original source height*. This is NOT scaled, must multiply by scaleY to get current # of cropped pixels
    #     transform["cropBottom"] = response.datain["sceneItemTransform"][
    #         "cropBottom"]  # the amount cropped off the *original source height*. This is NOT scaled, must multiply by scaleY to get current # of cropped pixels
    #     return transform

    def get_source_transform(self, scene_name, source_name):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        response = self.ws.call(requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=item_id))
        transform = {"positionX": response.datain["sceneItemTransform"]["positionX"],
                     "positionY": response.datain["sceneItemTransform"]["positionY"],
                     "scaleX": response.datain["sceneItemTransform"]["scaleX"],
                     "scaleY": response.datain["sceneItemTransform"]["scaleY"],
                     "rotation": response.datain["sceneItemTransform"]["rotation"],
                     "sourceWidth": response.datain["sceneItemTransform"]["sourceWidth"],
                     "sourceHeight": response.datain["sceneItemTransform"][
                         "sourceHeight"], "width": response.datain["sceneItemTransform"][
                "width"], "height": response.datain["sceneItemTransform"][
                "height"], "cropLeft": response.datain["sceneItemTransform"][
                "cropLeft"], "cropRight": response.datain["sceneItemTransform"][
                "cropRight"], "cropTop": response.datain["sceneItemTransform"][
                "cropTop"], "cropBottom": response.datain["sceneItemTransform"][
                "cropBottom"]}
        return transform

    # The transform should be a dictionary containing any of the following keys with corresponding values
    # positionX, positionY, scaleX, scaleY, rotation, width, height, sourceWidth, sourceHeight, cropTop, cropBottom, cropLeft, cropRight
    # e.g. {"scaleX": 2, "scaleY": 2.5}
    # Note: there are other transform settings, like alignment, etc., but these feel like the main useful ones.
    # Use get_source_transform to see the full list
    def set_source_transform(self, scene_name, source_name, new_transform):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemTransform(sceneName=scene_name, sceneItemId=item_id,
                                                    sceneItemTransform=new_transform))

    # Note: an input, like a text box, is a type of source. This will get *input-specific settings*, not the broader source settings like transform and scale
    # For a text source, this will return settings like its font, color, etc
    def get_input_settings(self, input_name):
        return self.ws.call(requests.GetInputSettings(inputName=input_name))

    # Get list of all the input types
    def get_input_kind_list(self):
        return self.ws.call(requests.GetInputKindList())

    # Get list of all items in a certain scene
    def get_scene_items(self, scene_name):
        return self.ws.call(requests.GetSceneItemList(sceneName=scene_name))


def refresh_pause():
    with open(clock_pause, "r") as file:
        return file.read()


def reset_pause():
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
                        with open(clock_pause, "w") as file:
                            file.write(new_pause_time)
                        print(f"New pause time set @ {new_pause_time}")
                        break
                    else:
                        print(f"Invalid Input -- You put {new_pause_time} -- which is a {type(new_pause_time)}")
            elif user_input == 2:
                with open(clock_pause, "w") as file:
                    file.write(clock_reset_pause)
                    print(f"Pause Time Reset to {clock_reset_pause}")
            else:
                print(f"You must enter a number, you put {user_input} which is a {type(user_input)}")

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


def write_sofar(second: float):
    with open(clock_sofar, "r") as read:
        current_sofar = read.read()
    with open(clock_sofar, "w") as file:
        # file.write(str(datetime.timedelta(seconds=get_sec(current_sofar) + second)).title())
        file.write(str(float(current_sofar) + second))


def write_clock(seconds: float, add: bool = False, channel_document: Document = None, obs=None, countdown: bool = False):
    try:
        if not countdown and add:
            seconds *= standard_seconds
        formatted_missed_seconds = None
        current_seconds = float(read_clock())
        if add:
            max_seconds = float(max_read_clock())
            total_seconds = float(total_read_clock())
            if channel_document is not None:
                if channel_document['hype_train_current']:
                    if channel_document['hype_train_current_level'] > 1:
                        seconds *= ((channel_document['hype_train_current_level'] - 1) / 10 + standard_ehvent_mult)
                    else:
                        seconds *= standard_ehvent_mult
            total_seconds += seconds
            if total_seconds > max_seconds:
                seconds_to_subtract = abs(total_seconds - max_seconds)
                seconds -= seconds_to_subtract
                total_seconds -= seconds_to_subtract
                formatted_missed_seconds = str(datetime.timedelta(seconds=round(seconds_to_subtract))).title()
                print(f"Went above MAX TIME -- {formatted_missed_seconds} ({seconds_to_subtract}--{round(seconds_to_subtract)}) will NOT be added")
            current_seconds += seconds
            with open(clock, "w") as file:
                file.write(str(current_seconds))
            with open(clock_total, "w") as file:
                file.write(str(current_seconds))
        elif not add:
            if seconds >= current_seconds != 1:  # This SHOULD Work to Counter Timer Going Below 0 or minus seconds haha
                seconds = current_seconds - 1
            current_seconds -= seconds
            with open(clock, "w") as file:
                file.write(str(current_seconds))
            if countdown:
                write_sofar(seconds)
        if obs is not None:
            obs.set_text("TwitchTimer", str(datetime.timedelta(seconds=round(current_seconds))).title())
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
