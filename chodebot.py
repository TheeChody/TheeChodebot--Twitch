import os
import sys
import time
import random
import asyncio
import datetime
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from mondocs import Channels, Users
from pyprobs import Probability as pr
from timeit import default_timer as timer
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, TwitchBackendException
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME, Document
from twitchAPI.object.eventsub import ChannelAdBreakBeginEvent, ChannelChatMessageEvent, ChannelChatNotificationEvent, \
    ChannelCheerEvent, ChannelFollowEvent, ChannelPollBeginEvent, ChannelPointsCustomRewardRedemptionAddEvent, ChannelPollEndEvent, \
    ChannelPredictionEvent, ChannelRaidEvent, ChannelSubscribeEvent, ChannelSubscriptionGiftEvent, ChannelUpdateEvent, HypeTrainEvent, \
    HypeTrainEndEvent, StreamOnlineEvent, StreamOfflineEvent
from functions import bot_delete_phrases, check_hype_train, clock_mode, cls, configure_write_to_clock, countdown_rate_strict, \
    flash_window, fortime, full_shutdown, load_dotenv, logs_directory, long_dashes, loop_get_user_input_clock, obs_timer_countup, \
    obs_hype_ehvent, obs_timer_main, obs_timer_pause, obs_timer_rate, obs_timer_scene, obs_timer_sofar, read_bot_minigames, read_bot_raid, \
    read_clock, read_clock_time_phase_accel, read_clock_max, read_night_mode, read_clock_pause, read_clock_phase, read_clock_time_phase_slow, \
    read_clock_sofar, read_clock_total, read_clock_up_time, reset_bot_raid, reset_clock_accel_rate, reset_clock_slow_rate, reset_clock_pause, \
    reset_current_time, reset_flash_settings, reset_max_time, reset_night_mode, reset_total_time, standard_seconds, setup_logger, \
    standard_direct_dono, set_timer_pause, set_timer_rate, set_timer_count_up, strict_pause, set_hype_ehvent, standard_ehvent_mult, \
    WebsocketsManager, write_clock, write_clock_time_phase_accel, write_clock_pause, write_clock_phase, write_clock_time_phase_slow, \
    write_clock_up_time, read_fish_pond, nl, obs_timer_systime, numberize, configure_hype_ehvent, write_clock_cuss, obs_timer_cuss, \
    obs_timer_lube, write_clock_lube, time_lube, time_ice, rate_lube, set_timer_lube, set_timer_cuss

# ToDo List ------------------------------------------------------------------------------------------------------------
#  Figure out music queueing system, gonna need ability to manipulate VLC player. or make my own? haha, yeah right
#  addon to ^^ use pytube to gather track info/download video if not downloaded already
#  Add Translation from MorseCode to English  -- Still unsure of this one..
#  Bowling mini game - think it over
#  Make the Lube/Ice time adders/slowers for the time being added -- if someone uses their 'lube for thee timer' it adds a slight bonus for a few minutes, and if someone plays the ice it slows it down for a bit
#  ---------------------------------------------------- End of List ----------------------------------------------------

load_dotenv()
name_streamer = os.getenv("name")
id_streamer = os.getenv("broadcaster")  # Your Twitch User ID
id_twitch_client = os.getenv("client")  # Your Twitch Dev App Client ID
id_twitch_secret = os.getenv("secret")  # Your Twitch Dev App Secret ID
mongo_login_string = os.getenv("monlog_string")  # MongoDB Login String
mongo_twitch_collection = os.getenv("montwi_string")  # Mongo Collection To Use
link_clips = os.getenv("link_clip").format(name_streamer)  # Used for clip command
link_tip = os.getenv("link_tip")  # Link to direct dono
link_discord = os.getenv("link_discord")  # Link to Discord
link_loots = os.getenv("link_loots")  # Link to streamloots page (if one)
link_loots_discount = os.getenv("link_loots_discount")  # Link to streamloots discount code (if one)
link_loots_coupon_blank = os.getenv("link_loots_coupon_blank")  # Link to streamloots blank coupon code for !freepack redemption
link_throne = os.getenv("link_throne")  # Link to Throne Wishlist
link_treatstream = os.getenv("link_treatstream")
response_thanks = os.getenv("response_thanks")  # A response message one wants to be repeated at thee end of monetary things
channel_point_name = os.getenv("channel_point_name")  # Your channel point name

cmd = ("$", "!", "¡")  # What thee commands can start with
target_scopes = [AuthScope.BITS_READ, AuthScope.CLIPS_EDIT, AuthScope.CHANNEL_BOT, AuthScope.USER_READ_CHAT, AuthScope.USER_WRITE_CHAT,
                 AuthScope.CHANNEL_MODERATE, AuthScope.CHANNEL_READ_ADS, AuthScope.CHANNEL_MANAGE_ADS, AuthScope.CHANNEL_READ_GOALS,
                 AuthScope.USER_READ_BROADCAST, AuthScope.CHANNEL_MANAGE_POLLS, AuthScope.USER_MANAGE_WHISPERS, AuthScope.CHANNEL_SUBSCRIPTIONS,
                 AuthScope.CHANNEL_READ_HYPE_TRAIN, AuthScope.MODERATOR_READ_CHATTERS, AuthScope.MODERATOR_READ_FOLLOWERS,
                 AuthScope.CHANNEL_READ_PREDICTIONS, AuthScope.MODERATOR_MANAGE_SHOUTOUTS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
                 AuthScope.CHANNEL_READ_SUBSCRIPTIONS, AuthScope.CHANNEL_MANAGE_PREDICTIONS, AuthScope.MODERATOR_MANAGE_BANNED_USERS,
                 AuthScope.MODERATOR_MANAGE_CHAT_MESSAGES, AuthScope.MODERATION_READ, AuthScope.CHANNEL_MANAGE_MODERATORS,
                 AuthScope.MODERATOR_MANAGE_ANNOUNCEMENTS, AuthScope.MODERATOR_MANAGE_WARNINGS]
logger_list = []

lines = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard"
    },
    1: {
        "cost": 5000,
        "effect": 5,
        "level": 1,
        "name": "Common"
    },
    2: {
        "cost": 25000,
        "effect": 10,
        "level": 2,
        "name": "UnCommon"
    },
    3: {
        "cost": 500000,
        "effect": 20,
        "level": 3,
        "name": "Rare"
    },
    4: {
        "cost": 5000000,
        "effect": 30,
        "level": 4,
        "name": "Epic"
    },
    5: {
        "cost": 25000000,
        "effect": 45,
        "level": 5,
        "name": "Legendary"
    },
    6: {
        "cost": 500000000,
        "effect": 60,
        "level": 6,
        "name": "TheeLine"
    }
}
lures = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard",
        "pLow": 0.0,
        "pHigh": 100.0
    },
    1: {
        "cost": 5000,
        "effect": 2.5,
        "level": 1,
        "name": "Common",
        "pLow": 85.0,
        "pHigh": 98.0
    },
    2: {
        "cost": 25000,
        "effect": 5,
        "level": 2,
        "name": "UnCommon",
        "pLow": 72.5,
        "pHigh": 94.0
    },
    3: {
        "cost": 500000,
        "effect": 10,
        "level": 3,
        "name": "Rare",
        "pLow": 50.0,
        "pHigh": 88.0
    },
    4: {
        "cost": 5000000,
        "effect": 15,
        "level": 4,
        "name": "Epic",
        "pLow": 34.0,
        "pHigh": 80.0
    },
    5: {
        "cost": 25000000,
        "effect": 20,
        "level": 5,
        "name": "Legendary",
        "pLow": 16.9,
        "pHigh": 69.0
    },
    6: {
        "cost": 500000000,
        "effect": 30,
        "level": 6,
        "name": "TheeLure",
        "pLow": 16.9,
        "pHigh": 50.0
    }
}
reels = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard",
        "pLow": 0,
        "pHigh": 100
    },
    1: {
        "cost": 5000,
        "effect": 5,
        "level": 1,
        "name": "Common",
        "pLow": 0,
        "pHigh": 100
    },
    2: {
        "cost": 25000,
        "effect": 10,
        "level": 2,
        "name": "UnCommon",
        "pLow": 0,
        "pHigh": 100
    },
    3: {
        "cost": 500000,
        "effect": 15,
        "level": 3,
        "name": "Rare",
        "pLow": 0,
        "pHigh": 100
    },
    4: {
        "cost": 5000000,
        "effect": 30,
        "level": 4,
        "name": "Epic",
        "pLow": 0,
        "pHigh": 100
    },
    5: {
        "cost": 25000000,
        "effect": 45,
        "level": 5,
        "name": "Legendary",
        "pLow": 0,
        "pHigh": 100
    },
    6: {
        "cost": 500000000,
        "effect": 60,
        "level": 6,
        "name": "TheeLure",
        "pLow": 0,
        "pHigh": 100
    },
}
rods = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard",
        "pLow": 0,
        "pHigh": 100
    },
    1: {
        "cost": 5000,
        "effect": 2.5,
        "level": 1,
        "name": "Common",
        "pLow": 0,
        "pHigh": 100
    },
    2: {
        "cost": 25000,
        "effect": 5,
        "level": 2,
        "name": "UnCommon",
        "pLow": 0,
        "pHigh": 100
    },
    3: {
        "cost": 500000,
        "effect": 10,
        "level": 3,
        "name": "Rare",
        "pLow": 0,
        "pHigh": 100
    },
    4: {
        "cost": 5000000,
        "effect": 15,
        "level": 4,
        "name": "Epic",
        "pLow": 0,
        "pHigh": 100
    },
    5: {
        "cost": 25000000,
        "effect": 20,
        "level": 5,
        "name": "Legendary",
        "pLow": 0,
        "pHigh": 100
    },
    6: {
        "cost": 500000000,
        "effect": 30,
        "level": 6,
        "name": "TheeLure",
        "pLow": 0,
        "pHigh": 100
    },
}

angry_items = ("an aggressive dragon", "an aggressive midget", "an aggressive carnage", "an aggressive mullens", "an aggressive pious")
fish_special_items = ("some ice for thee timer", "some lube for thee timer")
weapon_tuple = ("a dildo", "a beer bottle", "a brick", "a stabby stab knife", "a bundle of flowers", "a broom", "Gordon Ramsey's Knife", "a goldfish", "some ankle restraints for thee timer")
shield_tuple = ("a body", "a moist dude", "a dragon", "a snake", "all of maylore's trash", "a comedian", "Gordon Ramsey's Jacket", "a true friend", "shat's golden balls")

options_webcam = ("Colour", "Flip", "Spin")
options_webcam_colours = ("None", "Blue", "Green", "Hidden", "Magenta", "Red")
options_eq_colour = ("Blue", "Green", "Magenta", "Red", "White")

id_streamloots = "451658633"
id_chodebot = "1023291886"
marathon_name = "Hell-A-Thon"
boost_checkin = 5000
boost_tag = 1000
bot_name = "ChodyBot"
level_const = 150  # Base level Value
raid_seconds = 15  # Only for points now
follow_seconds = 30  # Only for points now
standard_points = 1  # Base value -- points for chatting, bitties, subbing/resubbing, gifting subbies etc.
stream_loots_seconds = 1.8  # How many seconds per CARD purchased is added
stream_loots_pack_quantity = 3  # How many cards are in ONE Pack
fish_auto_cost = 20  # AutoCast Cost
fish_cut_cost = 1000  # CastCut Cost
fish_cut_time = 1800  #7200  # CastCut CoolDown
jail_cost = 5000  # JailAttempt Cost -- ProbationOff = 1/5 -- ShieldOn *= 5
jail_time = 300  # TimeIn Jail
jail_wait_time = 1800  # JailCoolDown "Probation"
jail_shield_time = 7200  # JailProtectionTime
jail_shield_clear_time = 600  # JailProtectionClearTime
free_pack_cost = 25000  # FreePack Cost
free_pack_time = 28800  # FreePack CoolDown


class BotSetup(Twitch):
    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, app_secret)
        self.bot = Twitch


async def on_stream_ad_start(data: ChannelAdBreakBeginEvent):
    try:
        if not read_night_mode():
            marathon_response = None
            # old_pause = float(read_pause())
            # if old_pause not in (1.0, 2.0):
            #     old_pause = 1.0
            if data.event.is_automatic:
                auto_response = "this is a automatically scheduled ad break"
            else:
                auto_response = "this is a manually ran ad to attempt to time things better"
            ad_schedule = await bot.get_ad_schedule(id_streamer)
            ad_till_next_seconds, now_time_seconds = await get_ad_time(ad_schedule)
            ad_length = float(ad_schedule.duration)
            seconds_till_ad = ad_till_next_seconds - now_time_seconds
            await bot.send_chat_announcement(id_streamer, id_streamer, f"Incoming ad break, {auto_response} and should only last {datetime.timedelta(seconds=ad_length)}. Next ad inbound in {datetime.timedelta(seconds=seconds_till_ad)}.{f' {marathon_response}.' if marathon_response is not None else ''}", color="purple")
            # channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
            # if channel_document['data_channel']['writing_clock']:
            #     with open(clock_pause, "w") as file:
            #         file.write(str(ad_length))
            #     special_logger.info(f"{fortime()}: Wrote pause time in on_stream_ad_start: {datetime.timedelta(seconds=ad_length)}")
            #     marathon_response = f"Marathon Timer Paused"
            # obs.set_source_visibility("NS-Overlay", "InAd", True)
            # if channel_document['data_channel']['writing_clock']:
            #     await asyncio.sleep(old_pause + 1)
            #     with open(clock_pause, "w") as file:
            #         file.write(str(old_pause))
            #     special_logger.info(f"{fortime()}: Wrote pause time in on_stream_ad_start: {old_pause}")
            # await asyncio.sleep(ad_length - (old_pause + 1) if channel_document['data_channel']['writing_clock'] else ad_length)
            # await asyncio.sleep(ad_length)
            # obs.set_source_visibility("NS-Overlay", "InAd", False)
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_ad_start' -- {e}")
        return


async def on_stream_chat_message(data: ChannelChatMessageEvent):
    def end_timer(function_string: str):
        special_logger.info(f"fin--{function_string} -- {timer() - start}")

    def error_command(command_string: str, error_msg: Exception):
        logger.error(f"{fortime()}: Error in on_stream_chat_message -- {command_string} -- {error_msg}")
        end_timer(command_string)

    async def check_float(check: str):
        try:
            check = float(check)
        except ValueError:
            await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} {check} is not a float-type number.. Try again", reply_parent_message_id=data.event.message_id)
            return None
        return check

    async def twitch_backend():
        try:
            await asyncio.sleep(1)
            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} wait a min, try again, TwitchBackendException Raised...", reply_parent_message_id=data.event.message_id)
            logger.error(f"{fortime()}: TwitchBackendException Raised\n{data}\n")
        except Exception as growlz:
            await asyncio.sleep(1)
            logger.error(f"{fortime()}: TwitchBackendException Raised NOT HANDLED!! -- {growlz}\n{data}\n")
            return

    async def chatter_doc_swap(user_name: str, channel_document: Document, points: float):
        try:
            if user_name == "chabette9731":
                user_name = "chabette973"
            elif user_name == "karenglass":
                user_name = "peaches_003"
            elif user_name == "aromaticroaster":
                user_name = "aromatic_roaster"
            chatter_document = Users.objects.get(name=user_name)
            chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points / 4)  # / 2)
            channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
            channel_document['data_games']['gamble']['total'] += points
            channel_document.save()
            return chatter_document, response_level, None
        except Exception as g:
            if FileNotFoundError:
                return None, None, f"Hey {user_name}, make sure your StreamLoots name is thee same as your Twitch UserName eh? You missed out on {points} points."
            else:
                logger.error(f"{fortime()}: Error in chatter_doc_swap -- {g}")
                return None, None, g

    async def refresh_chatter_document(data, target_id=None, target_name=None, target_login=None):
        if target_id is not None:
            chatter_document = await get_chatter_document(None, user_id=target_id, user_name=target_name, user_login=target_login, b_id=id_streamer, b_name=name_streamer)
        else:
            chatter_document = await get_chatter_document(data)
        return chatter_document

    start = timer()
    try:
        response_was_lurk = None
        chatter_id = data.event.chatter_user_id
        channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
        if channel_document is None:
            special_logger.error(f"channel_document is None!!!")
            return
        if chatter_id in channel_document['data_lists']['ignore'] and not data.event.message.text.startswith(cmd):
            end_timer("chatter_id_in_ignore_list")
            return
        if chatter_id == id_streamer and not data.event.message.text.startswith(cmd):
            end_timer("streamer_id_no_cmd")
            return
        # ToDo: FIX THIS CRAP BELOW  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  SOMETHING IS NOT SPLITTING RIGHT
        if chatter_id == id_streamloots and not data.event.message.text.startswith(cmd):
            """username has gifted QUANTITY packs to the community. Claim yours now! LINK_HERE"""
            msg = data.event.message.text
            special_logger.info(msg)
            if "has gifted" in msg:
                name, quantity = msg.split(" has gifted ", maxsplit=1)
                if 'packs' in quantity:
                    quantity, _ = quantity.split("packs", maxsplit=1)
                else:
                    quantity, _ = quantity.split("pack", maxsplit=1)
                quantity = quantity.replace(" ", "")
                if not quantity.isdigit():
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- streamloots gifted community packs -- {name} {type(name)} - {quantity} {type(quantity)}")
                    end_timer("has gifted bit -- quantity is NOT a digit")
                    return
                seconds = int(quantity) * ((stream_loots_seconds * 100) * stream_loots_pack_quantity)
                if channel_document['data_channel']['hype_train']['current']:
                    seconds = check_hype_train(channel_document, seconds)
                seconds, time_not = write_clock(seconds, logger, True, obs)
                chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                if success is None:
                    points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                else:
                    points = None
                await bot.send_chat_message(id_streamer, id_streamer, f"{name} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'} Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}")
            return
        chatter_username = data.event.chatter_user_name
        chatter_document = await get_chatter_document(data, channel_document)
        if chatter_document is None and chatter_id not in channel_document['data_lists']['ignore']:
            special_logger.error(f"Chatter Document is None!! -- chatter-{chatter_username} -- channel-{channel_document}")
            return
        if chatter_id in channel_document['data_lists']['lurk']:
            response_was_lurk = f"Well, lookie who came back from thee shadows, {chatter_username}."
            try:
                channel_document['data_lists']['lurk'].remove(chatter_id)
                channel_document.save()
                channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                if data.event.message.text.startswith(cmd):
                    command = data.event.message.text
                    for letter in cmd:
                        command = command.removeprefix(letter)
                    if not command.startswith(("lurk", "brb")):
                        await bot.send_chat_message(id_streamer, id_streamer, response_was_lurk)
                else:
                    await bot.send_chat_message(id_streamer, id_streamer, response_was_lurk)
            except Exception as f:
                logger.error(f"{fortime()}: Error in on_stream_chat_message -- welcome back from lurk bit -- {f}")
                pass
        response, response_ranword, response_level, old_response_level, command = None, None, None, None, None
        if data.event.message.text.startswith(cmd):
            command = data.event.message.text
            for letter in cmd:
                command = command.removeprefix(letter)
            command = command.lower()
            command_check = command.replace(" ", "")
            # General Commands
            if command_check.startswith(("bittiesleader", "bitsleader")):
                try:
                    bits_lb = await bot.get_bits_leaderboard()
                    users_board = []
                    for n, user in enumerate(bits_lb):
                        if n == 5:
                            break
                        users_board.append(f"#{user.rank:02d}: {user.user_name}: {numberize(user.score)}")
                    await bot.send_chat_message(id_streamer, id_streamer,
                                                f"Bitties 4 Titties Leaderboard: {' - '.join(users_board)}",
                                                reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("bittiesleader", f)
                    return
            elif command_check.startswith("clip"):
                try:
                    now_time = datetime.datetime.now()
                    if channel_document['data_channel']['last_clip'] is None: pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(channel_document['data_channel']['last_clip'])) < 30 and chatter_id != id_streamer:
                        await bot.send_chat_message(id_streamer, id_streamer, f"There has already been a clip taken within thee last 30 seconds")
                        end_timer("clip command")
                        return
                    created_clip = await bot.create_clip(id_streamer, True)
                    channel_document['data_channel'].update(last_clip=datetime.datetime.now())
                    channel_document.save()
                    await asyncio.sleep(5)
                    await bot.send_chat_message(id_streamer, id_streamer, f"Clip can be seen at; {link_clips}{created_clip.id}", reply_parent_message_id=data.event.message_id)
                    logger.info(f"Clip Created by: {chatter_username}\nWATCH: {link_clips}{created_clip.id}\nEDIT: {created_clip.edit_url}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("clip command", f)
                    return
            elif command_check.startswith(("command", "cmd", "commandlist", "cmdlist")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Registered commands can be found in the 'BIP' extension activated in Component 1", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("commands command", f)
                    return
            elif command_check.startswith("discord"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee discord link is: {link_discord}",
                                                reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("discord command", f)
                    return
            elif command_check.startswith(("directdono", "tip")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, link_tip)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("tip command", f)
                    return
            elif command_check.startswith(("followage", "followtime")):
                try:
                    target_id, target_name = None, None
                    if command.replace(" ", "").removeprefix("followage").removeprefix("followtime").startswith("@"):
                        target_name = command.replace(" ", "").removeprefix("followage@").removeprefix("followtime@")
                        users_collection = twitch_database.twitch.get_collection('users')
                        users = users_collection.find({})
                        for user in users:
                            if user['name'].lower() == target_name:
                                target_name = user['name']
                                target_id = user['_id']
                                break
                        if target_id is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"Error fetching target_id.")
                            end_timer("followage command")
                            return
                        elif target_id == id_streamer:
                            end_timer("")
                            return
                        chatter = await bot.get_channel_followers(id_streamer, user_id=target_id)
                    else:
                        if chatter_id == id_streamer:
                            end_timer("")
                            return
                        chatter = await bot.get_channel_followers(id_streamer, user_id=chatter_id)
                    user_follow_seconds = await get_long_sec(fortime_long(chatter.data[0].followed_at.astimezone()))
                    now_seconds = await get_long_sec(fortime_long(datetime.datetime.now()))
                    await bot.send_chat_message(id_streamer, id_streamer, f"{f'You have' if target_id is None else f'{target_name} has'} been following for {str(datetime.timedelta(seconds=abs(user_follow_seconds - now_seconds))).title()}.", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("followage command", f)
                    return
            elif command_check.startswith(("lastcomment", "lastmessage")):
                if chatter_id == id_streamer:
                    end_timer("lastcomment command")
                    return
                try:
                    last_message = None
                    with open(f"{logs_directory}chat_log--{init_time}.log", "r", encoding="utf-8") as file:
                        chat_logs = file.read()
                    chat_logs = list(map(str, chat_logs.splitlines()))
                    for last in reversed(chat_logs):
                        if last.startswith(chatter_id):
                            user_name, last_message = last.split(": ", maxsplit=1)
                            break
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name}!! {chatter_username}'s last message was: {last_message if not None else 'Not Found!!!'}")
                    await flash_window("attn")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("lastcomment command", f)
                    return
            elif command_check.startswith(("lurk", "brb")):
                try:
                    if chatter_id not in channel_document['data_lists']['lurk'] and chatter_id != id_streamer:
                        channel_document['data_lists']['lurk'].append(chatter_id)
                        channel_document.save()
                        response_lurk = f"{chatter_username} fades off into thee shadows. {response_thanks}"
                        if response_was_lurk is None:
                            await bot.send_chat_message(id_streamer, id_streamer, response_lurk)
                        else:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{response_was_lurk} && {response_lurk}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("lurk command", f)
                    return
            elif command_check.startswith("pointsburn"):
                try:
                    points_burn = command_check.removeprefix("pointsburn")
                    try:
                        points_burn = abs(float(points_burn))
                    except ValueError:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} your 'points_value' isn't valid, try again", reply_parent_message_id=data.event.message_id)
                        end_timer("pointsburn fail")
                        return
                    except Exception as g:
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- pointsburn command -- {g}")
                        end_timer("pointsburn fail general exception")
                        return
                    if chatter_document['data_user']['rank']['points'] < points_burn:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you don't have enough {bot_name} Points to burn {numberize(points_burn)}, you have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points.", reply_parent_message_id=data.event.message_id)
                        end_timer("points burn not enuff")
                        return
                    chatter_document['data_user']['rank']['points'] -= points_burn
                    chatter_document.save()
                    chatter_document = await get_chatter_document(data)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you have successfully burnt {numberize(points_burn)} {bot_name} Points and have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points remaining.")
                    end_timer("pointsburn success")
                    return
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("pointsburn command", f)
                    return
            elif command_check.startswith(("throne", "wishlist")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, link_throne)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("throne command", f)
                    return
            elif command_check.startswith(("treat", "food")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, link_treatstream)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("treat command", f)
                    return
            # OBS Commands
            elif command_check.startswith("eqcolour"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"This is temp not available")
                    end_timer("eqcoulour command")
                    return
                    # if chatter_document['data_user']['rank']['points'] < 100 and chatter_id != id_streamer:
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enuff points for that, need 100 CP you have {numberize(chatter_document['data_user']['rank']['points'])} CP", reply_parent_message_id=data.event.message_id)
                    #     end_timer("eqcolour command")
                    #     return
                    # colour = command.replace(" ", "").removeprefix("eqcolour").title()
                    # if colour not in options_eq_colour:
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"Valid Colours are: '{'/'.join(list(options_eq_colour))}'", reply_parent_message_id=data.event.message_id)
                    #     end_timer("eqcolour command")
                    #     return
                    # success = change_colour_eq(colour)
                    # if success:
                    #     if chatter_id != id_streamer:
                    #         new_user_points = chatter_document['data_user']['rank']['points'] - 100
                    #         chatter_document['data_user'].update(points=new_user_points)
                    #         chatter_document.save()
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} changes thee colour to {colour.title()} with 100 chodybot points")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("eqcolour command", f)
                    return
            elif command_check.startswith("webcam"):
                try:  # Flip, filters, (un)hide
                    await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} this command is temp unavailable", reply_parent_message_id=data.event.message_id)
                    # new_colour = ""
                    # if chatter_document['data_user']['rank']['points'] < 100 and chatter_id != id_streamer:
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enuff points for that, need 100 CP you have {numberize(chatter_document['data_user']['rank']['points'])} CP", reply_parent_message_id=data.event.message_id)
                    #     end_timer("webcam command")
                    #     return
                    # action = command.replace(" ", "").removeprefix("webcam").title()
                    # if not action.startswith(options_webcam):
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"Valid options are: '{'/'.join(list(options_webcam))}'", reply_parent_message_id=data.event.message_id)
                    #     end_timer("webcam command")
                    #     return
                    # if action.startswith("Colour"):
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"This part is temp not available")
                    #     end_timer("webcam command -- colour")
                    #     return
                    #     # new_colour = action.removeprefix("Colour")
                    #     # action = action.removesuffix(new_colour)
                    #     # success = await change_webcam("colour", new_colour=new_colour.title())
                    # else:
                    #     success = await change_webcam("transform", new_transform=action)
                    # if success:
                    #     if chatter_id != id_streamer:
                    #         new_user_points = chatter_document['data_user']['rank']['points'] - 100
                    #         chatter_document['data_user']['rank'].update(points=new_user_points)
                    #         chatter_document.save()
                    #     response_webcam = f"{chatter_username} {f'{action}s {data.event.broadcaster_user_name}' if action != 'Colour' else f'changed thee {action} of {data.event.broadcaster_user_name} to {new_colour.title()}'} for 100 {bot_name} Points"
                    # else:
                    #     response_webcam = f"{chatter_username} your command was not registered, no points taken.", f"Valid colours are: {f'|'.join(list(options_webcam_colours))}" if action.startswith("Colour") else ""
                    # await bot.send_chat_message(id_streamer, id_streamer, response_webcam)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("webcam command", f)
                    return
            # Level/Points Commands
            elif command_check.startswith(("levelcheck", "levelscheck", "checklevel")):
                rank = None
                try:
                    command_level = command_check.removeprefix("levelcheck")
                    command_level = command_level.removeprefix("levelscheck")
                    command_level = command_level.removeprefix("checklevel")
                    if command_level.startswith("@") or command_level != "":
                        target_username = command_level.removeprefix("@")
                        target_username = target_username.replace(" ", "")
                        try:
                            target_document = Users.objects.get(name=target_username)
                        except FileNotFoundError:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target_username} couldn't be found!! Try again or make sure thee user has chatted here before.", reply_parent_message_id=data.event.message_id)
                            end_timer("level_check - target_document not found")
                            return
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in level_check -- target_document load -- {g}")
                            end_timer("level_check -- target_document load")
                            return
                        try:
                            users_collection = twitch_database.twitch.get_collection('users')
                            users = users_collection.find({})
                            users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['xp'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == target_document['_id']:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- levelcheck command -- fetching user rank on leaderboard -- {target_username} -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']} is Level(XP): {target_document['data_user']['rank']['level']:,}({numberize(target_document['data_user']['rank']['xp'])}) & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    elif chatter_document is not None:
                        try:
                            users_collection = twitch_database.twitch.get_collection('users')
                            users = users_collection.find({})
                            users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['xp'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == chatter_id:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- levelcheck command -- fetching user rank on leaderboard -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are Level(XP): {chatter_document['data_user']['rank']['level']:,}({numberize(chatter_document['data_user']['rank']['xp'])}) & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong getting your chatter_document", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("levelcheck command", f)
                    return
            elif command_check.startswith(("levelleader", "levelsleader", "leaderlevel")):
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    users = users_collection.find({})
                    users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['xp'], reverse=True)
                    response_leader = []
                    for n, user in enumerate(users_sorted[:5]):
                        response_leader.append(f"{n+1}: {user['name']} Lvl(XP):{user['data_user']['rank']['level']:,}({numberize(user['data_user']['rank']['xp'])})")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Leaderboard: {' - '.join(response_leader)}")
                    # guild_pipeline = [
                    #     {
                    #         "$group": {
                    #             "_id": "$data_user.channel.id",
                    #             "total_points": {
                    #                 "$sum": "$data_user.points"
                    #             }
                    #         }
                    #     },
                    #     {
                    #         "$sort": {
                    #             "total_points": -1
                    #         }
                    #     }
                    # ]
                    # results = users_collection.aggregate(guild_pipeline)
                    # response_leader = []
                    # for n, user in enumerate(results[:5]):
                    #     response_leader.append(f"{n + 1}: {user['name']} Lvl(XP):{user['data_user']['rank']['level']:,}({numberize(user['data_user']['rank']['xp'])})")
                    # await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name}'s Leaderboard: {' - '.join(response_leader)}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("levelleader command", f)
                    return
            elif command_check.startswith(("pointscheck", "pointcheck", "checkpoints")):
                rank = None
                try:
                    command_points = command_check.removeprefix("pointscheck")
                    command_points = command_points.removeprefix("pointcheck")
                    command_points = command_points.removeprefix("checkpoints")
                    if command_points.startswith("@") or command_points != "":
                        target_username = command_points
                        target_username = target_username.removeprefix("@")
                        target_username = target_username.replace(" ", "")
                        try:
                            target_document = Users.objects.get(name=target_username)
                        except FileNotFoundError:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target_username} couldn't be found!! Try again or make sure thee user has chatted here before.", reply_parent_message_id=data.event.message_id)
                            end_timer("point_check - target_document not found")
                            return
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in level_check -- target_document load -- {target_username} -- {g}")
                            end_timer("level_check -- target_document load")
                            return
                        try:
                            users_collection = twitch_database.twitch.get_collection('users')
                            users = users_collection.find({})
                            users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['points'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == target_document['_id']:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- pointscheck command -- fetching user rank on leaderboard -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']} has {numberize(target_document['data_user']['rank']['points'])} points & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    elif chatter_document is not None:
                        try:
                            users_collection = twitch_database.twitch.get_collection('users')
                            users = users_collection.find({})
                            users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['points'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == chatter_id:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- pointscheck command -- fetching user rank on leaderboard -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"You have {numberize(chatter_document['data_user']['rank']['points'])} points & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong getting your chatter_document", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("pointscheck command", f)
                    return
            elif command_check.startswith(("pointsleader", "pointleader", "leaderpoints")):
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    users = users_collection.find({})
                    users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['points'], reverse=True)
                    response_points_leader = ""
                    for n, user in enumerate(users_sorted[:5]):
                        response_points_leader += f"{n+1}: {user['name']}/{numberize(user['data_user']['rank']['points'])} - "
                    await bot.send_chat_message(id_streamer, id_streamer, response_points_leader[:-3], reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("pointsleader command", f)
                    return
            # Mini-Game Commands
            elif command_check.startswith(("bite", "burn", "kick", "lick", "pants", "pinch", "pounce", "punch", "slap", "tickle")) and read_bot_minigames():  # and chatter_id in (streamer.id, id_chodebot):
                try:
                    stats = False
                    target = None
                    if " " in command:
                        command, rest = command.split(" ", maxsplit=1)
                        if rest.startswith("stats"):
                            stats = True
                            command = command.removesuffix("stats")
                        elif rest.startswith("@"):
                            target_user_name = rest.replace("@", "")
                            target = await select_target(channel_document, chatter_id, True, target_user_name, command)
                            if target is None:
                                await bot.send_chat_message(id_streamer, id_streamer, f"{target_user_name} isn't a valid target!", reply_parent_message_id=data.event.message_id)
                                end_timer(f"{command} command")
                                return
                        else:
                            target = await select_target(channel_document, chatter_id, game_type=command)
                            if target is None:
                                await bot.send_chat_message(id_streamer, id_streamer, f"Couldn't locate a valid target!!", reply_parent_message_id=data.event.message_id)
                                end_timer(f"{command} command")
                                return
                    else:
                        if command.endswith("stats"):
                            stats = True
                            command = command.removesuffix("stats")
                        target = await select_target(channel_document, chatter_id, game_type=command)
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"Couldn't locate a valid target!!", reply_parent_message_id=data.event.message_id)
                            end_timer(f"{command} command")
                            return
                    if command == "bite":
                        adj = "bit"
                    elif command == "burn":
                        adj = "burned"
                    elif command == "kick":
                        adj = "kicked"
                    elif command == "lick":
                        adj = "licked"
                    elif command == "pants":
                        adj = "pantsed"
                    elif command == "pinch":
                        adj = "pinched"
                    elif command == "pounce":
                        adj = "pounced"
                    elif command == "punch":
                        adj = "punched"
                    elif command == "slap":
                        adj = "slapped"
                    elif command == "tickle":
                        adj = "tickled"
                    else:
                        adj = f"ERROR"
                    if stats:
                        await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} your {command} stats are (Aggressor/Defender); {chatter_document['data_games']['other'][command][f'times_{command}']}/{chatter_document['data_games']['other'][command][f'times_{adj}']}")
                        end_timer(f"{command} command - stats")
                        return
                    with open(f"data/bot/options_{command}", "r") as file:
                        options = file.read()
                    choices = list(map(str, options.splitlines()))
                    choice = random.choice(choices)
                    if adj != "ERROR":
                        target_document = Users.objects.get(name=target.user_name.lower())
                        if target_document is not None:
                            target_document['data_games']['other'][command][f'times_{adj}'] += 1
                            target_document.save()
                        chatter_document['data_games']['other'][command][f'times_{command}'] += 1
                        chatter_document.save()
                    await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} {adj} {target.user_name} {choice.format(chatter_username)}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command(f"{command} command", f)
                    return
            elif command_check.startswith("cutline") and read_bot_minigames():
                try:
                    if command_check.removeprefix("cutline").startswith("stat") and chatter_id == id_chodebot:
                        top_two_cut_by = []
                        top_two_cut_other = []
                        total_cut_by_points = 0.0
                        total_cut_other_points = 0.0
                        total_cut_by = 0
                        total_unique_cut_by = []
                        total_cut_other = 0
                        total_unique_cut_other = []
                        if len(chatter_document['data_games']['fish']['totals']['line']['cut_by']) > 0:
                            for key, value in chatter_document['data_games']['fish']['totals']['line']['cut_by'].items():
                                total_unique_cut_by.append([value[0], f"{key}/{numberize(value[0])}/{numberize(value[1])}"])
                                total_cut_by += value[0]
                                total_cut_by_points += value[1]
                        if len(chatter_document['data_games']['fish']['totals']['line']['cut_other']) > 0:
                            for key, value in chatter_document['data_games']['fish']['totals']['line']['cut_other'].items():
                                total_unique_cut_other.append([value[0], f"{key}/{numberize(value[0])}/{numberize(value[1])}"])
                                total_cut_other += value[0]
                                total_cut_other_points += value[1]

                        if len(total_unique_cut_by) > 0:
                            top_two_cut_by = sorted(total_unique_cut_by, key=lambda x: x[0], reverse=True)[:2]
                        if len(total_unique_cut_other) > 0:
                            top_two_cut_other = sorted(total_unique_cut_other, key=lambda x: x[0], reverse=True)[:2]
                        response_stats = f"YourLine Total/Unique/PointsLost(Negative=Good); {numberize(total_cut_by)}/{numberize(len(total_unique_cut_by))}/{numberize(total_cut_by_points)} | OtherLine Total/Unique/PointsLost(Positive=Good); {numberize(total_cut_other)}/{numberize(len(total_unique_cut_other))}/{numberize(total_cut_other_points)} | Top2Cut; {'None' if len(top_two_cut_by) == 0 else ' - '.join(top_two_cut_by[1])} | Top2From; {'None' if len(top_two_cut_other) == 0 else ' - '.join(top_two_cut_other[1])}"
                        await bot.send_chat_message(streamer.id, streamer.id, response_stats, reply_parent_message_id=data.event.message_id)
                        end_timer(f"cutline stats -- {response_stats}")
                        return
                    target = command_check.removeprefix("cutline").lower()
                    if target.startswith("@"):
                        target = target.removeprefix("@")
                    try:
                        target_document = Users.objects.get(name=target)
                    except Exception as g:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target} is not valid!!", reply_parent_message_id=data.event.message_id)
                        logger.error(f"{fortime()}: Error in cutline command -- {g}")
                        end_timer("cutline target failed")
                        return
                    if target_document['data_games']['fish']['line']['stats']['level'] > 1:
                        target_cutline_cost = fish_cut_cost * target_document['data_games']['fish']['line']['stats']['level']
                    else:
                        target_cutline_cost = fish_cut_cost
                    if chatter_document['data_user']['rank']['points'] < target_cutline_cost and chatter_id != id_streamer:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points for that! Need {target_cutline_cost} ({fish_cut_cost} x {target_document['name']}'s Lvl {target_document['data_games']['fish']['line']['stats']['level']}({target_document['data_games']['fish']['line']['stats']['name']}) Line), you have {numberize(chatter_document['data_user']['rank']['points'])}")
                        end_timer("cutline chatter not enough points")
                        return
                    elif target_document['data_games']['fish']['line']['cut_last'] is None: pass
                    elif await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(target_document['data_games']['fish']['line']['cut_last'])) < fish_cut_time and chatter_id != id_streamer:
                        wait_time = fish_cut_time - (await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(target_document['data_games']['fish']['line']['cut_last'])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line has been recently cut already. Gotta wait {datetime.timedelta(seconds=wait_time)}.", reply_parent_message_id=data.event.message_id)
                        end_timer("cutline target's line been cut recently")
                        return
                    elif target_document['data_games']['fish']['line']['cut']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line is already cut!!")
                        end_timer("cutline target's line been cut already")
                        return
                    if chatter_id != id_streamer:
                        chatter_document['data_user']['rank']['points'] -= target_cutline_cost
                    chatter_document.save()
                    chatter_document = await get_chatter_document(data)
                    target_document['data_games']['fish']['line']['cut'] = True
                    target_document['data_games']['fish']['line']['cut_by'] = chatter_username.lower()
                    target_document['data_games']['fish']['line']['cut_last'] = datetime.datetime.now()
                    target_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line has been cut successfully for {numberize(target_cutline_cost)}!! You now have {numberize(chatter_document['data_user']['rank']['points'])} points remaining", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("cutline command", f)
                    return
            elif command_check.startswith("fight") and read_bot_minigames():
                try:
                    if command.replace(" ", "").replace("fight", "").startswith("equipped"):
                        await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} you have {chatter_document['data_games']['fight']['weapon'][0]} worth {numberize(int(chatter_document['data_games']['fight']['weapon'][1]))} equipped as a weapon and {chatter_document['data_games']['fight']['shield'][0]} worth {numberize(int(chatter_document['data_games']['fight']['shield'][1]))} equipped as a shield.", reply_parent_message_id=data.event.message_id)
                        end_timer("fight command equipped")
                        return
                    elif command.replace(" ", "").replace("fight", "").startswith("stats"):
                        total_aggressor = numberize(chatter_document['data_games']['fight']['times_aggressor']['lost'] + chatter_document['data_games']['fight']['times_aggressor']['tied'] + chatter_document['data_games']['fight']['times_aggressor']['won'])
                        total_defender = numberize(chatter_document['data_games']['fight']['times_defender']['lost'] + chatter_document['data_games']['fight']['times_defender']['tied'] + chatter_document['data_games']['fight']['times_defender']['won'])
                        await bot.send_chat_message(streamer.id, streamer.id, f"Your stats are as follows; Aggressor Stats (Total/Won(Points)/Lost(Points)/Tied; {total_defender}/{numberize(chatter_document['data_games']['fight']['times_defender']['won'])}({numberize(chatter_document['data_games']['fight']['times_defender']['points_won'])})/{numberize(chatter_document['data_games']['fight']['times_defender']['lost'])}({numberize(chatter_document['data_games']['fight']['times_defender']['points_lost'])})/{chatter_document['data_games']['fight']['times_defender']['tied']} | Defender Stats (Total/Won(Points)/Lost(Points)/Tied; {total_aggressor}/{numberize(chatter_document['data_games']['fight']['times_defender']['won'])}({numberize(chatter_document['data_games']['fight']['times_defender']['points_won'])})/{numberize(chatter_document['data_games']['fight']['times_defender']['lost'])}({numberize(chatter_document['data_games']['fight']['times_defender']['points_lost'])})/{chatter_document['data_games']['fight']['times_defender']['tied']}")
                        end_timer("fight command stats")
                        return
                    elif command.replace(" ", "").replace("fight", "").startswith("@"):
                        target_user_name = command.replace(" ", "").replace("fight@", "")
                        target = await select_target(channel_document, chatter_id, True, target_user_name, "fight")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target_user_name} isn't a valid target!")
                            end_timer("fight command")
                            return
                    else:
                        target = await select_target(channel_document, chatter_id, game_type="fight")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"Couldn't locate a valid target!!", reply_parent_message_id=data.event.message_id)
                            end_timer("fight command")
                            return
                    target_document = await get_chatter_document(None, channel_document, target.user_id, target.user_name, target.user_login, id_streamer, name_streamer)
                    if target_document is None:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} something went wrong grabbing {target.user_name}'s document, try again later...")
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- fight command -- {target.user_name}'s target_document is None -- {chatter_username} has weapon")
                        end_timer("fight_fail")
                        return
                    fight_chance = random.randint(1, 3)
                    if fight_chance == 1:
                        chatter_document['data_games']['fight']['times_aggressor']['won'] += 1
                        target_document['data_games']['fight']['times_defender']['lost'] += 1
                        if chatter_document['data_games']['fight']['weapon'][0] is not None:
                            points_to_take = chatter_document['data_games']['fight']['weapon'][1]
                            if target_document['data_games']['fight']['shield'][0] is not None:
                                shield_name, shield_value = target_document['data_games']['fight']['shield'][0], target_document['data_games']['fight']['shield'][1]
                                points_to_take -= shield_value
                                if points_to_take < 0:
                                    points_to_take = 0
                                chatter_document['data_user']['rank']['points'] += points_to_take
                                chatter_document.save()
                                target_document['data_user']['rank']['points'] -= points_to_take
                                target_document['data_games']['fight']['shield'] = [None, 0]
                                target_document.save()
                                chatter_document = await refresh_chatter_document(data, None, None, None)
                                target_document = await refresh_chatter_document(None, target.user_id, target.user_name, target.user_login)
                                fight_response = f"and won! {target_document['name']} had {shield_name}({numberize(shield_value)}) as a shield!! {chatter_username} takes {numberize(points_to_take)} {bot_name} Points in their victory. {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points. {target_document['name']} you now have {numberize(target_document['data_user']['rank']['points'])} {bot_name} Points."
                            else:
                                chatter_document['data_user']['rank']['points'] += points_to_take
                                chatter_document.save()
                                target_document['data_user']['rank']['points'] -= points_to_take
                                target_document.save()
                                chatter_document = await refresh_chatter_document(data, None, None, None)
                                target_document = await refresh_chatter_document(None, target.user_id, target.user_name, target.user_login)
                                fight_response = f"and won! {chatter_username} takes {numberize(points_to_take)} {bot_name} Points in their victory. {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points. {target_document['name']} you now have {numberize(target_document['data_user']['rank']['points'])} {bot_name} Points."
                            chatter_document['data_games']['fight']['weapon'] = [None, 0]
                            chatter_document['data_games']['fight']['times_aggressor']['points_won'] += points_to_take
                            target_document['data_games']['fight']['times_defender']['points_lost'] += points_to_take
                        else:
                            fight_response = "and won"
                        chatter_document.save()
                        target_document.save()
                    elif fight_chance == 2:
                        chatter_document['data_games']['fight']['times_aggressor']['lost'] += 1
                        target_document['data_games']['fight']['times_defender']['won'] += 1
                        if target_document['data_games']['fight']['weapon'][0] is not None:
                            points_to_take = target_document['data_games']['fight']['weapon'][1]
                            if chatter_document['data_games']['fight']['shield'][0] is not None:
                                shield_name, shield_value = chatter_document['data_games']['fight']['shield'][0], chatter_document['data_games']['fight']['shield'][1]
                                points_to_take -= shield_value
                                if points_to_take < 0:
                                    points_to_take = 0
                                target_document['data_user']['rank']['points'] += points_to_take
                                target_document.save()
                                chatter_document['data_user']['rank']['points'] -= points_to_take
                                chatter_document['data_games']['fight']['shield'] = [None, 0]
                                chatter_document.save()
                                chatter_document = await refresh_chatter_document(data, None, None, None)
                                target_document = await refresh_chatter_document(None, target.user_id, target.user_name, target.user_login)
                                fight_response = f"and lost! {chatter_username} had {shield_name}({numberize(shield_value)}) as a shield!! {chatter_username} looses {numberize(points_to_take)} {bot_name} Points in their defeat. {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points. {target_document['name']} you now have {numberize(target_document['data_user']['rank']['points'])} {bot_name} Points."
                            else:
                                target_document['data_user']['rank']['points'] += points_to_take
                                target_document.save()
                                chatter_document['data_user']['rank']['points'] -= points_to_take
                                chatter_document.save()
                                chatter_document = await refresh_chatter_document(data, None, None, None)
                                target_document = await refresh_chatter_document(None, target.user_id, target.user_name, target.user_login)
                                fight_response = f"and lost! {chatter_username} looses {numberize(points_to_take)} {bot_name} Points in their defeat. {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points. {target_document['name']} you now have {numberize(target_document['data_user']['rank']['points'])} {bot_name} Points."
                            chatter_document['data_games']['fight']['times_aggressor']['points_lost'] += points_to_take
                            target_document['data_games']['fight']['times_defender']['points_won'] += points_to_take
                            target_document['data_games']['fight']['weapon'] = [None, 0]
                        else:
                            fight_response = "and lost"
                        chatter_document.save()
                        target_document.save()
                    else:
                        chatter_document['data_games']['fight']['times_aggressor']['tied'] += 1
                        chatter_document.save()
                        target_document['data_games']['fight']['times_defender']['tied'] += 1
                        target_document.save()
                        fight_response = "and tied"
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} challenged {target.user_name} to a fight {fight_response}!")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("fight command", f)
                    return
            elif command_check.startswith("fish") and read_bot_minigames():  # and chatter_id == streamer.id:  # Moist Dude's Line
                target_id, target_name, target_login = None, None, None
                initial_auto, final_auto, total_rewards = False, False, []
                fish_start, fish_limit = 5, 90
                response_auto_whisper = ""
                fish_auto_cast_speed = 0.0
                try:
                    if command_check.removeprefix("fish").startswith("stat"):
                        auto_total_cost = chatter_document['data_games']['fish']['auto']['cost'] + chatter_document['data_games']['fish']['totals']['auto']['cost']
                        line_level = chatter_document['data_games']['fish']['line']['stats']['level']
                        lure_level = chatter_document['data_games']['fish']['lure']['level']
                        reel_level = chatter_document['data_games']['fish']['reel']['level']
                        rod_level = chatter_document['data_games']['fish']['rod']['level']
                        total_points_auto_add, total_points_auto_loss = 0.0, 0.0
                        total_points_man_add, total_points_man_loss = 0.0, 0.0
                        total_cast_auto, total_cast_manual = 0, 0
                        line_cut, line_cut_total_lost, lines_cut, lines_cut_total_lost = 0, 0.0, 0, 0.0
                        total_unique_auto = {}
                        total_unique_man = {}
                        if len(chatter_document['data_games']['fish']['auto']['catches']) > 0:
                            for key, value in chatter_document['data_games']['fish']['auto']['catches'].items():
                                total_cast_auto += value[0]
                                if value[1] >= 0:
                                    total_points_auto_add += value[1]
                                else:
                                    total_points_auto_loss += value[1]
                                if key not in total_unique_auto:
                                    total_unique_auto[key] = 1
                                else:
                                    total_unique_auto[key] += 1
                        if len(chatter_document['data_games']['fish']['totals']['auto']['catches']) > 0:
                            for key, value in chatter_document['data_games']['fish']['totals']['auto']['catches'].items():
                                total_cast_auto += value[0]
                                if value[1] >= 0:
                                    total_points_auto_add += value[1]
                                else:
                                    total_points_auto_loss += value[1]
                                if key not in total_unique_auto:
                                    total_unique_auto[key] = 1
                                else:
                                    total_unique_auto[key] += 1
                        if len(chatter_document['data_games']['fish']['totals']['manual']['catches']) > 0:
                            for key, value in chatter_document['data_games']['fish']['totals']['manual']['catches'].items():
                                total_cast_manual += value[0]
                                if value[1] >= 0:
                                    total_points_man_add += value[1]
                                else:
                                    total_points_man_loss += value[1]
                                if key not in total_unique_man:
                                    total_unique_man[key] = 1
                                else:
                                    total_unique_man[key] += 1
                        if len(chatter_document['data_games']['fish']['totals']['line']['cut_by']) > 0:
                            for key, value in chatter_document['data_games']['fish']['totals']['line']['cut_by'].items():
                                for key2, value2 in chatter_document['data_games']['fish']['totals']['line']['cut_by'][key].items():
                                    line_cut += value2[0]
                                    line_cut_total_lost += value2[1]
                        if len(chatter_document['data_games']['fish']['totals']['line']['cut_other']) > 0:
                            for key, value in chatter_document['data_games']['fish']['totals']['line']['cut_other'].items():
                                for key2, value2 in chatter_document['data_games']['fish']['totals']['line']['cut_other'][key].items():
                                    lines_cut += value2[0]
                                    lines_cut_total_lost += value2[1]
                        response_stats = f"Casts (Total/Auto/Manual); {numberize(total_cast_auto + total_cast_manual)}/{numberize(total_cast_auto)}/{numberize(total_cast_manual)} | Auto UniqueCatches/Gain/Loss/Cost; {numberize(len(total_unique_auto))}/{numberize(total_points_auto_add)}/{numberize(total_points_auto_loss)}/{numberize(auto_total_cost)} | Manual UniqueCatches/Gain/Loss {numberize(len(total_unique_man))}/{numberize(total_points_man_add)}/{numberize(total_points_man_loss)} | Line/Lure/Reel/Rod Level(NextUpgradeCost); {line_level}({'Max' if line_level == max(lines.keys()) else numberize(lines[line_level + 1]['cost'])})/{lure_level}({'Max' if lure_level == max(lures.keys()) else numberize(lines[lure_level + 1]['cost'])})/{reel_level}({'Max' if reel_level == max(reels.keys()) else numberize(reels[reel_level + 1]['cost'])})/{rod_level}({'Max' if rod_level == max(rods.keys()) else numberize(rods[rod_level + 1]['cost'])}) | TimesOwnLineCut(PointsLost)/TimesCutOtherLines(PointsLost); {numberize(line_cut)}({numberize(line_cut_total_lost)})/{numberize(lines_cut)}({numberize(lines_cut_total_lost)}) | BucketsIce/BottlesLube; {numberize(chatter_document['data_games']['fish']['special']['ice'])}/{numberize(chatter_document['data_games']['fish']['special']['lube'])}"
                        await bot.send_chat_message(streamer.id, streamer.id, response_stats, reply_parent_message_id=data.event.message_id)
                        end_timer(f"fish stats for {chatter_username} -- {response_stats}")
                        return
                    elif command_check.removeprefix("fish").startswith("upgrade"):
                        fish_upgrade_success = None
                        fish_upgrade_options = ("line", "lure", "reel", "rod")
                        if command_check.removeprefix("fishupgrade").startswith("line"):
                            if chatter_document['data_games']['fish']['line']['stats']['level'] == max(lines.keys()):
                                fish_upgrade_success = "Max Level Already"
                                response_fish_upgrade = f"{chatter_username} you're already at thee max line level; {chatter_document['data_games']['fish']['line']['stats']['name']}({chatter_document['data_games']['fish']['line']['stats']['level']})!!"
                            elif chatter_document['data_user']['rank']['points'] < lines[chatter_document['data_games']['fish']['line']['stats']['level'] + 1]['cost']:
                                fish_upgrade_success = "Not Enuff Points"
                                response_fish_upgrade = f"{chatter_username} you don't have enough points to upgrade your line to {lines[chatter_document['data_games']['fish']['line']['stats']['level'] + 1]['name']}({chatter_document['data_games']['fish']['line']['stats']['level'] + 1}) tier, need {numberize(lines[chatter_document['data_games']['fish']['line']['stats']['level'] + 1]['cost'])} {bot_name} Points, but you only have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!!"
                            else:
                                chatter_document['data_user']['rank']['points'] -= lines[chatter_document['data_games']['fish']['line']['stats']['level'] + 1]['cost']
                                chatter_document['data_games']['fish']['line']['stats'] = lines[chatter_document['data_games']['fish']['line']['stats']['level'] + 1]
                                chatter_document.save()
                                chatter_document = await get_chatter_document(data)
                                fish_upgrade_success = f"Upgraded Line from {lines[chatter_document['data_games']['fish']['line']['stats']['level'] - 1]['name']}({chatter_document['data_games']['fish']['line']['stats']['level'] - 1}) to {chatter_document['data_games']['fish']['line']['stats']['name']}({chatter_document['data_games']['fish']['line']['stats']['level']}) for {numberize(chatter_document['data_games']['fish']['line']['stats']['cost'])}"
                                response_fish_upgrade = f"{chatter_username} you have successfully upgraded your line from {lines[chatter_document['data_games']['fish']['line']['stats']['level'] - 1]['name']}({chatter_document['data_games']['fish']['line']['stats']['level'] - 1}) to {chatter_document['data_games']['fish']['line']['stats']['name']}({chatter_document['data_games']['fish']['line']['stats']['level']}) for {numberize(chatter_document['data_games']['fish']['line']['stats']['cost'])} {bot_name} Points!! You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points Remaining."
                        elif command_check.removeprefix("fishupgrade").startswith("lure"):
                            if chatter_document['data_games']['fish']['lure']['level'] == max(lures.keys()):
                                fish_upgrade_success = "Max Level Already"
                                response_fish_upgrade = f"{chatter_username} you're already at thee max lure level; {chatter_document['data_games']['fish']['lure']['name']}({chatter_document['data_games']['fish']['lure']['level']})!!"
                            elif chatter_document['data_user']['rank']['points'] < lures[chatter_document['data_games']['fish']['lure']['level'] + 1]['cost']:
                                fish_upgrade_success = "Not Enuff Points"
                                response_fish_upgrade = f"{chatter_username} you don't have enough points to upgrade your lure to {lures[chatter_document['data_games']['fish']['lure']['level'] + 1]['name']}({chatter_document['data_games']['fish']['lure']['level'] + 1}) tier, need {numberize(lures[chatter_document['data_games']['fish']['lure']['level'] + 1]['cost'])} {bot_name} Points, but you only have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!!"
                            else:
                                chatter_document['data_user']['rank']['points'] -= lures[chatter_document['data_games']['fish']['lure']['level'] + 1]['cost']
                                chatter_document['data_games']['fish']['lure'] = lures[chatter_document['data_games']['fish']['lure']['level'] + 1]
                                chatter_document.save()
                                chatter_document = await get_chatter_document(data)
                                fish_upgrade_success = f"Upgraded Lure from {lures[chatter_document['data_games']['fish']['lure']['level'] - 1]['name']}({chatter_document['data_games']['fish']['lure']['level'] - 1}) to {chatter_document['data_games']['fish']['lure']['name']}({chatter_document['data_games']['fish']['lure']['level']}) for {numberize(chatter_document['data_games']['fish']['lure']['cost'])}"
                                response_fish_upgrade = f"{chatter_username} you have successfully upgraded your lure from {lures[chatter_document['data_games']['fish']['lure']['level'] - 1]['name']}({chatter_document['data_games']['fish']['lure']['level'] - 1}) to {chatter_document['data_games']['fish']['lure']['name']}({chatter_document['data_games']['fish']['lure']['level']}) for {numberize(chatter_document['data_games']['fish']['lure']['cost'])} {bot_name} Points!! You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points Remaining."
                        elif command_check.removeprefix("fishupgrade").startswith("reel"):
                            if chatter_document['data_games']['fish']['reel']['level'] == max(reels.keys()):
                                fish_upgrade_success = "Max Level Already"
                                response_fish_upgrade = f"{chatter_username} you're already at thee max reel level; {chatter_document['data_games']['fish']['reel']['name']}({chatter_document['data_games']['fish']['reel']['level']})!!"
                            elif chatter_document['data_user']['rank']['points'] < reels[chatter_document['data_games']['fish']['reel']['level'] + 1]['cost']:
                                fish_upgrade_success = "Not Enuff Points"
                                response_fish_upgrade = f"{chatter_username} you don't have enough points to upgrade your reel to {reels[chatter_document['data_games']['fish']['reel']['level'] + 1]['name']}({chatter_document['data_games']['fish']['reel']['level'] + 1}) tier, need {numberize(reels[chatter_document['data_games']['fish']['reel']['level'] + 1]['cost'])} {bot_name} Points, but you only have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!!"
                            else:
                                chatter_document['data_user']['rank']['points'] -= reels[chatter_document['data_games']['fish']['reel']['level'] + 1]['cost']
                                chatter_document['data_games']['fish']['reel'] = reels[chatter_document['data_games']['fish']['reel']['level'] + 1]
                                chatter_document.save()
                                chatter_document = await get_chatter_document(data)
                                fish_upgrade_success = f"Upgraded Lure from {reels[chatter_document['data_games']['fish']['reel']['level'] - 1]['name']}({chatter_document['data_games']['fish']['reel']['level'] - 1}) to {chatter_document['data_games']['fish']['reel']['name']}({chatter_document['data_games']['fish']['reel']['level']}) for {numberize(chatter_document['data_games']['fish']['reel']['cost'])}"
                                response_fish_upgrade = f"{chatter_username} you have successfully upgraded your reel from {reels[chatter_document['data_games']['fish']['reel']['level'] - 1]['name']}({chatter_document['data_games']['fish']['reel']['level'] - 1}) to {chatter_document['data_games']['fish']['reel']['name']}({chatter_document['data_games']['fish']['reel']['level']}) for {numberize(chatter_document['data_games']['fish']['reel']['cost'])} {bot_name} Points!! You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points Remaining."
                        elif command_check.removeprefix("fishupgrade").startswith("rod"):
                            if chatter_document['data_games']['fish']['rod']['level'] == max(rods.keys()):
                                fish_upgrade_success = "Max Level Already"
                                response_fish_upgrade = f"{chatter_username} you're already at thee max rod level; {chatter_document['data_games']['fish']['rod']['name']}({chatter_document['data_games']['fish']['rod']['level']})!!"
                            elif chatter_document['data_user']['rank']['points'] < rods[chatter_document['data_games']['fish']['rod']['level'] + 1]['cost']:
                                fish_upgrade_success = "Not Enuff Points"
                                response_fish_upgrade = f"{chatter_username} you don't have enough points to upgrade your rod to {rods[chatter_document['data_games']['fish']['rod']['level'] + 1]['name']}({chatter_document['data_games']['fish']['rod']['level'] + 1}) tier, need {numberize(rods[chatter_document['data_games']['fish']['rod']['level'] + 1]['cost'])} {bot_name} Points, but you only have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!!"
                            else:
                                chatter_document['data_user']['rank']['points'] -= rods[chatter_document['data_games']['fish']['rod']['level'] + 1]['cost']
                                chatter_document['data_games']['fish']['rod'] = rods[chatter_document['data_games']['fish']['rod']['level'] + 1]
                                chatter_document.save()
                                chatter_document = await get_chatter_document(data)
                                fish_upgrade_success = f"Upgraded Lure from {rods[chatter_document['data_games']['fish']['rod']['level'] - 1]['name']}({chatter_document['data_games']['fish']['rod']['level'] - 1}) to {chatter_document['data_games']['fish']['rod']['name']}({chatter_document['data_games']['fish']['rod']['level']}) for {numberize(chatter_document['data_games']['fish']['rod']['cost'])}"
                                response_fish_upgrade = f"{chatter_username} you have successfully upgraded your rod from {rods[chatter_document['data_games']['fish']['rod']['level'] - 1]['name']}({chatter_document['data_games']['fish']['rod']['level'] - 1}) to {chatter_document['data_games']['fish']['rod']['name']}({chatter_document['data_games']['fish']['rod']['level']}) for {numberize(chatter_document['data_games']['fish']['rod']['cost'])} {bot_name} Points!! You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points Remaining."
                        else:
                            response_fish_upgrade = f"{chatter_username} your command wasn't registered. Possible options after !fish upgrade are; {' | '.join(fish_upgrade_options)}"
                        await bot.send_chat_message(id_streamer, id_streamer, response_fish_upgrade, reply_parent_message_id=data.event.message_id)
                        end_timer(f"{command_check} {fish_upgrade_success}")
                        return
                    elif command_check.removeprefix("fish").isdigit():
                        if chatter_document['data_games']['fish']['auto']['cast'] != 0:
                            cap_reached = False
                            auto_casts = int(command_check.removeprefix("fish"))
                            new_casts = chatter_document['data_games']['fish']['auto']['cast'] + auto_casts
                            if new_casts > 100:
                                cap_reached = True
                                new_casts = 100
                            difference_casts = abs(new_casts - chatter_document['data_games']['fish']['auto']['cast'])
                            new_cost = difference_casts * (fish_auto_cost + chatter_document['data_games']['fish']['rod']['level'])
                            if new_cost > chatter_document['data_user']['rank']['points']:
                                await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points for {new_casts} to be set, need {int(new_cost):,} {bot_name} Points, you have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points.", reply_parent_message_id=data.event.message_id)
                                end_timer("fish_auto_cast_not_points")
                                return
                            chatter_document['data_user']['rank']['points'] -= new_cost
                            chatter_document['data_games']['fish']['auto']['cast'] = new_casts
                            chatter_document['data_games']['fish']['auto']['cost'] += new_cost
                            chatter_document.save()
                            chatter_document = await get_chatter_document(data)
                            if cap_reached:
                                response_fish_auto_cast = f"You cannot set above 100 AutoCasts, added {difference_casts} for {numberize(new_cost)} {bot_name} Points. You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points & {chatter_document['data_games']['fish']['auto']['cast']} AutoCast's."
                            else:
                                response_fish_auto_cast = f"You have added {difference_casts} to your AutoCasts for {numberize(new_cost)} {bot_name} Points. You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points & {chatter_document['data_games']['fish']['auto']['cast']} AutoCast's."
                            if not chatter_document['data_games']['fish']['line']['cast']:
                                initial_auto = True
                                response_fish_auto_cast += f" | Detected you're not currently casting.. Attempting to restart"
                            await bot.send_chat_message(id_streamer, id_streamer, response_fish_auto_cast, reply_parent_message_id=data.event.message_id)
                            if not initial_auto:
                                end_timer("fish add auto fishing command")
                                return
                        else:
                            cap_reached = False
                            auto_casts = int(command_check.removeprefix("fish"))
                            if auto_casts > 100:
                                cap_reached = True
                                auto_casts = 100
                            new_cost = auto_casts * (fish_auto_cost + chatter_document['data_games']['fish']['rod']['level'])
                            if chatter_document['data_user']['rank']['points'] < new_cost:
                                await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points for that. Need {numberize(new_cost)} and you have {numberize(chatter_document['data_user']['rank']['points'])}", reply_parent_message_id=data.event.message_id)
                                end_timer("fish auto cast not enuff points")
                                return
                            initial_auto = True
                            chatter_document['data_games']['fish']['auto']['cast'] = auto_casts
                            chatter_document['data_games']['fish']['auto']['cost'] = new_cost
                            chatter_document['data_user']['rank']['points'] -= new_cost
                            chatter_document.save()
                            chatter_document = await get_chatter_document(data)
                            if cap_reached:
                                response_fish_auto_cast = f"You cannot set above 100 AutoCasts, set {auto_casts} for {numberize(new_cost)} {bot_name} Points. You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points & {chatter_document['data_games']['fish']['auto']['cast']} AutoCast's."
                            else:
                                response_fish_auto_cast = f"You have set {auto_casts} AutoCasts for {numberize(new_cost)} {bot_name} Points. You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points & {chatter_document['data_games']['fish']['auto']['cast']} AutoCast's."
                            await bot.send_chat_message(id_streamer, id_streamer, response_fish_auto_cast, reply_parent_message_id=data.event.message_id)
                            if chatter_document['data_games']['fish']['line']['cast']:
                                end_timer("fish autocast set--cast already")
                                return
                    elif chatter_id == id_streamer and command_check.removeprefix("fish") != "":
                        target = command_check.removeprefix("fish")
                        if target.startswith("@"):
                            target = target.removeprefix("@")
                        if "|" in target:
                            target_fisher, _ = target.split("|", maxsplit=1)
                        else:
                            target_fisher = target
                        try:
                            chatter_document = Users.objects.get(name=target_fisher)
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in fish command -- document swap -- {target_fisher} -- {g}")
                            end_timer("fish doc swap command")
                            return
                        if chatter_document['data_games']['fish']['auto']['cast'] > 0:
                            fish_auto_cast_speed = (chatter_document['data_games']['fish']['lure']['effect'] / 4) + (chatter_document['data_games']['fish']['rod']['effect'] / 4) + (chatter_document['data_games']['fish']['line']['stats']['effect'] / 8) + chatter_document['data_games']['fish']['reel']['effect']
                            fish_start = max(90 - fish_auto_cast_speed, fish_start)
                            fish_limit = max(300 - fish_auto_cast_speed, fish_limit)
                        target_id, target_name, target_login = chatter_document['_id'], chatter_document['name'], chatter_document['data_user']['login']
                        if chatter_document['data_games']['jail']['in']:
                            fish_wait_time = abs(jail_time - (await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last']))))
                            await asyncio.sleep(fish_wait_time)
                            chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                            chatter_document['data_games']['jail']['in'] = False
                            chatter_document['data_games']['jail']['last'] = datetime.datetime.now()
                            chatter_document.save()
                            chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                            if chatter_document['_id'] in channel_document['data_lists']['mods']:
                                await bot.add_channel_moderator(id_streamer, chatter_document['_id'])
                        elif chatter_document['data_games']['fish']['line']['cast']:
                            logger.error(f"{fortime()}: Fish Error; {chatter_document['name']} is already casting!!! Something happened.. Two Instances??")
                            end_timer("fish-already-cast-auto-detected")
                            return
                    elif chatter_document['data_games']['fish']['line']['cast']:  # and not command_check.removeprefix("fish").isdigit():
                        auto_response = ""
                        if chatter_document['data_games']['fish']['auto']['cast'] != 0:
                            auto_response = f" You have {chatter_document['data_games']['fish']['auto']['cast']:,} auto casts remaining."
                        await bot.send_chat_message(id_streamer, id_streamer, f"You have already cast your line, wait a few.{auto_response}", reply_parent_message_id=data.event.message_id)
                        end_timer("fish game already fishing")
                        return
                    chatter_document['data_games']['fish']['line']['cast'] = True
                    chatter_document.save()
                    fish_cast_time = random.uniform(fish_start, fish_limit)
                    await asyncio.sleep(fish_cast_time)
                    chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    fish_list = [[], []]
                    fish_list_changed = []
                    fish_prob_cap = [chatter_document['data_games']['fish']['lure']['pLow'], chatter_document['data_games']['fish']['lure']['pHigh']]
                    with open("data/bot/fish_rewards", "r") as file:
                        fish_raw = file.read().splitlines()
                    for item in fish_raw:
                        prob = 100.00
                        fish_name, fish_value = item.split(", ", maxsplit=2)
                        fish_value = float(fish_value)
                        prob -= (abs(float(f'{fish_value:.2f}')) / len(str(abs(float(f'{fish_value:.2f}'))))) / 50
                        old_prob = prob
                        if chatter_document['data_games']['fish']['lure']['level'] > 0 and fish_prob_cap[0] <= prob < fish_prob_cap[1]:
                            prob += chatter_document['data_games']['fish']['lure']['effect']
                            fish_list_changed.append([fish_name, fish_value, prob, old_prob])
                        elif chatter_document['data_games']['fish']['lure']['level'] > 0 and prob > fish_prob_cap[1]:
                            prob -= chatter_document['data_games']['fish']['lure']['effect'] / 2
                            fish_list_changed.append([fish_name, fish_value, prob, old_prob])
                        if prob < 0:
                            while len(f'{int(abs(prob))}') > 1:
                                prob /= 10
                            prob = abs(prob)
                        fish_list[0].append([fish_name, fish_value, prob, old_prob])
                        fish_list[1].append(prob)
                    choice = random.choices(fish_list[0], fish_list[1])[0]
                    fish_logger.info(f"{fortime()}: oP;{choice[3]:.7f}: nP;{choice[2]:.7f}: nA;{chatter_document['name']}: vA;{numberize(choice[1])}: iT;{choice[0]}: lR;{chatter_document['data_games']['fish']['lure']['level']}/{chatter_document['data_games']['fish']['lure']['effect']}/{chatter_document['data_games']['fish']['lure']['pLow']}/{chatter_document['data_games']['fish']['lure']['pHigh']}: lI;{chatter_document['data_games']['fish']['line']['stats']['level']}/{chatter_document['data_games']['fish']['line']['stats']['effect']}: rE;{chatter_document['data_games']['fish']['reel']['level']}/{chatter_document['data_games']['fish']['reel']['effect']}: rO;{chatter_document['data_games']['fish']['rod']['level']}/{chatter_document['data_games']['fish']['rod']['effect']}: fC;{len(fish_list_changed)}: tMn;{fish_start:.2f}: tMx;{fish_limit:.2f}: tCn;{fish_auto_cast_speed:.2f}: tT;{fish_cast_time:.2f}")
                    fish = choice[0]
                    catch = fish
                    value = choice[1]
                    raw_value = value
                    if fish == "a hype-train":
                        value *= channel_document['data_channel']['hype_train']['record_level']
                        raw_value = value
                    fish_response = f"caught {fish} worth {numberize(raw_value)} point{'s' if raw_value != 1 else ''}"
                    line_cut = False
                    if chatter_document['data_games']['fish']['line']['cut']:
                        line_cut = True
                        catch = "CutLine"
                        old_fish = fish
                        name_cut_by = chatter_document['data_games']['fish']['line']['cut_by']
                        fish = f"line was cut by {name_cut_by} loosing {old_fish} worth {numberize(value)}"
                        fish_response = f"line was cut by {name_cut_by} loosing {old_fish} worth {numberize(value)}"
                        try:
                            target_document = Users.objects.get(name=name_cut_by)
                            if target_document is not None:
                                if chatter_document['name'] not in target_document['data_games']['fish']['totals']['line']['cut_other']:
                                    target_document['data_games']['fish']['totals']['line']['cut_other'][chatter_document['name']] = {old_fish: [1, raw_value]}
                                else:
                                    if old_fish not in target_document['data_games']['fish']['totals']['line']['cut_other'][chatter_document['name']]:
                                        target_document['data_games']['fish']['totals']['line']['cut_other'][chatter_document['name']][old_fish] = [1, raw_value]
                                    else:
                                        target_document['data_games']['fish']['totals']['line']['cut_other'][chatter_document['name']][old_fish][0] += 1
                                        target_document['data_games']['fish']['totals']['line']['cut_other'][chatter_document['name']][old_fish][1] += raw_value
                                target_document.save()
                            else:
                                logger.error(f"{fortime()}: {name_cut_by}'s document NOT FOUND during {chatter_document['name']}'s line_was_cut bit...")
                        except Exception as fuckingfish:
                            logger.error(f"{fortime()}: Error fetching/modifying {name_cut_by}'s document -- {fuckingfish}")
                            pass
                        if name_cut_by not in chatter_document['data_games']['fish']['totals']['line']['cut_by']:
                            chatter_document['data_games']['fish']['totals']['line']['cut_by'][name_cut_by] = {old_fish: [1, raw_value]}
                        else:
                            if old_fish not in chatter_document['data_games']['fish']['totals']['line']['cut_by'][name_cut_by]:
                                chatter_document['data_games']['fish']['totals']['line']['cut_by'][name_cut_by][old_fish] = [1, raw_value]
                            else:
                                chatter_document['data_games']['fish']['totals']['line']['cut_by'][name_cut_by][old_fish][0] += 1
                                chatter_document['data_games']['fish']['totals']['line']['cut_by'][name_cut_by][old_fish][1] += raw_value
                        chatter_document['data_games']['fish']['line']['cut'] = False
                        chatter_document['data_games']['fish']['line']['cut_by'] = ""
                        chatter_document.save()
                        chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                        fish_logger.info(f"{fortime()}: {chatter_document['name']}'s {fish}")
                        if raw_value > 0:
                            channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                            channel_document['data_games']['gamble']['total'] += raw_value
                            channel_document.save()
                        value, raw_value = 0, 0
                    chatter_document['data_games']['fish']['line']['caught_last'] = [fish, str(raw_value)]
                    fish_jail_reason = ""
                    response_freepack = ""
                    response_time_add = ""
                    if not line_cut and fish == "a Free2Escape Jail Card":
                        if chatter_document['data_games']['jail']['escapes'] == 0:
                            fish_response += f" | You keep it not gaining any points"
                            value, raw_value = 0, 0
                            chatter_document['data_games']['jail']['escapes'] += 1
                        else:
                            fish_response += f" | You already have one saved"
                    elif not line_cut and fish == "a Go Directly To Jail Card":
                        chatter_document['data_games']['jail']['in'] = True
                        chatter_document['data_games']['jail']['last'] = datetime.datetime.now()
                        chatter_document['data_games']['jail']['history']['fished'] += 1
                        chatter_document.save()
                        fish_jail_reason = f"{chatter_document['name']} was sent 'Directly To Jail, Didn't Pass Go, Didn't Collect 200 {bot_name} Points' for {str(datetime.timedelta(seconds=jail_time)).title()} from their fishing catch"
                        special_logger.info(f"{fortime()}: {fish_jail_reason}")
                        fish_logger.info(f"{fortime()}: {fish_jail_reason}")
                        await bot.ban_user(id_streamer, id_streamer, chatter_document['_id'], fish_jail_reason, jail_time)
                    # elif not line_cut and fish == "a UNO Reverse Card":  # ToDo: Add This Logic, to idk, fight game? Or any point loss from another player/linecut?? 10% chance to use on jail attempt/5% on fail attempt?? IDK, think it out
                    #     pass
                    elif not line_cut and fish == "a time token" and channel_document['data_channel']['writing_clock']:
                        if channel_document['data_channel']['hype_train']['current']:
                            value = check_hype_train(channel_document, value)
                        seconds, time_not = write_clock(value, logger, True, obs)
                        chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, seconds)
                        response_time_add = f"{chatter_document['name']} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'}{f' {response_level}' if response_level is not None else ''}"
                        special_logger.info(f"{response_time_add} @ {fortime()}")
                        fish_logger.info(f"{fortime()}: {response_time_add}")
                        value, raw_value = 0, 0
                        fish_response += f" | You exchange it for {str(datetime.timedelta(seconds=seconds)).title()} on thee clock"
                    elif not line_cut and fish == "a FreePack Redemption":
                        if channel_document['data_channel']['writing_clock']:
                            fish_response += f" | You trade it in for a free coupon code"
                            value, raw_value = 0, 0
                            if len(channel_document['data_lists']['coupons']) > 0:
                                coupon_code = channel_document['data_lists']['coupons'].pop(0)
                                channel_document.save()
                                channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                                chatter_document['data_user']['dates']['daily_cards'][2].append(coupon_code)
                                response_freepack = f"Hey {chatter_document['name']}, you fished a FreePack via !fish command!! Here is your single use coupon code; {link_loots_coupon_blank}{coupon_code}"
                                fish_logger.info(f"{fortime()}: {chatter_document['name']} redeemed FISHING_FREEPACK {bot_name} Points for 1 Pack -- {coupon_code} -- # coupons left on channel_document; {len(channel_document['data_lists']['coupons'])}")
                            else:
                                chatter_document['data_user']['dates']['daily_cards'][0] += 1
                                response_freepack = f"Hey {chatter_document['name']}, I ran outta coupon codes for your fishing FreePack!!!! {name_streamer} will get to it manually later on, remind him next time you see him, eh?"
                                logger_msg = f"{fortime()}: {chatter_document['name']} attempted an FISHING_FREEPACK AUTO REDEEM FREE PACK, but NO COUPON CODES AVAILABLE!!!"
                                logger.warn(logger_msg)
                                fish_logger.warn(logger_msg)
                        else:
                            fish_response += f" | You keep it for points"
                    elif not line_cut and fish in weapon_tuple:
                        if chatter_document['data_games']['fight']['weapon'][0] is None:
                            chatter_document['data_games']['fight']['weapon'] = [fish, value]
                            fish_response += " | You keep it as a weapon gaining no points"
                            value, raw_value = 0, 0
                        else:
                            if value > chatter_document['data_games']['fight']['weapon'][1]:
                                old_item = chatter_document['data_games']['fight']['weapon']
                                chatter_document['data_games']['fight']['weapon'] = [fish, value]
                                chatter_document['data_user']['rank']['points'] += old_item[1]
                                fish_response += f" | You keep it as a weapon replacing {old_item[0]}({numberize(old_item[1])}), gaining the old item's value"
                                value, raw_value = 0, 0
                            else:
                                fish_response += f" | You already have {chatter_document['data_games']['fight']['weapon'][0]}({numberize(chatter_document['data_games']['fight']['weapon'][1])}) equipped as a weapon"
                    elif not line_cut and fish in shield_tuple:
                        if chatter_document['data_games']['fight']['shield'][0] is None:
                            chatter_document['data_games']['fight']['shield'] = [fish, value]
                            fish_response += " | You keep it as a shield gaining no points"
                            value, raw_value = 0, 0
                        else:
                            if value > chatter_document['data_games']['fight']['shield'][1]:
                                old_item = chatter_document['data_games']['fight']['shield']
                                chatter_document['data_games']['fight']['shield'] = [fish, value]
                                chatter_document['data_user']['rank']['points'] += old_item[1]
                                fish_response += f" | You keep it as a shield replacing {old_item[0]}({numberize(old_item[1])}), gaining the old item's value"
                                value, raw_value = 0, 0
                            else:
                                fish_response += f" | You already have {chatter_document['data_games']['fight']['shield'][0]}({numberize(chatter_document['data_games']['fight']['shield'][1])}) equipped as a shield"
                    elif not line_cut and fish in fish_special_items:
                        if fish == "some ice for thee timer":
                            chatter_document['data_games']['fish']['special']['ice'] += 1
                            fish_response += f" | You keep thee ice, now have {numberize(chatter_document['data_games']['fish']['special']['ice'])} buckets of ice"
                            value, raw_value = 0, 0
                        elif fish == "some lube for thee timer":
                            chatter_document['data_games']['fish']['special']['lube'] += 1
                            fish_response += f" | You keep thee lube, now have {numberize(chatter_document['data_games']['fish']['special']['lube'])} bottles of lube"
                            value, raw_value = 0, 0
                    elif not line_cut and fish in angry_items:
                        target = await select_target(channel_document, chatter_document['_id'], game_type="fight")
                        if target is None:
                            fish_response += f" | {fish} attempted to fight someone in chat, however couldn't find a target!! Gained normal points"
                        else:
                            try:
                                target_document = Users.objects.get(_id=target.user_id)
                                target_document['data_user']['rank']['points'] -= raw_value
                                target_document['data_games']['fight']['times_defender']['lost'] += 1
                                target_document['data_games']['fight']['times_defender']['points_lost'] += raw_value
                                target_document.save()
                                chatter_document['data_user']['rank']['points'] += raw_value
                                chatter_document['data_games']['fight']['times_aggressor']['won'] += 1
                                chatter_document['data_games']['fight']['times_aggressor']['points_won'] += raw_value
                                chatter_document.save()
                                fish_response += f" | {fish} fights {target.user_name} on your behalf, you gained {numberize(raw_value)} from them!!"
                                value, raw_value = 0, 0
                            except FileNotFoundError:
                                fish_response += f" | {fish} attempted to fight {target.user_name} but I couldn't load their document.. Gained normal points"
                                pass
                    if chatter_document['data_games']['fish']['auto']['cast'] > 0 and not initial_auto:
                        if catch not in chatter_document['data_games']['fish']['auto']['catches']:
                            chatter_document['data_games']['fish']['auto']['catches'][catch] = [1, raw_value]
                        else:
                            chatter_document['data_games']['fish']['auto']['catches'][catch][0] += 1
                            chatter_document['data_games']['fish']['auto']['catches'][catch][1] += raw_value
                    else:
                        if catch not in chatter_document['data_games']['fish']['totals']['manual']['catches']:
                            chatter_document['data_games']['fish']['totals']['manual']['catches'][catch] = [1, raw_value]
                        else:
                            chatter_document['data_games']['fish']['totals']['manual']['catches'][catch][0] += 1
                            chatter_document['data_games']['fish']['totals']['manual']['catches'][catch][1] += raw_value
                    if value < 0:
                        value = abs(value)
                        add = False
                        channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                        channel_document['data_games']['gamble']['total'] += value
                        channel_document.save()
                    else:
                        value = value
                        add = True
                    chatter_document.save()
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, value, add)
                    response_auto = ""
                    if chatter_document['data_games']['fish']['auto']['cast'] > 0 and not initial_auto:
                        chatter_document['data_games']['fish']['auto']['cast'] -= 1
                        if chatter_document['data_games']['fish']['auto']['cast'] == 0:
                            final_auto = True
                            auto_cost_value = chatter_document['data_games']['fish']['auto']['cost']
                            auto_casts, auto_catches_gain, auto_catches_lost, auto_catches_list, free_packs = 0, 0.0, 0.0, [], 0
                            for key, value in chatter_document['data_games']['fish']['auto']['catches'].items():
                                if key not in chatter_document['data_games']['fish']['totals']['auto']['catches']:
                                    chatter_document['data_games']['fish']['totals']['auto']['catches'][key] = [value[0], value[1]]
                                else:
                                    chatter_document['data_games']['fish']['totals']['auto']['catches'][key][0] += value[0]
                                    chatter_document['data_games']['fish']['totals']['auto']['catches'][key][1] += value[1]
                                if value[1] >= 0:
                                    auto_catches_gain += value[1]
                                else:
                                    auto_catches_lost += value[1]
                                if key == "a FreePack Redemption":
                                    free_packs += value[0]
                                auto_casts += value[0]
                                auto_catches_list.append([key, value[0], value[1]])
                            top_five_unique_sorted = sorted(auto_catches_list, key=lambda x: x[1], reverse=True)
                            top_five_totals_sorted = sorted(auto_catches_list, key=lambda x: abs(x[2]) / x[1], reverse=True)
                            chatter_document['data_games']['fish']['auto'] = {"cast": 0, "catches": {}, "cost": 0}
                            chatter_document['data_games']['fish']['totals']['auto']['cost'] += auto_cost_value
                            top_five_unique_list = []
                            top_five_totals_list = []
                            for n, item in enumerate(top_five_unique_sorted[:5]):
                                top_five_unique_list.append(f"{n+1}: {item[0]} total value {numberize(item[2])} caught {numberize(item[1])} time{'s' if item[1] != 1 else ''}")
                            for n, item in enumerate(top_five_totals_sorted[:5]):
                                top_five_totals_list.append(f"{n+1}: {item[0]} worth {numberize(item[2] / item[1])} caught {numberize(item[1])} time{'s' if item[1] != 1 else ''}")
                            fish_pond_quantity = read_fish_pond()
                            points_change = numberize((auto_catches_gain + auto_catches_lost) - auto_cost_value)
                            response_auto = f"AutoCast Expired from {auto_casts:,}: Unique Items Caught/Total Available; {len(auto_catches_list)}/{fish_pond_quantity}: Points Change; {points_change} {bot_name} Points. Top {len(top_five_unique_list)} catches whispered."
                            response_auto_whisper = f"Hey {chatter_document['name']}, your {auto_casts:,} AutoCast Expired{f'! You caught {numberize(free_packs)} FreePack Redemptions' if free_packs > 0 else ''}! Unique Items Caught/Total Available; {len(auto_catches_list)}/{fish_pond_quantity}: Points Change; {points_change}: Your Top {len(top_five_unique_list)} Unique Catches; {' | '.join(top_five_unique_list) if len(auto_catches_list) != auto_casts else f'You only caught your {len(auto_catches_list):,} once each.'} ||| Top {len(top_five_totals_list)} Points Values; {' | '.join(top_five_totals_list)}"
                            fish_logger.info(f"{long_dashes}\n{fortime()}: AUTO CAST EXPIRED FOR {chatter_document['name']}\n{response_auto}\n{long_dashes}\n{response_auto_whisper.replace(' ||| ', nl)}\n{long_dashes}")  #{auto_catches_list}\n{long_dashes}\n{top_five_unique_sorted}\n{long_dashes}\n{top_five_totals_sorted}\n{long_dashes}\n{response_auto}\n{response_auto_whisper}")
                    if not chatter_document['data_games']['fish']['line']['cast']:
                        bot_restart = True
                    else:
                        bot_restart = False
                        chatter_document['data_games']['fish']['line']['cast'] = False
                    chatter_document.save()
                    chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    if chatter_document['data_games']['fish']['auto']['cast'] > 0:
                        name = chatter_document['name']
                        response_fish_message = f"{'!fish' if not bot_restart else 'AUTO_CAST_PAUSED_RESTART_DETECTED'} {name} | You{'r' if line_cut else ''} {fish_response}! Your new points are: {numberize(chatter_document['data_user']['rank']['points'])}{f' {response_level}' if response_level is not None else ''}. You have {chatter_document['data_games']['fish']['auto']['cast']} Auto Casts Remaining."
                    else:
                        response_fish_message = f"{chatter_document['name']} you{'r' if line_cut else ''} {fish_response}! Your new points are: {numberize(chatter_document['data_user']['rank']['points'])}.{f' {response_level}.' if response_level is not None else ''}"
                    if response_time_add != "":
                        response_fish_message += f" | {response_time_add}"
                    if response_freepack != "":
                        response_fish_message += f" | {chatter_document['name']} I'm attempting to whisper you a FreePack Code!!{'' if len(chatter_document['data_user']['dates']['daily_cards'][2]) > 0 else f' Check your whisper settings if you dont get it and its our first time whispering. Let {name_streamer} know eh?'}"
                    if fish_jail_reason != "":
                        response_fish_message += f" | {fish_jail_reason}!!"
                    if response_auto != "":
                        response_fish_message += f" | {response_auto}"
                    if chatter_document['data_games']['jail']['in'] and chatter_document['data_games']['fish']['auto']['cast'] > 0:
                        wait_time = abs(jail_time - (await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last']))))
                        response_fish_message += f" | {chatter_document['name']} you're in jail!! Your AutoCasting will continue in {str(datetime.timedelta(seconds=wait_time)).title()}!!"
                    await bot.send_chat_message(streamer.id, streamer.id, response_fish_message)
                    if response_freepack != "" and chatter_document['_id'] != streamer.id:
                        try:
                            await bot.send_whisper(id_streamer, chatter_document['_id'], response_freepack)
                        except Exception as freepack_fail:
                            await asyncio.sleep(1)
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- fish command -- freepack redemption whisper failed -- {freepack_fail}\n{fish}\n{long_dashes}\n{data}\n{long_dashes}")
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} an attempt was made to whisper you but failed for reasons logged in thee background. Your fishing free redemption DID go thru, and your code/attempt has been logged.", reply_parent_message_id=data.event.message_id)
                            end_timer("fish freepack redeemed but failed to whisper")
                            return
                    elif fish_jail_reason != "" and chatter_document['data_games']['fish']['auto']['cast'] == 0 and not final_auto:
                        await asyncio.sleep(abs(jail_time - (await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])))))
                        chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                        chatter_document['data_games']['jail']['in'] = False
                        chatter_document['data_games']['jail']['last'] = datetime.datetime.now()
                        chatter_document.save()
                        if chatter_document['_id'] in channel_document['data_lists']['mods']:
                            await bot.add_channel_moderator(id_streamer, chatter_document['_id'])
                    elif final_auto:
                        try:
                            await bot.send_whisper(streamer.id, chatter_document['_id'], response_auto_whisper)
                        except Exception as whisper_fail:
                            logger.error(f"{fortime()}: error in on_stream_chat_message -- fish command -- whisper autocast expire top 5 to {chatter_document['name']} failed -- {whisper_fail}")
                            await asyncio.sleep(1)
                            await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_document['name']} an attempt was made to whisper you, but it failed. Error logged background")
                            pass
                except TwitchBackendException:
                    await asyncio.sleep(1)
                    try:
                        chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                        name = chatter_document['name']
                        message_attempt = f"{f'!fish {name} | ' if chatter_document['data_games']['fish']['auto']['cast'] > 0 and not initial_auto and not final_auto else f'{name},'} your cast message failed. Your last catch was '{' worth '.join(chatter_document['data_games']['fish']['line']['caught_last'])}' and your current points are {numberize(chatter_document['data_user']['rank']['points'])}"
                        await bot.send_chat_message(id_streamer, id_streamer, message_attempt)
                        logger.info(f"{fortime()}: TwitchBackendException handled OK. -- {chatter_document['name']}'s fish message\n{message_attempt}")
                        end_timer("fish command retry server error success")
                        return
                    except Exception as g:
                        error_command(f"fish command TwitchBackendException handled FAIL\n{data}\n", g)
                        return
                except Exception as f:
                    error_command("fish command", f)
                    return
            elif command_check.startswith("gamble") and read_bot_minigames():
                try:
                    bet_cost = 5000
                    if command_check.removeprefix("gamble").startswith("total"):
                        await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} thee total to be won is {numberize(channel_document['data_games']['gamble']['total'])} {bot_name} Points. Bet Cost is; {numberize(bet_cost)} {bot_name} Points.", reply_parent_message_id=data.event.message_id)
                        end_timer("gamble command total")
                        return
                    if chatter_document['data_user']['rank']['points'] < bet_cost:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You do not have enough points to bet {numberize(bet_cost)}. You currently have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points", reply_parent_message_id=data.event.message_id)
                        end_timer("gamble command")
                        return
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, bet_cost, False, True)
                    if pr.prob(95/100):
                        channel_document['data_games']['gamble']['total'] += bet_cost
                        if chatter_username not in channel_document['data_games']['gamble']['viewers']:
                            channel_document['data_games']['gamble']['viewers'][chatter_username] = {'total': 1, 'won': 0, 'lost': 1, 'total_won': 0, 'total_lost': bet_cost}
                        else:
                            channel_document['data_games']['gamble']['viewers'][chatter_username]['total'] += 1
                            channel_document['data_games']['gamble']['viewers'][chatter_username]['lost'] += 1
                            channel_document['data_games']['gamble']['viewers'][chatter_username]['total_lost'] += bet_cost
                        channel_document.save()
                        channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                        response_gamble = f"You lost {numberize(bet_cost)}! You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points! New total to be won is; {numberize(channel_document['data_games']['gamble']['total'])}"
                    else:
                        win_value = channel_document['data_games']['gamble']['total'] + bet_cost
                        chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, win_value, True, True)
                        channel_document['data_games']['gamble']['total'] = 10000.0
                        if chatter_username not in channel_document['data_games']['gamble']['viewers']:
                            channel_document['data_games']['gamble']['viewers'][chatter_username] = {'total': 1, 'won': 1, 'lost': 0, 'total_won': win_value, 'total_lost': 0}
                        else:
                            channel_document['data_games']['gamble']['viewers'][chatter_username]['total'] += 1
                            channel_document['data_games']['gamble']['viewers'][chatter_username]['won'] += 1
                            channel_document['data_games']['gamble']['viewers'][chatter_username]['total_won'] += win_value
                        channel_document.save()
                        channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                        response_gamble = f"You won {numberize(win_value)}! You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points! New total to be won has been reset to; {numberize(channel_document['data_games']['gamble']['total'])}"
                    gamble_logger.info(f"{fortime()}: {chatter_id}/{chatter_username} gambled and {response_gamble}.")
                    await bot.send_chat_message(streamer.id, streamer.id, response_gamble, reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    gamble_logger.error(f"{fortime()}: Error in on_stream_chat_message - gamble command -- {f}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong, TheeChody will fix it sooner than later. Error logged in thee background", reply_parent_message_id=data.event.message_id)
                    error_command("gamble command", f)
                    return
            elif command_check.startswith("iq") and read_bot_minigames():
                try:
                    now_time = datetime.datetime.now()
                    if command.replace(" ", "").removeprefix("iq").startswith("history"):
                        response_iq = []
                        for entry in reversed(chatter_document['data_games']['iq']['history'][-10:]):
                            response_iq.append(str(entry))
                        await bot.send_chat_message(id_streamer, id_streamer, f"Your last 10 IQ's were; {' | '.join(response_iq)}", reply_parent_message_id=data.event.message_id)
                        end_timer("iq command history")
                        return
                    elif chatter_document['data_games']['iq']['last'] is None: pass
                    elif now_time.day == chatter_document['data_games']['iq']['last'].day:
                        if now_time.month == chatter_document['data_games']['iq']['last'].month:
                            if now_time.year == chatter_document['data_games']['iq']['last'].year:
                                await bot.send_chat_message(id_streamer, id_streamer, f"You've already checked your IQ for thee day, it's {chatter_document['data_games']['iq']['current']}.")
                                end_timer("iq_already_command")
                                return
                    iq = random.randint(-20, 420)
                    chatter_document['data_games']['iq']['current'] = iq
                    chatter_document['data_games']['iq']['last'] = datetime.datetime.now()
                    chatter_document['data_games']['iq']['history'].append(iq)
                    chatter_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username}'s IQ today is {iq}.")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("iq command error", f)
                    return
            elif command_check.startswith("jail") and read_bot_minigames():
                try:
                    now_time = datetime.datetime.now()
                    if command.replace(" ", "").replace("jail", "").startswith("probation"):
                        if chatter_document['data_games']['jail']['last'] is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you ain't on probation bud!", reply_parent_message_id=data.event.message_id)
                            end_timer("jail command - not probation")
                            return
                        elif chatter_document['data_user']['rank']['points'] < jail_cost / 5:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you don't have enough points! Need {numberize(jail_cost / 5)} points, you have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points.", reply_parent_message_id=data.event.message_id)
                            end_timer("jail command - probation - not enuff points")
                            return
                        elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])) >= jail_wait_time:
                            time_free = abs(jail_wait_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last']))))
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you've been free for {str(datetime.timedelta(seconds=time_free)).title()}!!", reply_parent_message_id=data.event.message_id)
                            end_timer("jail command - free probation")
                            return
                        chatter_document['data_games']['jail'].update(last=None)
                        chatter_document['data_games']['jail']['history']['early_released'] += 1
                        chatter_document['data_user']['rank']['points'] -= jail_cost / 5
                        chatter_document.save()
                        chatter_document = await get_chatter_document(data)
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you have been released from your probation!! You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points. Be careful!!", reply_parent_message_id=data.event.message_id)
                        end_timer("jail command - probation release successful")
                        return
                    elif command.replace(" ", "").replace("jail", "").startswith("protection"):
                        if chatter_document['data_games']['jail']['attempt_last'] is None: pass
                        elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['attempt_last'])) <= jail_shield_clear_time:
                            wait_time = abs(jail_shield_clear_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['attempt_last']))))
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you have recently attempted to put someone in jail, must wait {str(datetime.timedelta(seconds=wait_time)).title()} before you can buy protection.")
                            end_timer("jail_protection_too_early")
                            return
                        if chatter_document['data_games']['jail']['shield'] is None: pass
                        elif chatter_document['data_user']['rank']['points'] < jail_cost * 5:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you don't have enough {bot_name} points, you need {jail_cost * 5}, but you have {numberize(chatter_document['data_user']['rank']['points'])}", reply_parent_message_id=data.event.message_id)
                            end_timer("jail_protection_not_enuff")
                            return
                        elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['shield'])) <= jail_shield_time:
                            protect_time = abs(jail_shield_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['shield']))))
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you are still protected for another {str(datetime.timedelta(seconds=protect_time)).title()}.", reply_parent_message_id=data.event.message_id)
                            end_timer("jail_protection_already_protected")
                            return
                        chatter_document['data_games']['jail']['shield'] = now_time
                        chatter_document['data_games']['jail']['history']['times_shielded'] += 1
                        chatter_document['data_user']['rank']['points'] -= jail_cost * 5
                        chatter_document.save()
                        chatter_document = await get_chatter_document(data)
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you have been put under {bot_name} protection for {str(datetime.timedelta(seconds=jail_shield_time)).title()}. You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points.")
                        end_timer("jail_protection_started")
                        return
                    elif command.replace(" ", "").replace("jail", "").startswith("stats") and chatter_id == id_chodebot:
                        pass
                    elif chatter_document['data_user']['rank']['points'] < jail_cost and chatter_id != id_streamer:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you don't have enough points! Need {numberize(jail_cost)} points, you have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points.", reply_parent_message_id=data.event.message_id)
                        end_timer("jail command - not enuff points")
                        return
                    if command.replace(" ", "").replace("jail", "").startswith("@"):
                        target_user_name = command.replace(" ", "").replace("jail@", "")
                    else:
                        target_user_name = command.replace(" ", "").replace("jail", "")
                    target = await select_target(channel_document, chatter_id, True, target_user_name, game_type="jail")
                    if target is None:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_user_name} is not in chat right now or just joined chat. Try again later", reply_parent_message_id=data.event.message_id)
                        end_timer("jail command - target none random")
                        return
                    elif target.user_id in (id_streamer, id_streamloots):
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you cannot attempt to jail {target.user_name}", reply_parent_message_id=data.event.message_id)
                        end_timer(f"jail command - target not valid -- {target.user_name}")
                        return
                    target_document = await get_chatter_document(None, channel_document, target.user_id, target.user_name, target.user_login, id_streamer, name_streamer)
                    if target_document is None:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name}'s document couldn't be loaded!!! Aborting jail attempt.", reply_parent_message_id=data.event.message_id)
                        end_timer("jail-target_doc is none")
                        return
                    if chatter_document['data_games']['jail']['shield'] is None: pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['shield'])) <= jail_shield_time:
                        if target_document['name'] not in chatter_document['data_games']['jail']['history']['attempt_shielded']:
                            chatter_document['data_games']['jail']['history']['attempt_shielded'][target_document['name']] = 1
                        else:
                            chatter_document['data_games']['jail']['history']['attempt_shielded'][target_document['name']] += 1
                        chatter_document.save()
                        protect_time = abs(jail_shield_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['shield']))))
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you are still protected for another {str(datetime.timedelta(seconds=protect_time)).title()}, therefore you cannot attempt to jail anyone else.", reply_parent_message_id=data.event.message_id)
                        end_timer("jail_protection_already_protected_cant_jail")
                        return
                    if chatter_document['data_games']['jail']['last'] is None: pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])) <= jail_wait_time:
                        wait_time = jail_wait_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you cannot attempt to jail someone right now as you're on 'Probation' and will have to wait {str(datetime.timedelta(seconds=wait_time)).title()} till it expires.", reply_parent_message_id=data.event.message_id)
                        end_timer("jail command - been in jail, cannot attempt")
                        return
                    if target_document['data_games']['jail']['in']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} is already in jail right now!!", reply_parent_message_id=data.event.message_id)
                        end_timer("jail command - target in jail")
                        return
                    if target_document['data_games']['jail']['shield'] is None: pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['shield'])) <= jail_shield_time:
                        if chatter_id != id_streamer:
                            if chatter_username not in target_document['data_games']['jail']['history']['shielded_attempt']:
                                target_document['data_games']['jail']['history']['shielded_attempt'][chatter_username] = 1
                            else:
                                target_document['data_games']['jail']['history']['shielded_attempt'][chatter_username] += 1
                            target_document.save()
                            wait_time = abs(jail_shield_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['shield']))))
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} is being protected right now, must wait {str(datetime.timedelta(seconds=wait_time)).title()}. Aborting jail attempt.", reply_parent_message_id=data.event.message_id)
                            end_timer("jail command - target protected")
                            return
                    if target_document['data_games']['jail']['last'] is None: pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['last'])) <= jail_wait_time:
                        if chatter_id != id_streamer:
                            wait_time = jail_wait_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['last'])))
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} has been jailed too recently to attempt, must wait {str(datetime.timedelta(seconds=wait_time)).title()}. Aborting jail attempt.", reply_parent_message_id=data.event.message_id)
                            end_timer("jail command - target probation still")
                            return
                    if chatter_id != id_streamer:
                        chatter_document['data_user']['rank']['points'] -= jail_cost
                        chatter_document['data_games']['jail']['attempt_last'] = now_time
                        chatter_document.save()
                        chatter_document = await get_chatter_document(data)
                    if pr.prob(80/100) or chatter_id == id_streamer:
                        if target_document['data_games']['jail']['escapes'] > 0 and chatter_id != id_streamer:
                            target_document['data_games']['jail']['escapes'] -= 1
                            if chatter_username not in target_document['data_games']['jail']['history']['escaped_attempt']:
                                target_document['data_games']['jail']['history']['escaped_attempt'][chatter_username] = 1
                            else:
                                target_document['data_games']['jail']['history']['escaped_attempt'][chatter_username] += 1
                            target_document.save()
                            if target_document['name'] not in chatter_document['data_games']['jail']['history']['attempt_fail']:
                                chatter_document['data_games']['jail']['history']['attempt_fail'][target_document['name']] = 1
                            else:
                                chatter_document['data_games']['jail']['history']['attempt_fail'][target_document['name']] += 1
                            chatter_document.save()
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} had a 'Free2Escape Jail Card' and escapes {chatter_username}'s jail attempt!! {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!", reply_parent_message_id=data.event.message_id)
                            end_timer("jail attempt escaped")
                            return
                        target_document['data_games']['jail']['in'] = True
                        target_document['data_games']['jail']['last'] = now_time
                        if chatter_username not in target_document['data_games']['jail']['history']['in']:
                            target_document['data_games']['jail']['history']['in'][chatter_username] = 1
                        else:
                            target_document['data_games']['jail']['history']['in'][chatter_username] += 1
                        target_document.save()
                        if target_document['name'] not in chatter_document['data_games']['jail']['history']['attempt_success']:
                            chatter_document['data_games']['jail']['history']['attempt_success'][target_document['name']] = 1
                        else:
                            chatter_document['data_games']['jail']['history']['attempt_success'][target_document['name']] += 1
                        chatter_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} jailed {target.user_name} for {datetime.timedelta(seconds=jail_time)}!! {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} points.", reply_parent_message_id=data.event.message_id)
                        await bot.ban_user(id_streamer, id_streamer, target.user_id, f"You've been jailed by {chatter_username} for {datetime.timedelta(seconds=jail_time)}.", jail_time)
                        await asyncio.sleep(jail_time + 1)
                        target_document = await get_chatter_document(None, channel_document, target.user_id, target.user_name, target.user_login, id_streamer, name_streamer)
                        target_document['data_games']['jail']['in'] = False
                        target_document['data_games']['jail']['last'] = datetime.datetime.now()
                        target_document.save()
                        if target.user_id in channel_document['data_lists']['mods']:
                            await bot.add_channel_moderator(id_streamer, target.user_id)
                    else:
                        if chatter_document['data_games']['jail']['escapes'] > 0:
                            chatter_document['data_games']['jail']['escapes'] -= 1
                            if target_document['name'] not in chatter_document['data_games']['jail']['history']['attempt_fail']:
                                chatter_document['data_games']['jail']['history']['attempt_fail'][target_document['name']] = 1
                            else:
                                chatter_document['data_games']['jail']['history']['attempt_fail'][target_document['name']] += 1
                            if target_document['name'] not in chatter_document['data_games']['jail']['history']['escaped_attempt']:
                                chatter_document['data_games']['jail']['history']['escaped_attempt'][target_document['name']] += 1
                            chatter_document.save()
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} attempted to jail {target.user_name} for {datetime.timedelta(seconds=jail_time)} but was caught in thee act however, they had a Free2Escape Jail Card escaping their failed attempt!! {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} points.", reply_parent_message_id=data.event.message_id)
                            end_timer("jail attempt fail escaped")
                            return
                        chatter_document['data_games']['jail']['in'] = True
                        chatter_document['data_games']['jail']['last'] = now_time
                        if target_document['name'] not in chatter_document['data_games']['jail']['history']['in']:
                            chatter_document['data_games']['jail']['history']['in'][target_document['name']] = 1
                        else:
                            chatter_document['data_games']['jail']['history']['in'][target_document['name']] += 1
                        if target_document['name'] not in chatter_document['data_games']['jail']['history']['attempt_fail']:
                            chatter_document['data_games']['jail']['history']['attempt_fail'][target_document['name']] = 1
                        else:
                            chatter_document['data_games']['jail']['history']['attempt_fail'][target_document['name']] += 1
                        chatter_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} attempted to jail {target.user_name} for {datetime.timedelta(seconds=jail_time)} but was caught in thee act and was instead jailed themselves!! {chatter_username} you now have {numberize(chatter_document['data_user']['rank']['points'])} points.", reply_parent_message_id=data.event.message_id)
                        await bot.ban_user(id_streamer, id_streamer, chatter_id, f"You've been jailed for your attempt to jail {target.user_name} for {datetime.timedelta(seconds=jail_time)}.", jail_time)
                        await asyncio.sleep(jail_time + 1)
                        chatter_document = await get_chatter_document(data)
                        chatter_document['data_games']['jail']['in'] = False
                        chatter_document['data_games']['jail']['last'] = datetime.datetime.now()
                        chatter_document.save()
                        if chatter_id in channel_document['data_lists']['mods']:
                            await bot.add_channel_moderator(id_streamer, chatter_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("jail command - error", f)
                    return
            elif command_check.startswith("numberize") and read_bot_minigames():
                try:
                    number_to_numberize = command_check.removeprefix("numberize")
                    try:
                        number_to_numberize = float(number_to_numberize)
                    except ValueError:
                        await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} {number_to_numberize} isn't a valid number to numberize!! Try again", reply_parent_message_id=data.event.message_id)
                        end_timer("numberize fail")
                        return
                    await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} {number_to_numberize:,.2f} numberized is; {numberize(number_to_numberize)}", reply_parent_message_id=data.event.message_id)
                    end_timer("numberize success")
                    return
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("numberize command", f)
                    return
            elif command_check.startswith("pp") and read_bot_minigames():
                async def already_done():
                    size = chatter_document['data_games']['pp']['size']
                    await bot.send_chat_message(id_streamer, id_streamer, f"You've already checked your pp size today, it's a {f'{size} inch pecker' if size > 0 else f'{size} inch innie'}", reply_parent_message_id=data.event.message_id)
                    end_timer("pp_already command")
                try:
                    now_time = datetime.datetime.now()
                    if command.replace(" ", "").removeprefix("pp").startswith("history"):
                        response_pp = []
                        if chatter_id == "627417784":  # Chrispy's ID
                            final_response = "".join(chatter_document['data_games']['pp']['history'])
                        else:
                            for entry in reversed(chatter_document['data_games']['pp']['history'][-10:]):
                                response_pp.append(f"{entry} inch pecker" if entry > 0 else f"{entry} inch innie")
                            final_response = f"Your last 10 pp sizes were: {' | '.join(response_pp)}"
                        await bot.send_chat_message(id_streamer, id_streamer, final_response, reply_parent_message_id=data.event.message_id)
                        end_timer("pp_history command")
                        return
                    elif chatter_id == "627417784":  # Chrispy's ID
                        size = -69
                        chatter_document['data_games']['pp'] = [size, now_time, ["Always -69 inches depth"]]
                        chatter_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} is The King of Thee Innie's, as such has Thee Deepest of Deep Innie's at {size} inch innie")
                        end_timer("pp_moist command")
                        return
                    elif chatter_document['data_games']['pp']['last'] is None: pass
                    elif now_time.day == chatter_document['data_games']['pp']['last'].day:
                        if now_time.month == chatter_document['data_games']['pp']['last'].month:
                            if now_time.year == chatter_document['data_games']['pp']['last'].year:
                                await already_done()
                                return
                    size = random.randint(-4, 18)
                    chatter_document['data_games']['pp']['size'] = size
                    chatter_document['data_games']['pp']['last'] = now_time
                    chatter_document['data_games']['pp']['history'].append(size)
                    chatter_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username}'s packin' a {f'{size} inch pecker' if size > 0 else f'{size} inch innie'}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("pp command", f)
                    return
            elif command_check.startswith("tag") and read_bot_minigames():
                try:
                    if command.replace(" ", "").removeprefix("tag").startswith(("history", "stats")):
                        await bot.send_chat_message(id_streamer, id_streamer, f"Your tag stats are (Total/Valid/Fail): {chatter_document['data_games']['tag']['total']}/{chatter_document['data_games']['tag']['success']}/{chatter_document['data_games']['tag']['fail']}", reply_parent_message_id=data.event.message_id)
                        end_timer("tag history command")
                        return
                    rem_response, target_rem_response, response_level = None, None, None
                    if chatter_id in channel_document['data_lists']['non_tag']:
                        channel_document['data_lists']['non_tag'].remove(chatter_id)
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                        rem_response = f"You have been removed from thee untag list"
                    if channel_document['data_games']['tag']['tagged_last'] is None:
                        last_tag_id, last_tag_name, time_since_tagged = chatter_id, chatter_username, datetime.datetime.now()
                    else:
                        last_tag_id, last_tag_name, time_since_tagged = channel_document['data_games']['tag']['tagged_id'], channel_document['data_games']['tag']['tagged_name'], await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(channel_document['data_games']['tag']['tagged_last']))
                    if chatter_id != last_tag_id and time_since_tagged < 120:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are not last tagged, {last_tag_name} is last to be tagged. {abs(time_since_tagged - 120)} seconds till able to tag.{f' {rem_response}' if rem_response is not None else ''}", reply_parent_message_id=data.event.message_id)
                        end_timer("tag command")
                        return
                    else:
                        while True:
                            target = await select_target(channel_document, chatter_id)
                            if target is None:
                                channel_document['data_games'].update(tag={"tagged_id": None, "tagged_name": None, "tagged_last": None})
                                channel_document.save()
                                await bot.send_chat_message(id_streamer, id_streamer, f"Error fetching a random tag target.. Are we thee only ones here??{f' {rem_response}.' if rem_response is not None else ''}{f' {target_rem_response}.' if target_rem_response is not None else ''}")
                                end_timer("tag command")
                                return
                            elif chatter_id != last_tag_id and last_tag_id != "":
                                if last_tag_id not in channel_document['data_lists']['non_tag']:
                                    prior_target_chatter_doc = Users.objects.get(_id=last_tag_id)
                                    channel_document['data_lists']['non_tag'].append(last_tag_id)
                                    channel_document['data_games']['tag'] = {"tagged_id": None, "tagged_name": None, "tagged_last": None}
                                    channel_document.save()
                                    channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                                    last_tag_id = ""
                                    target_rem_response = f"{prior_target_chatter_doc['name']} has been added to untag list"
                                    await update_tag_stats(prior_target_chatter_doc, 1, 0, 1)
                            elif chatter_id == last_tag_id or last_tag_id == "":
                                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, 2.5)
                                chatter_document, response_tag = await update_tag_stats(chatter_document, 1, 1, 0)
                                break
                        channel_document['data_games']['tag'] = {"tagged_id": target.user_id, "tagged_name": target.user_name, "tagged_last": datetime.datetime.now()}
                        channel_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{'!tag ' if target.user_id == id_streamer else ''}{chatter_username} tags {target.user_name}{f' {rem_response}.' if rem_response is not None else '.'}{f' {target_rem_response}' if target_rem_response is not None else ''}{f' {response_tag}.' if response_tag is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("tag command", f)
                    return
            elif command_check.startswith(("notag", "untag")) and read_bot_minigames():
                try:
                    if chatter_id not in channel_document['data_lists']['non_tag']:
                        channel_document['data_lists']['non_tag'].append(chatter_id)
                        channel_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are now out of thee tag game", reply_parent_message_id=data.event.message_id)
                    elif chatter_id in channel_document['data_lists']['non_tag']:
                        channel_document['data_lists']['non_tag'].remove(chatter_id)
                        channel_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are now back in thee tag game", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("untag command", f)
                    return
            # Counter Commands
            elif command_check.startswith("atscount"):
                try:
                    command_check = command_check.removeprefix("atscount")
                    if chatter_id == streamer.id or chatter_id in channel_document['data_lists']['mods']:
                        if command_check.startswith("game"):
                            game_crash = await check_float(command_check.removeprefix("game"))
                            if game_crash is None:
                                end_timer("atscount fail")
                                return
                            channel_document['data_counters']['ats']['game_crash'] += int(game_crash)
                        elif command_check.startswith(("truck", "tractor")):
                            tractor_crash = await check_float(command_check.removeprefix("truck").removeprefix("tractor"))
                            if tractor_crash is None:
                                end_timer("atscount fail")
                                return
                            channel_document['data_counters']['ats']['tractor_crash'] += int(tractor_crash)
                        elif command.replace(" ", "").removeprefix("atscount").startswith("reset"):
                            channel_document['data_counters']['ats']['game_crash'] = 0
                            channel_document['data_counters']['ats']['tractor_crash'] = 0
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    await bot.send_chat_message(id_streamer, id_streamer, f"American Truck Sim Crash Count (Tractor/Game): {channel_document['data_counters']['ats']['tractor_crash']} / {channel_document['data_counters']['ats']['game_crash']}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("atscount command", f)
                    return
            elif command_check.startswith("codcount"):
                try:
                    if chatter_id == id_streamer or chatter_id in channel_document['data_lists']['mods']:
                        command_check = command_check.removeprefix("codcount")
                        if command_check.startswith("total"):
                            total = await check_float(command_check.removeprefix("total"))
                            if total is None:
                                end_timer("codcount fail")
                                return
                            channel_document['data_counters']['cod']['game_total'] += int(total)
                        elif command_check.startswith("win"):
                            win = await check_float(command_check.removeprefix("win"))
                            if win is None:
                                end_timer("codcount fail")
                                return
                            channel_document['data_counters']['cod']['game_win'] += int(win)
                        elif command_check.startswith(("loss", "lost", "lose")):
                            loss = await check_float(command_check.removeprefix("loss").removeprefix("lost").removeprefix("lose"))
                            if loss is None:
                                end_timer("codcount fail")
                                return
                            channel_document['data_counters']['cod']['game_loss'] += int(loss)
                        elif command_check.startswith("crash"):
                            crash = await check_float(command_check.removeprefix("crash"))
                            if crash is None:
                                end_timer("codcount fail")
                                return
                            channel_document['data_counters']['cod']['game_crash'] += int(crash)
                        elif command_check.startswith("reset"):
                            channel_document['data_counters']['cod']['game_total'] = 0
                            channel_document['data_counters']['cod']['game_win'] = 0
                            channel_document['data_counters']['cod']['game_loss'] = 0
                            channel_document['data_counters']['cod']['game_crash'] = 0
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    await bot.send_chat_message(id_streamer, id_streamer, f"CoD Counter (Matches/Wins/Losses/Crashes): {channel_document['data_counters']['cod']['game_total']} / {channel_document['data_counters']['cod']['game_win']} / {channel_document['data_counters']['cod']['game_loss']} / {channel_document['data_counters']['cod']['game_crash']}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("codcount command", f)
                    return
            elif command_check.startswith("jointscount"):
                async def update_history(channel_document: Document):
                    date = str(channel_document['data_counters']['joints']['smoked_last'].strftime("%y-%m-%d"))
                    if date not in channel_document['data_counters']['joints']['smoked_history']:
                        channel_document['data_counters']['joints']['smoked_history'][date] = channel_document['data_counters']['joints']['smoked']
                    else:
                        channel_document['data_counters']['joints']['smoked_history'][date] += channel_document['data_counters']['joints']['smoked']
                    channel_document['data_counters']['joints']['smoked'] = 0
                    channel_document['data_counters']['joints'].update(smoked_last=None)
                    channel_document.save()
                    return await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                new_day = None
                try:
                    if chatter_id == id_streamer or chatter_id in channel_document['data_lists']['mods']:
                        command_check = command_check.removeprefix("jointscount")
                        if command_check.startswith("update"):
                            update = await check_float(command_check.removeprefix("update"))
                            if update is None:
                                end_timer("jointscount fail")
                                return
                            if channel_document['data_counters']['joints']['smoked_last'] is not None:
                                if datetime.datetime.now().day != channel_document['data_counters']['joints']['smoked_last'].day:
                                    new_day = f" New Day Detected, Resetting Count"
                                    channel_document = await update_history(channel_document)
                            channel_document['data_counters']['joints']['smoked'] += int(update)
                            channel_document['data_counters']['joints']['smoked_last'] = datetime.datetime.now()
                        elif command_check.startswith("reset"):
                            if channel_document['data_counters']['joints']['smoked_last'] is not None:
                                channel_document = await update_history(channel_document)
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    await bot.send_chat_message(streamer.id, streamer.id, f"Current Joints Count (Total/Last Smoked); {channel_document['data_counters']['joints']['smoked']} / {'None' if channel_document['data_counters']['joints']['smoked_last'] is None else str(channel_document['data_counters']['joints']['smoked_last'].strftime('%I:%M%p')).removeprefix('0').lower()}.{new_day if new_day is not None else ''}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("jointscount command", f)
                    return
            elif command_check.startswith("streamcount"):
                try:
                    if chatter_id == id_streamer or chatter_id in channel_document['data_lists']['mods']:
                        command_check = command_check.removeprefix("streamcount")
                        if command_check.startswith("bot"):
                            bot_restart = await check_float(command_check.removeprefix("bot"))
                            if bot_restart is None:
                                end_timer("streamcount fail")
                                return
                            channel_document['data_counters']['stream']['bot_restart'] += int(bot_restart)
                        elif command_check.startswith("crash"):
                            crash = await check_float(command_check.removeprefix("crash"))
                            if crash is None:
                                end_timer("streamcount fail")
                                return
                            channel_document['data_counters']['stream']['crash'] += int(crash)
                        elif command_check.startswith("reset"):
                            channel_document['data_counters']['stream']['bot_restart'] = 0
                            channel_document['data_counters']['stream']['crash'] = 0
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{marathon_name} Bot Restart/Stream Crash Count: {channel_document['data_counters']['stream']['bot_restart']} / {channel_document['data_counters']['stream']['crash']}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("streamcount command", f)
                    return
            # Marathon Commands
            elif command_check.startswith(("lube", "ice")):  # and chatter_id == streamer.id:
                try:
                    if command_check.startswith("lube") and chatter_document['data_games']['fish']['special']['lube'] > 0:
                        chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, time_lube)
                        chatter_document['data_games']['fish']['special']['lube'] -= 1
                        chatter_document.save()
                        chatter_document = await refresh_chatter_document(data)
                        new_current = write_clock_lube(time_lube)
                        set_timer_lube(obs, new_current)
                        obs.set_source_visibility(obs_timer_scene, obs_timer_lube, True)
                        await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} applies lube to thee timer, increasing time manipulated by {rate_lube}x for {str(datetime.timedelta(seconds=time_lube)).title()}{f', total time; {str(datetime.timedelta(seconds=new_current)).title()}' if new_current != time_lube else ''}. {chatter_username} you have {chatter_document['data_games']['fish']['special']['lube']} bottles of lube left.. You have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points.{f' {response_level}' if response_level is not None else ''}")
                    elif command_check.startswith("ice") and chatter_document['data_games']['fish']['special']['ice'] > 0:
                        chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, time_ice)
                        chatter_document['data_games']['fish']['special']['ice'] -= 1
                        chatter_document.save()
                        chatter_document = await refresh_chatter_document(data)
                        write_clock_phase("slow")
                        new_current = write_clock_time_phase_slow(time_ice)
                        set_timer_rate(obs, "slow")
                        obs.set_source_visibility(obs_timer_scene, obs_timer_rate, True)
                        await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} applies ice to thee timer, slowing it for {str(datetime.timedelta(seconds=time_ice)).title()}{f', total time; {str(datetime.timedelta(seconds=new_current)).title()}' if new_current != time_ice else ''}. {chatter_username} you have {chatter_document['data_games']['fish']['special']['ice']} buckets of ice left.. You have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points.{f' {response_level}' if response_level is not None else ''}")
                    else:
                        ice_total = chatter_document['data_games']['fish']['special']['ice']
                        lube_total = chatter_document['data_games']['fish']['special']['lube']
                        await bot.send_chat_message(streamer.id, streamer.id, f"{chatter_username} you don't have any bottles of lube or buckets of ice to apply.. Go fish and try and get some" if ice_total + lube_total == 0 else f"{chatter_username} you have {numberize(ice_total)} buckets of ice & {numberize(lube_total)} bottles of lube")
                    end_timer("lube/ice command")
                    return
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command(f"lube/ice command", f)
                    return
            elif command_check.startswith("freepack"):
                try:
                    now_time = datetime.datetime.now()
                    if chatter_document['data_user']['rank']['points'] < free_pack_cost:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points, you need {numberize(free_pack_cost)} and you have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points. You currently have {chatter_document['data_user']['dates']['daily_cards'][0]} packs waiting to be sent.", reply_parent_message_id=data.event.message_id)
                        end_timer("freepack Command")
                        return
                    elif chatter_document['data_user']['dates']['daily_cards'][1] is None: pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_user']['dates']['daily_cards'][1])) <= free_pack_time:
                        wait_time = free_pack_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_user']['dates']['daily_cards'][1])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"You gotta wait {str(datetime.timedelta(seconds=wait_time)).title()} for your next redeem. You currently have {chatter_document['data_user']['dates']['daily_cards'][0]} packs waiting to be sent.", reply_parent_message_id=data.event.message_id)
                        end_timer("freepack command")
                        return
                    if len(channel_document['data_lists']['coupons']) > 0:
                        coupon_code = channel_document['data_lists']['coupons'].pop(0)
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                        chatter_document['data_user']['dates']['daily_cards'][2].append(coupon_code)
                        response_freepack_whisper = f"Hey {chatter_username}, you redeemed a FreePack via !freepack command!! Here is your single use coupon code; {link_loots_coupon_blank}{coupon_code}"
                        special_logger.info(f"{fortime()}: {chatter_username} redeemed {numberize(free_pack_cost)} {bot_name} Points for 1 Pack -- {coupon_code} -- # coupons left on channel_document; {len(channel_document['data_lists']['coupons'])}")
                    else:
                        chatter_document['data_user']['dates']['daily_cards'][0] += 1
                        response_freepack_whisper = f"Hey {chatter_username}, I ran outta coupon codes!!!! {name_streamer} will get to it manually later on, remind him next time you see him, eh?"
                        special_logger.warn(f"{fortime()}: {chatter_username} attempted an AUTO REDEEM FREE PACK, but NO COUPON CODES AVAILABLE!!!")
                    chatter_document['data_user']['rank']['points'] -= free_pack_cost
                    chatter_document['data_user']['dates']['daily_cards'][1] = now_time
                    chatter_document.save()
                    chatter_document = await get_chatter_document(data)
                    wait_time = free_pack_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_user']['dates']['daily_cards'][1])))
                    response_freepack_whisper += f" Next redeem is in; {str(datetime.timedelta(seconds=wait_time - 2)).title()}. You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points."
                    response_freepack_message = f"{chatter_username} I'm about to attempt to whisper you a freepack code!!"
                    if len(chatter_document['data_user']['dates']['daily_cards'][2]) <= 1:
                        response_freepack_message += f" If you don't receive thee whisper, let {name_streamer} know, and make sure your whispers are open to strangers if we haven't talked before eh?"
                    await bot.send_chat_message(id_streamer, id_streamer, response_freepack_message, reply_parent_message_id=data.event.message_id)
                    await asyncio.sleep(2)
                    try:
                        await bot.send_whisper(id_streamer, chatter_id, response_freepack_whisper)
                    except Exception as freepack_fail:
                        await asyncio.sleep(1)
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- freepack command -- redemption whisper failed -- {freepack_fail}\n{long_dashes}\n{response_freepack_whisper}\n{response_freepack_message}\n{data}\n{long_dashes}")
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} an attempt was made to whisper you but failed for reasons logged in thee background. Your redemption DID go thru, and your code/attempt has been logged.", reply_parent_message_id=data.event.message_id)
                        end_timer("freepack redeemed but failed to whisper")
                        return
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command(f"freepack command", f)
                    return
            elif command_check.startswith(("streamloot", "loot", marathon_name.lower(), marathon_name.replace("-", "").lower(), "pack", "coupon")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{link_loots} | Monthly use 20% off coupon: {link_loots_discount}")
                    with open("data/bot/pack_link", "r") as file:
                        link = file.read()
                    ran_choice = random.randint(1, 2)
                    if ran_choice == 1:
                        response_pack = list(map(str, reversed(link.splitlines())))
                    else:
                        response_pack = list(map(str, link.splitlines()))
                    for i in range(0, len(response_pack), 10):
                        await bot.send_chat_message(id_streamer, id_streamer, " | ".join(response_pack[i:i + 10]))
                        await asyncio.sleep(0.5)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("loot command", f)
                    return
            elif command_check.startswith(("time2add", "timeadd")):
                try:
                    time_to_add = float(f"{abs(float(read_clock_max()) - float(read_clock_total())):.2f}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Time that can still be added to thee clock is: {str(datetime.timedelta(seconds=time_to_add)).title()}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("timeadd command", f)
                    return
            elif command_check.startswith(("timecurrent", "timeremain", "timeleft")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee current time remaining: {str(datetime.timedelta(seconds=int(float(read_clock())))).title()}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("timecurrent command", f)
                    return
            elif command_check.startswith(("timemax", "timecap")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee Marathon Cap is: {str(datetime.timedelta(seconds=float(read_clock_max()))).title()}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("timemax command", f)
                    return
            elif command_check.startswith(("timepause", "timepaused")):
                try:
                    time_pause = float(read_clock_pause())
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee timer is {f'currently paused for {str(datetime.timedelta(seconds=time_pause)).title()}' if time_pause != 0.0 else 'not currently paused'}.", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("timepause command", f)
                    return
            elif command_check.startswith(("timerate", "timedown")):
                try:
                    phase = read_clock_phase()
                    if phase == "accel":
                        time_left = float(read_clock_time_phase_accel())
                        response_phase = f"Timer Rate @ {int(strict_pause)} real sec/{int(countdown_rate_strict)} Timer Sec; {str(datetime.timedelta(seconds=time_left)).title()}"
                    elif phase == "slow":
                        time_left = float(read_clock_time_phase_slow())
                        response_phase = f"Timer Rate @ {int(countdown_rate_strict)} real sec/{int(strict_pause)} Timer Sec; {str(datetime.timedelta(seconds=time_left)).title()}"
                    else:
                        response_phase = f"Timer Rate @ 1 Real Sec/1 Timer Sec"
                    await bot.send_chat_message(id_streamer, id_streamer, response_phase, reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("timerate command", f)
                    return
            elif command_check.startswith("timesofar"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee total elapsed time so far is: {str(datetime.timedelta(seconds=float(read_clock_sofar()))).title()}.", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("timesofar command", f)
                    return
            elif command_check.startswith("time"):
                try:
                    response_throne = f"{standard_seconds * 2} Seconds / Cent Contributed ($1 = {str(datetime.timedelta(seconds=(standard_seconds * 2) * 100)).title()})"
                    response_direct_dono = f"{standard_direct_dono} Seconds / Cent Received ($1 = {str(datetime.timedelta(seconds=standard_direct_dono * 100)).title()})"
                    response_twitch = f"{standard_seconds} Seconds / Cent Received (100 bitties = {str(datetime.timedelta(seconds=standard_seconds * 100)).title()} -- 1 T1 subbie = {str(datetime.timedelta(seconds=standard_seconds * 250)).title()} -- 1 T2 subbie = {str(datetime.timedelta(seconds=standard_seconds * 500)).title()} -- 1 T3 subbie = {str(datetime.timedelta(seconds=standard_seconds * 1250)).title()})"
                    response_streamloots = f"{stream_loots_seconds} Seconds / Cent Received (1 card = {str(datetime.timedelta(seconds=stream_loots_seconds * 100)).title()}) (1 Pack of {stream_loots_pack_quantity} Cards = {str(datetime.timedelta(seconds=(stream_loots_seconds * 100) * stream_loots_pack_quantity)).title()})"
                    await bot.send_chat_message(id_streamer, id_streamer, f"Throne & TreatStream Contributions; {response_throne} | DirectDono; {response_direct_dono} | Twitch; {response_twitch} | Streamloots; {response_streamloots}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("times command", f)
                    return
            # Special Commands
            elif command_check.startswith("ak"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Shooting AK's, While downing shine, Sounds like a decent way to spend thee day", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("ak command", f)
                    return
            elif command_check.startswith(("beckky", "carnage")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"We're going on a trip, in our flavourite rocket ship.. Zooming through thee skies, Little Einsteins!!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("beckky/carnage command", f)
                    return
            elif command_check.startswith(("chicken", "xbox", "boxboy")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Love Peace n' Chicken Grease", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("chicken(boy) command", f)
                    return
            elif command_check.startswith(("clammy", "moist")):
                try:
                    if command.replace(" ", "").startswith("clammy"):
                        moist_response = f"First"
                    else:
                        moist_response = f"Second"
                    await bot.send_chat_message(id_streamer, id_streamer, f"Chrispy_Turtle's {moist_response} Flavourite word!!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("clammy/moist command", f)
                    return
            elif command_check.startswith("dark"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} and me go Throbbin in thee Dark.", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("dark command", f)
                    return
            elif command_check.startswith(("deecoy", "decoy")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "PettyMassacre is thee decoy, toss her in! Let thee rage consume them", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("deecoy command", f)
                    return
            elif command_check.startswith("fire"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"@FireGMC08, we gonna need you to turn up thee heat bro, ya skills are freezing cold!! :P", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("fire command", f)
                    return
            elif command_check.startswith("flip"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"(╯°□°）╯︵ ┻━┻", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("flip command", f)
                    return
            elif command_check.startswith("free"):
                try:
                    random_usernames = await bot.get_chatters(id_streamer, id_streamer)
                    target = random.choice(random_usernames.data)
                    await bot.send_chat_message(id_streamer, id_streamer, f"Free2Escape's name is now {target.user_name}. :P", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("free command", f)
                    return
            elif command_check.startswith("fuck"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"I'ma bout outta fucks to give. Time to light up me thinks", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("fuck command", f)
                    return
            elif command_check.startswith(("hug", "chodyhug")):
                try:
                    if command_check.removeprefix("hug").startswith("@"):
                        target_username = command_check.removeprefix("hug@")
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} gives Big Chody Hugs to {target_username}!")
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Big Chody Hugs!!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("hug command", f)
                    return
            elif command_check.startswith("hour"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Tic Tok on thee Clock. Till thee party don't st.. Nopeee", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("hour command", f)
                    return
            elif command_check.startswith("joe"):  # and chatter_id == "806552159":
                try:
                    if chatter_id == "806552159":  # Joe's id
                        response_joe = f"Dammit Me!!! Wait... I mean Dammit Joe!!!"
                    else:
                        response_joe = f"Dammit Joe!!!"
                    await bot.send_chat_message(id_streamer, id_streamer, response_joe, reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("joe command", f)
                    return
            elif command_check.startswith("lore"):  # and chatter_id == "170147951":
                try:
                    if chatter_id == "170147951":  # Maylore's id
                        response_lore = f"Fucking run Chody!! Run! It's Maylore himself here to taunt you"
                    else:
                        response_lore = f"{chatter_username} is taunting you with Maylore's command"
                    await bot.send_chat_message(id_streamer, id_streamer, response_lore, reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("lore command", f)
                    return
            elif command_check.startswith(("moony", "stardust")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Have some star dust on behalf of MoonyStarDust", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("moony command", f)
                    return
            elif command_check.startswith("mullen"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Toasted Crap Is Delicious!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("mullen command", f)
                    return
            elif command_check.startswith("mull"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Joe Say's \"Its !mullens try again\"", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("mull command", f)
                    return
            elif command_check.startswith("petty"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"🧩 If you know, you know 🧩", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("petty command", f)
                    return
            elif command_check.startswith("pious"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Something badass for sure!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("pious command", f)
                    return
            elif command_check.startswith("queenpenguin"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Queen of Penguins.. Who'm cannot fly", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("queenpenguin command", f)
                    return
            elif command_check.startswith("rageflip"):
                try:
                    await bot.send_chat_message(streamer.id, streamer.id, f"┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("rageflip command", f)
                    return
            elif command_check.startswith("ronin"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"RoninGT, his Pettiness, thee Royal Leader of The Petty Squad. https://discord.gg/pettysquad", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("ronin command", f)
                    return
            elif command_check.startswith("rubi"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "Shine bright like a dia... RUBI!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("rubi command", f)
                    return
            elif command_check.startswith(("sarah", "rexarah", "fuckinggiggity", "giggity", "rawr")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "rexara1Giggity rexara1Wink rexara1Giggity rexara1Wink", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("sarah command", f)
                    return
            elif command_check.startswith(("shat", "shathiris")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Guess who's back back back.. Back again gain gain.. TheeShat is back back back... {data.event.broadcaster_user_name} better RUN RUN RUN!!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("shat command", f)
                    return
            elif command_check.startswith(("shit", "holyshit", "unholyshit")):
                try:
                    if command_check.startswith("shit"):
                        response_shit = f"What Thee Shit!??!"
                    elif command_check.startswith("holyshit"):
                        response_shit = f"Holy Trucking Shit!!!!"
                    else:
                        response_shit = f"Thee UnHoliest Of ALLLL UnHoly SHIT!!!"
                    await bot.send_chat_message(id_streamer, id_streamer, f"{response_shit} eh?", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("shit command", f)
                    return
            elif command_check.startswith("silencer"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name} be sneaky like silencer56", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("silencer command", f)
                    return
            elif command_check.startswith("toodles"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "TTTOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOODDDDDDDDDDDDDDDLLLLLLLLLLLLLLEEEEEEEEEEEESSSSSSSSSSSSSSSSSSSSSSSSSS", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("toodles command", f)
                    return
            elif command_check.startswith("vanish"):
                try:
                    await bot.ban_user(id_streamer, id_streamer, chatter_id, f"{chatter_username} vanishes", 1)
                    if chatter_id in channel_document['data_lists']['mods']:
                        await asyncio.sleep(2)
                        await bot.add_channel_moderator(id_streamer, chatter_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("vanish command", f)
                    return
            elif command_check.startswith("whoudini"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Whoooo.. Whoooooo... Whoooooooooooooooooooooooooooo", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("whoudini command", f)
                    return
            elif command_check.startswith("willsmash"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Hul... Will Smash!!", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("willsmash command", f)
                    return
            # Mod Commands
            elif command_check.startswith("resetobs") and (chatter_id in channel_document['data_lists']['mods'] or chatter_id == id_streamer):
                try:
                    change_colour_eq("Reset")
                    await change_webcam("reset")
                    await bot.send_chat_message(id_streamer, id_streamer, f"OBS filters reset to default values", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("resetobs command", f)
                    return
            elif command_check.startswith("shutdown") and (chatter_id in channel_document['data_lists']['mods'] or chatter_id == id_streamer):
                try:
                    logger.info(f"{fortime()}: {data.event.chatter_user_name} is attempting to shut me down!! {data.event.message.text}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Attempting to shut down", reply_parent_message_id=data.event.message_id)
                    obs.disconnect()
                    sys._exit(666)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("shutdown command", f)
                    return
            # Un-Listed Commands ToDo: Add check for adding time, if one is in jail, they don't get points
            elif command_check.startswith("addtime") and chatter_id in (id_streamer, id_streamloots):
                try:
                    points, success = None, None
                    if not channel_document['data_channel']['writing_clock']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Writing to clock is currently disabled", reply_parent_message_id=data.event.message_id)
                        end_timer("addtime command")
                        return
                    time_value = command.replace(" ", "").replace("addtime", "")
                    if "packfrom" in time_value or "packsfrom" in time_value:
                        """$addtime {{username}} bought {{quantity}} packs from {{collectionName}}"""
                        name, coll_name = time_value.split("bought", maxsplit=1)
                        quantity, coll_name = coll_name.split("from", maxsplit=1)
                        if coll_name != marathon_name.lower():
                            logger.error(f"{fortime()}: {coll_name}, {type(coll_name)}, Collection name doesn't match {marathon_name.lower()}")
                            end_timer("addtime command")
                            return
                        if quantity.endswith("s"):
                            quantity = quantity.removesuffix("packs")
                        else:
                            quantity = quantity.removesuffix("pack")
                        if not quantity.isdigit():
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- addtime command -- packsfrom - quantity isn't a int -- {quantity} {type(quantity)}")
                            end_timer("addtime command")
                            return
                        time_add = int(quantity) * ((stream_loots_seconds * 100) * stream_loots_pack_quantity)
                    elif "hasgifted" in time_value:
                        """$addtime {{gifterUsername}} has gifted {{quantity}} to {{gifteeUsername}}"""
                        name, quantity = time_value.split("hasgifted", maxsplit=1)
                        quantity, _ = quantity.split("to", maxsplit=1)
                        if not quantity.isdigit():
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- addtime command -- hasgifted - quantity isn't a int -- {quantity} {type(quantity)}")
                            end_timer("addtime command")
                            return
                        time_add = int(quantity) * ((stream_loots_seconds * 100) * stream_loots_pack_quantity)
                    elif "by" in time_value:
                        time_value, name = time_value.split("by", maxsplit=1)
                        name, _ = name.split("via")
                        if not time_value.isdigit():
                            logger.error(f"{fortime()}: {time_value}, {type(time_value)}, not valid")
                            end_timer("addtime command")
                            return
                        time_add = float(time_value)
                    else:
                        # time_value, name = time_value.split("by", maxsplit=1)
                        # name, _ = name.split("via")
                        # if not time_value.isdigit():
                        #     logger.error(f"{fortime()}: {time_value}, {type(time_value)}, not valid")
                        #     end_timer("addtime command")
                        #     return
                        # time_add = float(time_value)
                        if time_value.isdigit():
                            name = chatter_username
                            time_add = float(time_value)
                        else:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- addtime command -- else block -- time_value is NOT digit")
                            return
                    if channel_document['data_channel']['hype_train']['current']:
                        time_add = check_hype_train(channel_document, time_add)
                    seconds, time_not = write_clock(time_add, logger, True, obs)
                    if name != "community^":
                        chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                        if success is None:
                            points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                    else:
                        name = name.rstrip("^")
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'} Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}", reply_parent_message_id=data.event.message_id)
                    special_logger.info(f"timeadded -- {datetime.timedelta(seconds=int(seconds))} -- {seconds} by {name}{f' -- MAX TIME HIT {time_not} not added.' if time_not is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                except Exception as f:
                    error_command("addtime command", f)
                    return
            elif command_check.startswith("cuss") and chatter_id in (streamer.id, id_streamloots):
                """$cuss time_value by {{username}}: Msg Here"""
                try:
                    if not channel_document['data_channel']['writing_clock']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Writing to clock is currently disabled", reply_parent_message_id=data.event.message_id)
                        end_timer("cuss command")
                        return
                    command = command.removeprefix("cuss ")
                    time_value, name = command.split(" by ", maxsplit=1)
                    time_value = int(time_value)
                    if ':' in name:
                        name, _ = name.split(":", maxsplit=1)
                    if channel_document['data_channel']['hype_train']['current']:
                        time_value = check_hype_train(channel_document, time_value)
                    time_cuss_total = write_clock_cuss(time_value)
                    set_timer_cuss(obs, time_cuss_total)
                    obs.set_source_visibility(obs_timer_scene, obs_timer_cuss, True)
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, time_value)
                    if success is None:
                        points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                    else:
                        points = None
                    await bot.send_chat_message(streamer.id, streamer.id, f"{name} {f'added {str(datetime.timedelta(seconds=time_value)).title()} to thee No Cuss Timer, total of' if time_cuss_total != time_value else 'is starting the No Cuss Timer for'} {str(datetime.timedelta(seconds=time_cuss_total)).title()}! Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command(f"cuss command", f)
                    return
            elif command_check.startswith("cardlube") and chatter_id in (streamer.id, id_streamloots):
                """$cardlube time_value by {{username}}: Msg Here"""
                try:
                    command = command.removeprefix("cardlube ")
                    if not channel_document['data_channel']['writing_clock']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Writing to clock is currently disabled", reply_parent_message_id=data.event.message_id)
                        end_timer("cardlube command")
                        return
                    time_value, name = command.split(" by ", maxsplit=1)
                    time_value = float(time_value)
                    if ':' in name:
                        name, _ = name.split(":", maxsplit=1)
                    if not channel_document['data_channel']['hype_train']['current']:
                        time_value = check_hype_train(channel_document, time_value)
                    time_lube_total = write_clock_lube(time_value)
                    set_timer_lube(obs, time_lube_total)
                    obs.set_source_visibility(obs_timer_scene, obs_timer_lube, True)
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, time_value)
                    if success is None:
                        points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                    else:
                        points = None
                    await bot.send_chat_message(streamer.id, streamer.id, f"{name} {f'added {str(datetime.timedelta(seconds=time_value)).title()} to thee Lube Timer, total of' if time_lube_total != time_value else 'is starting Thee Lube Timer for'} {str(datetime.timedelta(seconds=time_lube_total)).title()}! Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}", reply_parent_message_id=data.event.message_id)
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command(f"cardlube command", f)
                    return
            elif command_check.startswith("remtime") and chatter_id in (id_streamer, id_streamloots):
                try:
                    points, success = None, None
                    time_value = command.replace(" ", "").replace("remtime", "")
                    time_value, name = time_value.split("by", maxsplit=1)
                    name, _ = name.split("via", maxsplit=1)
                    if not time_value.isdigit():
                        print(time_value, type(time_value), "not valid")
                        return
                    time_rem = float(time_value)
                    if channel_document['data_channel']['hype_train']['current']:
                        time_rem = check_hype_train(channel_document, time_rem)
                    seconds, time_not = write_clock(time_rem, logger, False, obs)
                    if name != "community^":
                        chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                        if success is None:
                            points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                    else:
                        name = name.rstrip("^")
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} removed {datetime.timedelta(seconds=int(seconds))} from thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'} Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}", reply_parent_message_id=data.event.message_id)
                    special_logger.info(f"timeadded -- {datetime.timedelta(seconds=int(seconds))} -- {seconds} by {chatter_username}{f' -- MAX TIME HIT {time_not} not added.' if time_not is not None else ''}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("remtime command", f)
                    return
            elif command_check.startswith("changerate") and chatter_id in (id_streamer, id_streamloots):
                """$changerate (accel/slow/norm)-new_rate by {{username}} for time_here via StreamLoots Card. {{message}}"""
                try:
                    phase = command.replace("changerate", "")
                    phase, name = phase.split(" by ", maxsplit=1)
                    phase, new_rate = phase.split("-", maxsplit=1)
                    name, last_time = name.split(" for ", maxsplit=1)
                    last_time, _ = last_time.split(" via ", maxsplit=1)
                    phase = phase.replace(" ", "")
                    new_rate = new_rate.replace(" ", "")
                    name = name.replace(" ", "")
                    last_time = last_time.replace(" ", "")
                    if phase not in ("accel", "slow", "norm"):
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- phase couldn't be identified -- '{phase}' {type(phase)}")
                        return
                    if not new_rate.isdigit:
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- new_rate couldn't be identified -- '{new_rate}' {type(new_rate)}")
                        return
                    if not last_time.isdigit():
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- last_time couldn't be identified -- '{last_time}' {type(last_time)}")
                        return
                    last_time, new_rate = float(last_time), float(new_rate)
                    if channel_document['data_channel']['hype_train']['current']:
                        last_time = check_hype_train(channel_document, last_time)
                    if phase == "accel":
                        write_clock_phase(phase)
                        new_time = write_clock_time_phase_accel(last_time)
                    elif phase == "slow":
                        # if float(read_clock_time_phase_slow()) == 0:
                        #     write_clock_phase_slow_rate(countdown_rate_strict)
                        write_clock_phase(phase)
                        new_time = write_clock_time_phase_slow(float(last_time))
                    elif phase == "norm":
                        write_clock_phase(phase)
                        obs.set_source_visibility(obs_timer_scene, obs_timer_rate, False)
                        response_changerate = f"{name} has set Thee Timer Rate to Normal; 1 Real Sec/1 Timer Sec"
                        special_logger.info(f"{fortime()}: {response_changerate}")
                        await bot.send_chat_message(id_streamer, id_streamer, response_changerate)
                        end_timer("changerate command -- normal phase")
                        return
                    else:
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- phase isn't accel/slow/norm -- {phase}, {type(phase)}....")
                        end_timer("changerate command -- error phase read")
                        return
                    set_timer_rate(obs, phase)  #, new_time)
                    obs.set_source_visibility(obs_timer_scene, obs_timer_rate, True)
                    last_time, new_rate = last_time, new_rate
                    points_add = last_time * new_rate
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, points_add)
                    response_changerate = f"{name} has set Thee Timer Rate to; {int(new_rate) if phase == 'slow' else '1'} Real Sec/{'1' if phase == 'slow' else int(new_rate)} Timer Sec for; {str(datetime.timedelta(seconds=last_time)).title()}.{f' {str(datetime.timedelta(seconds=new_time)).title()} now remaining.' if new_time != last_time else ''}"
                    special_logger.info(f"{fortime()}: {response_changerate}")
                    if success is None:
                        points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                    else:
                        points = None
                    await bot.send_chat_message(id_streamer, id_streamer, f"{response_changerate} Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("changerate command", f)
                    return
            elif command_check.startswith("pausetime") and chatter_id in (id_streamer, id_streamloots):
                """$pausetime x_second by user_name via StreamLoots Card"""
                try:
                    time_value = command.replace("pausetime", "")
                    time_value, name = time_value.split(" by ", maxsplit=1)
                    name, _ = name.split(" via ", maxsplit=1)
                    time_value = time_value.replace(" ", "")
                    name = name.replace(" ", "")
                    if not time_value.isdigit():
                        special_logger.error(f"{fortime()}: PAUSE TIME WAS ATTEMPTED BUT FAILED!!!!!!!!! -- paused for {time_value, type(time_value)} by {name}")
                        return
                    time_pause = float(time_value)
                    if channel_document['data_channel']['hype_train']['current']:
                        time_pause = check_hype_train(channel_document, time_pause)
                    total_pause = write_clock_pause(time_pause)
                    set_timer_pause(obs, True)
                    special_logger.info(f"{name} paused thee timer for {time_pause}")
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, time_pause)
                    if success is None:
                        points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                    else:
                        points = None
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} paused thee timer for {str(datetime.timedelta(seconds=time_pause)).title()}.{f' Timer paused for a total of {str(datetime.timedelta(seconds=int(total_pause))).title()}.' if time_pause != total_pause else ''} Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("pausetime command", f)
                    return
            elif command_check.startswith("directtime") and chatter_id in (id_streamer, id_streamloots):
                """$directtime x_seconds by chatter_name via StreamLoots Card"""
                try:
                    time_value = command.replace("directtime", "")
                    time_value, name = time_value.split(" by ", maxsplit=1)
                    name, origin = name.split(" via ", maxsplit=1)
                    time_value = time_value.replace(" ", "")
                    if not time_value.isdigit():
                        special_logger.error(f"{fortime()}: DIRECTION TIME WAS ATTEMPTED BUT FAILED!!!!!!!!! -- direction time for {time_value, type(time_value)} by {name}")
                        return
                    time_value = float(time_value)
                    if channel_document['data_channel']['hype_train']['current']:
                        time_value = check_hype_train(channel_document, time_value)
                    old_value = float(read_clock_up_time())
                    total_direct_time = write_clock_up_time(time_value)
                    with open(clock_mode, "w") as file:
                        file.write("up")
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, time_value)
                    special_logger.info(f"{fortime()}: Count Up -- Old Value; {old_value} -- New Value; {total_direct_time} -- By; {name} -- Via; {origin}")
                    set_timer_count_up(obs, total_direct_time)
                    obs.set_source_visibility(obs_timer_scene, obs_timer_countup, True)
                    if success is None:
                        points = f"{numberize(chatter_document['data_user']['rank']['points'])}."
                    else:
                        points = None
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} {f'made thee timer count UP for {datetime.timedelta(seconds=time_value)}' if time_value == total_direct_time else f'added {datetime.timedelta(seconds=time_value)} to thee timer counting UP. Total time left {datetime.timedelta(seconds=total_direct_time)}'}. Your new points are; {points if points is not None else f' {success}' if success is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("directtime command", f)
                    return
            elif command_check.startswith("addlurk") and chatter_id == id_streamer:
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    target_username = command.replace(" ", "").replace("addlurk@", "")
                    target_id = None
                    users = users_collection.find({})
                    for user in users:
                        if user['name'].lower() == target_username:
                            target_id = user['_id']
                            break
                    if target_id is not None:
                        if str(target_id) not in channel_document['data_lists']['lurk']:
                            channel_document['data_lists']['lurk'].append(str(target_id))
                            channel_document.save()
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target_username} has been forced into thee shadows by {data.event.broadcaster_user_name} himself")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("addlurk command", f)
                    return
            elif command_check.startswith("clearlists") and chatter_id == id_streamer:
                try:
                    channel_document['data_lists'].update(lurk=[], non_tag=[])
                    channel_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"Lurk and Non-Tag List cleared")
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("clearlists command", f)
                    return
            # elif command_check.startswith("rtag") and chatter_id == id_streamer:  # ToDo: Connect This To NEW Data Structure
            #     try:
            #         response_rtag = None
            #         if channel_document['data_games']['tag'][2] is not None:
            #             if channel_document['data_games']['tag'][0] not in channel_document['data_lists']['non_tag']:
            #                 channel_document['data_lists']['non_tag'].append(channel_document['data_games']['tag'][0])
            #                 response_rtag = f"{channel_document['data_games']['tag'][1]} has been moved to thee untag list"
            #         channel_document['data_games'].update(tag=[None, None, None])
            #         channel_document.save()
            #         await bot.send_chat_message(id_streamer, id_streamer, f"Tag game reset{f', {response_rtag}' if response_rtag is not None else '.'}")
            #     except TwitchBackendException:
            #         await twitch_backend()
            #         return
            #     except Exception as f:
            #         error_command("tagreset command", f)
            #         return
            elif command_check.startswith("test") and chatter_id == id_streamer:
                try:
                    pass
                    # print(obs.get_sound_alert("TheeIntroVid1"))
                    # print(obs.get_input_kind_list())
                    # print(obs.get_scene_items("TheeIntro"))
                    # print(obs.get_input_settings("AlertAudio"))
                    # print(obs.set_source_visibility("TheeIntro", "AlertAudio", False))
                    # print(obs.set_input_settings("AlertAudio", {"local_file": f"{alerts}half_bastard.mp3"}))
                    # print(obs.set_source_visibility("TheeIntro", "AlertAudio", True))
                    # print("sleep")
                    # await asyncio.sleep(30)
                    # print(obs.set_source_visibility("TheeIntro", "AlertAudio", False))
                    # print(obs.set_input_settings("AlertAudio", {"local_file": f"{alerts}beep.wav"}))
                    # print(obs.set_source_visibility("TheeIntro", "AlertAudio", True))
                    # print("sleep")
                    # await asyncio.sleep(30)
                    # print(obs.set_source_visibility("TheeIntro", "AlertAudio", False))
                    # print(obs.set_input_settings("AlertAudio", {"local_file": f"{alerts}hype_train.mp3"}))
                    # print(obs.set_source_visibility("TheeIntro", "AlertAudio", True))
                    # print(obs.get_input_settings("AlertAudio"))
                except TwitchBackendException:
                    await twitch_backend()
                    return
                except Exception as f:
                    error_command("test", f)
                    return
            end_timer(f"{command} command")
        else:
            phrase_del = False
            messagecont = data.event.message.text.replace(" ", "").lower()
            try:
                with open(bot_delete_phrases, "r") as file:
                    delete_phrases = list(map(str, file.read().splitlines()))
                for phrase in delete_phrases:
                    if messagecont.startswith(phrase):
                        await bot.delete_chat_message(id_streamer, id_streamer, data.event.message_id)
                        if chatter_id in channel_document['data_lists']['spam']:
                            await bot.ban_user(id_streamer, id_streamer, chatter_id, f"Bot Spam -- {data.event.message.text}")
                        else:
                            channel_document['data_lists']['spam'].append(chatter_id)
                            channel_document.save()
                        phrase_del = True
                        break
            except Exception as f:
                logger.error(f"{fortime()}: Error in on_stream_chat_message - phrases_loop -- {f}")
                pass
            try:
                if channel_document['data_games']['ranword'] in messagecont:
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, 10000)
                    response_ranword = f"You used thee random word!! It was {channel_document['data_games']['ranword']}. You gained 10,000 points!"
                    channel_document = await ran_word(channel_document)
            except Exception as f:
                logger.error(f"{fortime()}: Error in on_stream_chat_message -- ranword_bit -- {f}")
                pass
            try:
                if not phrase_del:
                    if response_level is not None:
                        old_response_level = response_level
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, standard_points)
                    if response_level is None and old_response_level is not None:
                        response_level = old_response_level
                chat_logger.info(f"{chatter_id}/{chatter_username}: {data.event.message.text if data.event.message_type in ('text', 'power_ups_message_effect') else f'Last message was a type({data.event.message_type}) not a text type.'}")
            except Exception as f:
                logger.error(f"{fortime()}: Error in on_stream_chat_message -- twitch_points -- {f}")
                pass
        response_spec_msg = None
        if data.event.message_type.startswith("power_ups") and channel_document['data_channel']['writing_clock']:  # power_ups_message_effect, power_ups_gigantified_emote
            special_logger.info(f"Special Message -- {data.event.message_type}")
            try:
                if data.event.message_type == "power_ups_message_effect":
                    bits = 25
                elif data.event.message_type == "power_ups_gigantified_emote":
                    bits = 50
                elif data.event.message_type == "power_ups_onscreen_celebration":
                    bits = 75
                else:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- power_ups bits -- {data.event.message_type} {type(data.event.message_type)}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Unable to identify # of bits..")
                    return
                seconds = bits * standard_seconds
                if channel_document['data_channel']['hype_train']['current']:
                    seconds = check_hype_train(channel_document, seconds)
                seconds, not_added = write_clock(seconds, logger, True, obs)
                response_spec_msg = f"{chatter_username} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f' -- MAX TIME HIT {not_added} to thee clock' if not_added is not None else ''} {response_thanks}"
                special_logger.info(response_spec_msg)
            except Exception as f:
                logger.error(f"{fortime()}: Error in on_stream_chat_message -- power_ups -- {f}")
                end_timer("power_ups")
                return
        if response_spec_msg is not None or response_ranword is not None or response_level is not None:
            if response_level is not None and command is not None and response_spec_msg is None and response_ranword is None:
                end_timer("level up during command")
                return
            await bot.send_chat_message(id_streamer, id_streamer, f"{f'{response_ranword}.' if response_ranword is not None else ''} {f'{response_spec_msg}.' if response_spec_msg is not None else ''} {f'{response}.' if response is not None else ''} {f' {response_level}.' if response_level is not None else ''}", reply_parent_message_id=data.event.message_id)
        end_timer("on_stream_chat_message")
    except Exception as e:
        logger.error(f"{fortime()}: Error in on_stream_chat_message -- {e}\n\n\n{data}\n\n\n")
        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong in thee backend, error logged. Try again later", reply_parent_message_id=data.event.message_id)
        end_timer("main_exception")
        return


async def on_stream_chat_notification(data: ChannelChatNotificationEvent):
    """For Reference
    - sub
    - resub
    - sub_gift
    - community_sub_gift
    - gift_paid_upgrade
    - prime_paid_upgrade
    - raid
    - unraid
    - pay_it_forward
    - announcement
    - bits_badge_tier
    - charity_donation"""
    try:
        special_logger.info(f"CHAT_NOTIFICATION--Type - {data.event.notice_type}")
        if data.event.notice_type == "resub":
            streak = data.event.resub.streak_months
            special_logger.info(f"STREAK--CHECK--{streak}--Type--{type(streak)}")
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.chatter_user_name}{f' is on a {streak} month streak, and has been subscribed for a total of' if streak is not None or streak == 0 else 'has been subscribed for a total of'} {data.event.resub.cumulative_months} months. {response_thanks}")
        elif data.event.notice_type == "pay_it_forward":
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.chatter_user_name} is paying forward thee subbie gifted by {data.event.pay_it_forward.gifter_user_name} to {data.event.sub_gift.recipient_user_name}. {response_thanks}")
        elif data.event.notice_type == "bits_badge_tier":
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.chatter_user_name} just unlocked thee {data.event.bits_badge_tier.tier} bitties badge!! {response_thanks}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in on_stream_chat_notification -- {e}")
        return


async def on_stream_cheer(data: ChannelCheerEvent):
    try:
        points = 0
        response, response_level = "!", None
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if data.event.is_anonymous:
            chatter_username = "Anonymous"
        else:
            chatter_username = data.event.user_name
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = float((standard_points * data.event.bits) / 2)
                if channel_document['data_channel']['hype_train']['current']:
                    points_to_add = check_hype_train(channel_document, points_to_add)
                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
                channel_document['data_games']['gamble']['total'] += points_to_add
                channel_document.save()
                points = chatter_document['data_user']['rank']['points']
        if channel_document['data_channel']['writing_clock']:
            seconds = float(standard_seconds * data.event.bits)
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, logger, True, obs)
            response = f", adding {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!!{f' Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} has cheered {data.event.bits}{response}{f' You have {numberize(points)} {bot_name} Points' if points != 0 else ''}{f' {response_level}' if response_level is not None else ''} {response_thanks}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_cheer' -- {e}")
        return


async def on_stream_follow(data: ChannelFollowEvent):
    try:
        if read_bot_raid() == "False" or read_night_mode() == "False":
            response, response_level = "!", None
            channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
            if data.event.user_id not in channel_document['data_channel']['followers']:
                chatter_document = await get_chatter_document(data)
                if chatter_document is not None:
                    points_to_add = float((standard_seconds * follow_seconds) / 2)
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
                # if channel_document['data_channel']['writing_clock']:
                #     seconds, time_not_added = write_clock(follow_seconds, logger, True, channel_document, obs)
                #     response = f", adding {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!! {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}{f' {response_level}' if response_level is not None else ''{}"
                channel_document['data_channel']['followers'].append(data.event.user_id)
                channel_document.save()
                await bot.send_chat_message(id_streamer, id_streamer, f"Welcome {data.event.user_name} to Thee Chodeling's Nest{response} {response_thanks}{f'. {response_level}' if response_level is not None else ''}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_follow' -- {e}")
        return


async def on_stream_hype_begin(data: HypeTrainEvent):
    try:
        response = f""
        # try:
        #     ad_schedule = await bot.get_ad_schedule(id_streamer)
        #     ad_next_seconds, now_time_seconds = await get_ad_time(ad_schedule)
        #     ad_next = ad_next_seconds - now_time_seconds
        #     if ad_next <= 300:
        #         ad_attempt_snooze = await bot.snooze_next_ad(id_streamer)
        #         ad_next_seconds, now_time_seconds = await get_ad_time(ad_attempt_snooze)
        #         response = f" Attempting to snooze ad, hype train start - {ad_attempt_snooze.snooze_count} snooze's remaining. Next ad in: {datetime.timedelta(seconds=abs(ad_next_seconds - now_time_seconds))}."
        # except Exception as f:
        #     logger.error(f"{fortime()}: ERROR in on_stream_hype_begin -- ad_schedule shit -- {f}")
        #     pass
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if channel_document is None:
            await bot.send_chat_message(id_streamer, id_streamer, f"Error grabbing/creating channel document. Try again later")
            return
        if channel_document['data_channel']['writing_clock']:
            mult = check_hype_train(channel_document, None)
            set_hype_ehvent(obs, mult)
            response_writing_to_log = f"New Hype EhVent Level -- {mult:.1f}X -- {data.event.level} -- {response}"
        else:
            response_writing_to_log = f"Thee Hype Train ENABLED -- {data.event.level} level"
        special_logger.info(response_writing_to_log)
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Choo Choooooooo!! Hype train started by {data.event.last_contribution.user_name}{f', also triggering a Hype EhVent, increasing twitch contributions to thee clock!!' if channel_document['data_channel']['writing_clock'] else '!'}{response}", color="green")
        channel_document['data_channel']['hype_train'].update(current=True, current_level=data.event.level)
        channel_document.save()
    except TwitchBackendException:
        await asyncio.sleep(2)
        try:
            logger.warn(f"{fortime()}: TwitchBackendError -- InProcessHandlingHypeStart\n{long_dashes}\n{data}\n{long_dashes}")
            await bot.send_chat_message(id_streamer, id_streamer, f"TwitchBackendError -- HypeTrainLevelStart @{data.event.level}")
            pass
        except Exception as twitch_backend_fail:
            logger.error(f"{fortime()}: TwitchBackendError -- FAIL HANDLING -- {twitch_backend_fail}\n{long_dashes}\n{data}\n{long_dashes}")
            return
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_hype_begin' -- {e}")
        return


async def on_stream_hype_end(data: HypeTrainEndEvent):
    try:

        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if channel_document is None:
            await bot.send_chat_message(id_streamer, id_streamer, f"Error grabbing/creating channel document. Try again later")
            return
        if data.event.level > channel_document['data_channel']['hype_train']['record_level']:
            record_beat = True
            new_hype_train_record_level = data.event.level
        else:
            record_beat = False
            new_hype_train_record_level = channel_document['data_channel']['hype_train']['record_level']
        top_post = []
        top_contributors = data.event.top_contributions
        special_logger.info(f"{fortime()}:HypeTrainEnd TopContributors -- {len(top_contributors)}")
        for n, user in enumerate(top_contributors):
            top_post.append(f"{n+1}: {user.user_name}: {user.type}; {user.total}")
            special_logger.info(f"{fortime()}: {user.user_id}, {user.user_name}, {user.user_login}, {user.type}, {user.total}")
        special_logger.info(f"Thee Hype EhVent DISABLED" if channel_document['data_channel']['writing_clock'] else f"Hype Train Ended")
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Hype Train Completed @ {data.event.level}!! Top Contributors; {' | '.join(top_post)}{f' New local record reached at {new_hype_train_record_level}!!' if record_beat else ''}{f' Thee Hype EhVent is now over, all contributions to thee clock have returned to normal.' if channel_document['data_channel']['writing_clock'] else ''} {response_thanks}", color="orange")
        channel_document['data_channel']['hype_train'].update(current=False, current_level=1, last=fortime(), last_level=data.event.level, record_level=new_hype_train_record_level)
        channel_document.save()
        if channel_document['data_channel']['writing_clock']:
            set_hype_ehvent(obs, standard_ehvent_mult, "Disabled")
    except TwitchBackendException:
        await asyncio.sleep(2)
        try:
            logger.warn(f"{fortime()}: TwitchBackendError -- InProcessHandlingHypeEnd\n{long_dashes}\n{data}\n{long_dashes}")
            await bot.send_chat_message(id_streamer, id_streamer, f"TwitchBackendError -- HypeTrainEnded @ Level {data.event.level}")
            pass
        except Exception as twitch_backend_fail:
            logger.error(f"{fortime()}: TwitchBackendError -- FAIL HANDLING -- {twitch_backend_fail}\n{long_dashes}\n{data}\n{long_dashes}")
            return
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_hype_end' -- {e}")
        return


async def on_stream_hype_progress(data: HypeTrainEvent):
    try:
        response = f""
        # try:
        #     ad_schedule = await bot.get_ad_schedule(id_streamer)
        #     ad_next_seconds, now_time_seconds = await get_ad_time(ad_schedule)
        #     ad_next = ad_next_seconds - now_time_seconds
        #     if ad_next <= 300:
        #         ad_attempt_snooze = await bot.snooze_next_ad(id_streamer)
        #         ad_next_seconds, now_time_seconds = await get_ad_time(ad_attempt_snooze)
        #         response = f" Attempting to snooze ad, hype train Progress - {ad_attempt_snooze.snooze_count} snooze's remaining. Next ad in: {datetime.timedelta(seconds=abs(ad_next_seconds - now_time_seconds))}."
        # except Exception as f:
        #     logger.error(f"{fortime()}: ERROR in on_stream_hype_progress -- ad_schedule shit -- {f}")
        #     pass
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if channel_document is None:
            await bot.send_chat_message(id_streamer, id_streamer, f"Error grabbing/creating channel document. Try again later")
            return
        if data.event.level > channel_document['data_channel']['hype_train']['current_level']:
            new_hype_train_current_level = data.event.level
            # special_logger.info(f"New Hype Train Level!! Currently @ {data.event.level}.{response}")
            channel_document['data_channel']['hype_train'].update(current_level=new_hype_train_current_level)
            channel_document.save()
            if channel_document['data_channel']['writing_clock']:
                mult = check_hype_train(channel_document, None)
                set_hype_ehvent(obs, mult)
                response_writing_to_log = f"New Hype EhVent Level -- {mult:.1f}X -- {data.event.level} -- {response}"
            else:
                response_writing_to_log = f"New Hype Train Level!! Currently @ {data.event.level} -- {response}"
            await bot.send_chat_announcement(id_streamer, id_streamer, f"New Hype Train Level!! Currently @ {data.event.level}.{response}", color="purple")
        else:
            response_writing_to_log = f"New Hype Train Level!! Currently @ {data.event.level} -- {response}"
            new_hype_train_current_level = channel_document['data_channel']['hype_train']['current_level']
        special_logger.info(f"{response_writing_to_log}, {new_hype_train_current_level}")
        # channel_document['data_channel']['hype_train'].update(current_level=new_hype_train_current_level)
        # channel_document.save()
    except TwitchBackendException:
        await asyncio.sleep(2)
        try:
            logger.warn(f"{fortime()}: TwitchBackendError -- InProcessHandlingHypeProgress\n{long_dashes}\n{data}\n{long_dashes}")
            await bot.send_chat_message(id_streamer, id_streamer, f"TwitchBackendError -- HypeTrainLevel @{data.event.level}")
            pass
        except Exception as twitch_backend_fail:
            logger.error(f"{fortime()}: TwitchBackendError -- FAIL HANDLING -- {twitch_backend_fail}\n{long_dashes}\n{data}\n{long_dashes}")
            return
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_hype_progress' -- {e}")
        return


async def on_stream_poll_begin(data: ChannelPollBeginEvent):
    try:
        choices = []
        for n, choice in enumerate(data.event.choices):
            choices.append(f"{n+1}: {choice.title}")
        time_till_end = await get_long_sec(fortime_long(data.event.ends_at.astimezone()))
        seconds_now = await get_long_sec(fortime_long(datetime.datetime.now()))
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Poll '{data.event.title}' has started. Choices are: {' - '.join(choices)}. Poll will end in {datetime.timedelta(seconds=abs(time_till_end - seconds_now))}. Voting with extra channel points is {'enabled' if data.event.channel_points_voting.is_enabled else 'disabled'}", color="green")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_poll_begin' -- {e}")
        return


async def on_stream_poll_end(data: ChannelPollEndEvent):
    try:
        if data.event.status != "completed":
            return
        choices = []
        for choice in data.event.choices:
            choices.append([choice.votes, choice.title])
        choices_sorted = sorted(choices, key=lambda choice: choice[0], reverse=True)
        winner = choices_sorted[0]
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Poll '{data.event.title}' has ended. Thee winner is: {winner[1].title()} with {winner[0]} votes!", color="orange")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_poll_end' -- {e}")
        return


async def on_stream_point_redemption(data: ChannelPointsCustomRewardRedemptionAddEvent):
    try:
        data.event.to_dict()
        chatter_username = data.event.user_name
        check_in, multiple_spin = True, False
        response_redemption, response_check_in, times_spun = None, None, None
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        chatter_document = await get_chatter_document(data)
        special_logger.info(f"fin--RewardID: {data.event.reward.id} -- {data.event.reward.title}")
        if data.event.reward.title == "Text-to-Speech":
            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} used Text-To-Speech to say; {data.event.user_input}")
            return
        elif data.event.reward.title == "Daily Check-In":
            chatter_document = await get_chatter_document(data, channel_document)
            response_boost, now_time = None, datetime.datetime.now()
            if chatter_document['data_user']['dates']['checkin_streak'][1] is None: pass
            elif now_time.day == chatter_document['data_user']['dates']['checkin_streak'][1].day:
                if now_time.month == chatter_document['data_user']['dates']['checkin_streak'][1].month:
                    if now_time.year == chatter_document['data_user']['dates']['checkin_streak'][1].year:
                        check_in = False
                        response_check_in = f"check-ins are restricted to daily use! :P"
            if check_in:
                new_checkin_streak = chatter_document['data_user']['dates']['checkin_streak'][0] + 1
                if new_checkin_streak % 5 == 0:
                    new_boost = chatter_document['data_user']['rank']['boost'] + boost_checkin
                    response_boost = f"You now have {new_boost} boosted Experience Points!!"
                else:
                    new_boost = chatter_document['data_user']['rank']['boost']
                chatter_document['data_user']['rank'].update(boost=new_boost)
                chatter_document['data_user']['dates'].update(checkin_streak=[new_checkin_streak, now_time])
                chatter_document.save()
                response_check_in = f"check-in registered. Your next boost is in {abs(5 - new_checkin_streak % 5)} check-ins.{f' {response_boost}' if response_boost is not None else ''}"
        elif data.event.reward.title == "Add 10 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 600
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, logger, True, obs)
            chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, seconds)
            response_redemption = f"added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {numberize(data.event.reward.cost)} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''} You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!{f' {response_level}' if response_level is not None else ''}"
            channel_document['data_games']['gamble']['total'] += seconds / 4
            channel_document.save()
        elif data.event.reward.title == "Add 20 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 1200
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, logger, True, obs)
            chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, seconds)
            response_redemption = f"{chatter_username} added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {numberize(data.event.reward.cost)} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''} You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!{f' {response_level}' if response_level is not None else ''}"
            channel_document['data_games']['gamble']['total'] += seconds / 4
            channel_document.save()
        elif data.event.reward.title == "Add 30 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 1800
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, logger, True, obs)
            chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, seconds)
            response_redemption = f"added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {numberize(data.event.reward.cost)} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''} You now have {numberize(chatter_document['data_user']['rank']['points'])} {bot_name} Points!{f' {response_level}' if response_level is not None else ''}"
            channel_document['data_games']['gamble']['total'] += seconds / 4
            channel_document.save()
        elif data.event.reward.title.startswith("EQ Colour"):
            colour = data.event.reward.title.replace(" ", "").removeprefix("EQColour")
            change_colour_eq(colour)
        elif data.event.reward.title.startswith("Webcam Colour"):
            new_colour = data.event.reward.title.replace(" ", "").removeprefix("WebcamColour").title()
            await change_webcam("colour", new_colour=new_colour)
        elif data.event.reward.title == "Flip Me":
            await change_webcam("transform", new_transform="Flip")
        elif data.event.reward.title.startswith("Spin Me"):
            if data.event.reward.title.replace(" ", "").removeprefix("SpinMe").startswith("Multiple"):
                multiple_spin = True
            success, times_spun = await change_webcam("transform", new_transform="Spin", multiple_spin=multiple_spin)

        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} {response_check_in if response_check_in is not None else response_redemption if response_redemption is not None else f'used {numberize(data.event.reward.cost)} {channel_point_name} to redeem {data.event.reward.title}'}{f' {times_spun} times spun.' if multiple_spin else ''}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_point_redemption' -- {e}")
        return


async def on_stream_prediction_begin(data: ChannelPredictionEvent):
    try:
        outcomes = ""
        for n, outcome in enumerate(data.event.outcomes):
            outcomes += f"{n+1}: {outcome.title} - "
        time_till_end = await get_long_sec(fortime_long(data.event.locks_at.astimezone()))
        seconds_now = await get_long_sec(fortime_long(datetime.datetime.now()))
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Prediction '{data.event.title}' has started. Choices are: {outcomes[:-3]}. Prediction will end in {datetime.timedelta(seconds=time_till_end - seconds_now)}.", "purple")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_prediction_begin' -- {e}")
        return


async def on_stream_subbie(data: ChannelSubscribeEvent):
    try:
        if not data.event.is_gift:
            points = 0
            response_level = None
            channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
            sub_tier = await get_subbie_tier(data)
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = float((standard_seconds * sub_tier) / 2)
                if channel_document['data_channel']['hype_train']['current']:
                    points_to_add = check_hype_train(channel_document, points_to_add)
                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
                channel_document['data_games']['gamble']['total'] += points_to_add
                channel_document.save()
                points = chatter_document['data_user']['rank']['points']
            if channel_document['data_channel']['writing_clock']:
                seconds = float(standard_seconds * sub_tier)
                if channel_document['data_channel']['hype_train']['current']:
                    seconds = check_hype_train(channel_document, seconds)
                seconds, time_not_added = write_clock(seconds, logger, True, obs)
                response = f", adding {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!! {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
            else:
                response = '.'
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} subscribed to Thee Nest{response}{f' Your points are; {numberize(points)} {bot_name} Points' if points != 0 else ''}{f' {response_level}' if response_level is not None else ''} {response_thanks}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_subbie' -- {e}")
        return


async def on_stream_subbie_gift(data: ChannelSubscriptionGiftEvent):
    try:
        points = 0
        response, response_level = "", None
        sub_tier = await get_subbie_tier(data)
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if data.event.is_anonymous:
            user = "Anonymous"
            user_response = ""
        else:
            user = data.event.user_name
            user_response = f"Giving them a total of {data.event.cumulative_total} gifted subbies."
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = float(((standard_seconds * sub_tier) * data.event.total) / 2)
                if channel_document['data_channel']['hype_train']['current']:
                    points_to_add = check_hype_train(channel_document, points_to_add)
                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
                channel_document['data_games']['gamble']['total'] += points_to_add
                channel_document.save()
                points = chatter_document['data_user']['rank']['points']
        if channel_document['data_channel']['writing_clock']:
            seconds = float((standard_seconds * sub_tier) * data.event.total)
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, logger, True, obs)
            response = f" Added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!! {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        await bot.send_chat_message(id_streamer, id_streamer, f"{user} gifted out {data.event.total} {'subbie' if data.event.total == 1 else 'subbies'} to Thee Chodelings. {user_response}{response}{f' Your points are; {numberize(points)} {bot_name} Points' if points != 0 else ''}{f' {response_level}' if response_level is not None else ''} {response_thanks}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_subbie_gift' -- {e}")
        return


async def on_stream_raid_in(data: ChannelRaidEvent):
    try:
        if data.event.viewers > 1:
            response, response_level = "!!!", None
            channel_document = await get_channel_document(data.event.to_broadcaster_user_id, data.event.to_broadcaster_user_name, data.event.to_broadcaster_user_id)
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points = float((((raid_seconds / 4) * standard_seconds) * data.event.viewers) / 2)
                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points)
            # if channel_document['data_channel']['writing_clock']:
            #     seconds = float(raid_seconds * data.event.viewers)
            #     seconds, time_not_added = write_clock(seconds, logger, True, channel_document, obs)
            #     response = f" adding {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!!! {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''{}"
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.from_broadcaster_user_name} raid with {data.event.viewers} incoming{response} Go show them some love back y'all!{f' {response_level}' if response_level is not None else ''}")
            await bot.send_a_shoutout(id_streamer, data.event.from_broadcaster_user_id, id_streamer)
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_raid_in' -- {e}")
        return


async def on_stream_raid_out(data: ChannelRaidEvent):
    try:
        await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.from_broadcaster_user_name} has sent thee raid with {data.event.viewers} to https://twitch.tv/{data.event.to_broadcaster_user_name}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_raid_out' -- {e}")
        return


async def on_stream_update(data: ChannelUpdateEvent):
    try:
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if channel_document is None:
            logger.error(f"{fortime()}: ERROR: Channel Document is NONE!!! -- in on_stream_update")
            return
        if data.event.title != channel_document['channel_details']['title'] or data.event.category_id != channel_document['channel_details']['game_id']:
            response = []
            title_new, game_id_new, game_name_new = channel_document['channel_details']['title'], channel_document['channel_details']['game_id'], channel_document['channel_details']['game_name']
            if channel_document['channel_details']['title'] != data.event.title:
                response.append(f"Title Change to {data.event.title}")
                title_new = data.event.title
            if channel_document['channel_details']['game_id'] != data.event.category_id:
                response.append(f"Category Change to {data.event.category_name}")
                game_id_new = data.event.category_id
                game_name_new = data.event.category_name
                channel_document = await game_id_check(data.event.category_id, channel_document)
                if channel_document is None:
                    return
            channel_document['channel_details'].update(title=title_new, game_id=game_id_new, game_name=game_name_new)
            channel_document.save()
            await bot.send_chat_message(id_streamer, id_streamer, f"Channel Update: {' -- '.join(response)}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_update' -- {e}")
        return


async def on_stream_start(data: StreamOnlineEvent):
    try:
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if channel_document is not None:
            channel_info = await bot.get_channel_information(id_streamer)
            channel_mods = []
            async for mod in bot.get_moderators(id_streamer):
                channel_mods.append(mod.user_id)
            channel_document['channel_details'].update(online=True, branded=channel_info[0].is_branded_content, title=channel_info[0].title,
                                                       game_id=channel_info[0].game_id, game_name=channel_info[0].game_name,
                                                       content_class=channel_info[0].content_classification_labels, tags=channel_info[0].tags)
            channel_document['data_channel']['hype_train'].update(current=False, current_level=1)
            channel_document['data_lists'].update(mods=channel_mods)
            channel_document.save()
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Hola. I is here :D Big Chody Hugs.", color="green")
        if channel_document['data_channel']['writing_clock']:
            await bot.send_chat_message(id_streamer, id_streamer, f"{link_loots} | Monthly use 20% off coupon: {link_loots_discount}")
            with open("data/bot/pack_link", "r") as file:
                link = file.read()
            response_pack = list(map(str, link.splitlines()))
            for i in range(0, len(response_pack), 10):
                await bot.send_chat_message(id_streamer, id_streamer, " | ".join(response_pack[i:i + 10]))
                await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_start' -- {e}")
        return


async def on_stream_end(data: StreamOfflineEvent):
    try:
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if channel_document is not None:
            channel_document['channel_details'].update(online=False, online_last=datetime.datetime.now())
            channel_document.save()
        await bot.send_chat_announcement(id_streamer, id_streamer, f"I have faded into thee shadows. {response_thanks}", color="blue")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_end' -- {e}")
        return


def change_colour_eq(new_colour: str):
    try:
        success = True
        if new_colour == "Blue":
            obs.set_filter_visibility("TheeEQ", "MAGENTA", False)
            obs.set_filter_visibility("TheeEQ", "RED", False)
            obs.set_filter_visibility("TheeEQ", "REDBOOST", False)
            obs.set_filter_visibility("TheeEQ", "GREEN", False)
            obs.set_filter_visibility("TheeEQ", "GREENBOOST", False)
            obs.set_filter_visibility("TheeEQ", "BLUE", True)
            obs.set_filter_visibility("TheeEQ", "BLUEBOOST", True)
        elif new_colour in ("Green", "Reset"):
            obs.set_filter_visibility("TheeEQ", "MAGENTA", False)
            obs.set_filter_visibility("TheeEQ", "BLUE", False)
            obs.set_filter_visibility("TheeEQ", "BLUEBOOST", False)
            obs.set_filter_visibility("TheeEQ", "RED", False)
            obs.set_filter_visibility("TheeEQ", "REDBOOST", False)
            obs.set_filter_visibility("TheeEQ", "GREEN", True)
            obs.set_filter_visibility("TheeEQ", "GREENBOOST", True)
        elif new_colour == "Red":
            obs.set_filter_visibility("TheeEQ", "MAGENTA", False)
            obs.set_filter_visibility("TheeEQ", "BLUE", False)
            obs.set_filter_visibility("TheeEQ", "BLUEBOOST", False)
            obs.set_filter_visibility("TheeEQ", "GREEN", False)
            obs.set_filter_visibility("TheeEQ", "GREENBOOST", False)
            obs.set_filter_visibility("TheeEQ", "RED", True)
            obs.set_filter_visibility("TheeEQ", "REDBOOST", True)
        elif new_colour == "Magenta":
            obs.set_filter_visibility("TheeEQ", "RED", False)
            obs.set_filter_visibility("TheeEQ", "REDBOOST", False)
            obs.set_filter_visibility("TheeEQ", "BLUE", False)
            obs.set_filter_visibility("TheeEQ", "BLUEBOOST", False)
            obs.set_filter_visibility("TheeEQ", "GREEN", False)
            obs.set_filter_visibility("TheeEQ", "GREENBOOST", False)
            obs.set_filter_visibility("TheeEQ", "MAGENTA", True)
        elif new_colour == "White":
            obs.set_filter_visibility("TheeEQ", "MAGENTA", False)
            obs.set_filter_visibility("TheeEQ", "RED", False)
            obs.set_filter_visibility("TheeEQ", "REDBOOST", False)
            obs.set_filter_visibility("TheeEQ", "BLUE", False)
            obs.set_filter_visibility("TheeEQ", "BLUEBOOST", False)
            obs.set_filter_visibility("TheeEQ", "GREEN", False)
            obs.set_filter_visibility("TheeEQ", "GREENBOOST", False)
        else:
            success = False
        return success
    except Exception as e:
        logger.error(f"{fortime()}: Error in new_colour -- {e}")
        return False


async def change_webcam(webcam_manipulation: str, new_colour: str = "", new_transform: str = "", multiple_spin: bool = False):
    try:
        success, x = True, None
        if webcam_manipulation == "colour":
            if new_colour == "None":
                obs.set_filter_visibility("nvcam", "BLUE", False)
                obs.set_filter_visibility("nvcam", "GREEN", False)
                obs.set_filter_visibility("nvcam", "HIDDEN", False)
                obs.set_filter_visibility("nvcam", "MAGENTA", False)
                obs.set_filter_visibility("nvcam", "RED", False)
            elif new_colour == "Blue":
                obs.set_filter_visibility("nvcam", "GREEN", False)
                obs.set_filter_visibility("nvcam", "HIDDEN", False)
                obs.set_filter_visibility("nvcam", "MAGENTA", False)
                obs.set_filter_visibility("nvcam", "RED", False)
                obs.set_filter_visibility("nvcam", "BLUE", True)
            elif new_colour == "Green":
                obs.set_filter_visibility("nvcam", "BLUE", False)
                obs.set_filter_visibility("nvcam", "HIDDEN", False)
                obs.set_filter_visibility("nvcam", "MAGENTA", False)
                obs.set_filter_visibility("nvcam", "RED", False)
                obs.set_filter_visibility("nvcam", "GREEN", True)
            elif new_colour == "Hidden":
                obs.set_filter_visibility("nvcam", "BLUE", False)
                obs.set_filter_visibility("nvcam", "GREEN", False)
                obs.set_filter_visibility("nvcam", "MAGENTA", False)
                obs.set_filter_visibility("nvcam", "RED", False)
                obs.set_filter_visibility("nvcam", "HIDDEN", True)
            elif new_colour == "Magenta":
                obs.set_filter_visibility("nvcam", "BLUE", False)
                obs.set_filter_visibility("nvcam", "GREEN", False)
                obs.set_filter_visibility("nvcam", "HIDDEN", False)
                obs.set_filter_visibility("nvcam", "RED", False)
                obs.set_filter_visibility("nvcam", "MAGENTA", True)
            elif new_colour == "Red":
                obs.set_filter_visibility("nvcam", "BLUE", False)
                obs.set_filter_visibility("nvcam", "GREEN", False)
                obs.set_filter_visibility("nvcam", "HIDDEN", False)
                obs.set_filter_visibility("nvcam", "MAGENTA", False)
                obs.set_filter_visibility("nvcam", "RED", True)
            else:
                success = False
        elif webcam_manipulation == "transform":
            old_style = obs.get_source_transform("NS-Cam", "nvcam")
            if new_transform.startswith("Flip"):
                if old_style['rotation'] == 180.0:
                    position_x = 788.0
                    position_y = 1700.0
                    rotation = 0.0
                    reset_position_x = 789.0
                    reset_position_y = 460.0
                    reset_rotation = 180.0
                else:
                    position_x = 789.0
                    position_y = 460.0
                    rotation = 180.0
                    reset_position_x = 788.0
                    reset_position_y = 1700.0
                    reset_rotation = 0.0
                obs.set_source_transform("NS-Cam", "nvcam", {"positionX": position_x, "positionY": position_y, "rotation": rotation})
                await asyncio.sleep(60)
                obs.set_source_transform("NS-Cam", "nvcam", {"positionX": reset_position_x, "positionY": reset_position_y, "rotation": reset_rotation})
            elif new_transform.startswith("Spin"):
                old_rotation = old_style["rotation"]
                if multiple_spin:
                    x = random.randint(2, 10)
                else:
                    x = 1
                for n in range(x):
                    new_rotation = old_rotation + 1
                    while new_rotation != old_rotation:
                        if new_rotation == 361.0:
                            new_rotation = 0.0
                            if new_rotation == old_rotation:
                                break
                        obs.set_source_transform("NS-Cam", "nvcam", {"rotation": new_rotation})
                        new_rotation += 1
                        await asyncio.sleep(0.00005)
                    obs.set_source_transform("NS-Cam", "nvcam", {"rotation": old_rotation})
                check_position = obs.get_source_transform("NS-Cam", "nvcam")
                if old_rotation == 0 and check_position["positionY"] == 460.0:
                    new_rotation = 1
                    old_rotation = 180
                    while new_rotation != old_rotation:
                        if new_rotation == 361.0:
                            new_rotation = 0.0
                            if new_rotation == old_rotation:
                                break
                        obs.set_source_transform("NS-Cam", "nvcam", {"rotation": new_rotation})
                        new_rotation += 1
                        await asyncio.sleep(0.00005)
                elif old_rotation == 180 and check_position["positionY"] == 1700:
                    new_rotation = 180
                    old_rotation = 1
                    while new_rotation != old_rotation:
                        if new_rotation == 361.0:
                            new_rotation = 0.0
                            if new_rotation == old_rotation:
                                break
                        obs.set_source_transform("NS-Cam", "nvcam", {"rotation": new_rotation})
                        new_rotation += 1
                        await asyncio.sleep(0.00005)
        elif webcam_manipulation == "reset":
            obs.set_source_transform("NS-Cam", "nvcam", {"positionX": 664.0, "positionY": 1726.0, "rotation": 0.0})
        else:
            success = False
        return success, x
    except Exception as e:
        logger.error(f"{fortime()}: Error in change_webcam -- {e}")
        return False


def connect_mongo(db, alias):
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


async def disconnect_mongo():
    try:
        disconnect_all()
        logger.info(f"{long_dashes}\nDisconnected from MongoDB")
    except Exception as e:
        logger.error(f"{fortime()}: Error Disconnection MongoDB -- {e}")
        return


def fortime_long(time: datetime):
    try:
        return str(time.strftime("%y:%m:%d:%H:%M:%S"))[1:]
    except Exception as e:
        logger.error(f"Error creating formatted_long_time -- {e}")
        return None


async def get_long_sec(time: datetime):
    try:
        y, mo, d, h, mi, s = time.split(":")
        return int(y) * 31536000 + int(mo) * 2628288 + int(d) * 86400 + int(h) * 3600 + int(mi) * 60 + int(s)
    except Exception as e:
        logger.error(f"Error creating long_second -- {e}")
        return None


async def game_id_check(game_id: str, channel_document: Document):
    try:
        streamer_id, streamer_name, streamer_login = channel_document['_id'], channel_document['user_name'], channel_document['user_login']
        if game_id == "488910":  # ATS CatID
            channel_document['data_counters'].update(ats=[0, 0])
        elif game_id == "1337444628":  # COD CatID
            channel_document['data_counters'].update(cod=[0, 0, 0, 0])
        else:
            return channel_document
        channel_document.save()
        return await get_channel_document(streamer_id, streamer_name, streamer_login)
    except Exception as e:
        logger.error(f"{fortime()}: Error in game_id_check -- {e}")
        return None


async def get_ad_time(ad_schedule):
    try:
        ad_next_seconds = await get_long_sec(fortime_long(ad_schedule.next_ad_at.astimezone()))
        now_time_seconds = await get_long_sec(fortime_long(datetime.datetime.now()))
        return ad_next_seconds, now_time_seconds
    except Exception as e:
        logger.error(f"Error returning short_ad_seconds -- {e}")
        return None, None


async def get_channel_document(b_id: str, name: str, login: str):
    try:
        try:
            channel_document = Channels.objects.get(_id=b_id)
        except Exception as f:
            if FileNotFoundError:
                try:
                    channel_collection = twitch_database.twitch.get_collection('channels')
                    new_channel_document = Channels(_id=b_id, user_name=name, user_login=login)
                    new_channel_document_dict = new_channel_document.to_mongo()
                    channel_collection.insert_one(new_channel_document_dict)
                    channel_document = Channels.objects.get(_id=b_id)
                    pass
                except Exception as g:
                    logger.error(f"{fortime()}: Error creating new document for channel -- {b_id}/{name}/{login} -- {g}")
                    return None
            else:
                logger.error(f"{fortime()}: Error fetching/creating channel document -- {b_id}/{name}/{login} -- {f}")
                return None
        return channel_document
    except Exception as e:
        logger.error(f"{fortime()}: Error in get_channel_document -- {b_id}/{name}/{login} -- {e}")
        return None


async def get_chatter_document(data: any = None, channel_document: Document = None, user_id: str = "", user_name: str = "", user_login: str = "", b_id: str = "", b_name: str = ""):  # Figure out why on_raid_in errors out on document creation...
    try:
        if data is None:
            broadcaster_id = b_id
            broadcaster_name = b_name
            chatter_id = user_id
            chatter_name = user_name
            chatter_login = user_login
        elif type(data) in (ChannelChatMessageEvent, ChannelChatNotificationEvent):
            broadcaster_id = data.event.broadcaster_user_id
            broadcaster_name = data.event.broadcaster_user_name
            chatter_id = data.event.chatter_user_id
            chatter_name = data.event.chatter_user_name
            chatter_login = data.event.chatter_user_login
        elif type(data) == ChannelRaidEvent:
            broadcaster_id = data.event.to_broadcaster_user_id
            broadcaster_name = data.event.to_broadcaster_user_name
            chatter_id = data.event.from_broadcaster_user_id
            chatter_name = data.event.from_broadcaster_user_name
            chatter_login = data.event.from_broadcaster_user_login
        else:
            broadcaster_id = data.event.broadcaster_user_id
            broadcaster_name = data.event.broadcaster_user_name
            chatter_id = data.event.user_id
            chatter_name = data.event.user_name
            chatter_login = data.event.user_login
        if channel_document is not None:
            if chatter_id in channel_document['data_lists']['ignore']:
                return None
        try:
            # if data is not None:
            chatter_document = Users.objects.get(_id=chatter_id)
            if chatter_document['name'] != chatter_name.lower():
                chatter_document['name'] = chatter_name.lower()
                chatter_document.save()
                chatter_document = Users.objects.get(_id=chatter_id)
            # else:
            #     chatter_document = Users.objects.get(_id=chatter_id)
        except Exception as f:
            if FileNotFoundError:
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    new_chatter_document = Users(_id=chatter_id, name=chatter_name.lower())
                    new_chatter_document_dict = new_chatter_document.to_mongo()
                    users_collection.insert_one(new_chatter_document_dict)
                    chatter_document = Users.objects.get(_id=chatter_id)
                    chatter_document['data_user'].update(id=chatter_id, login=chatter_login)
                    chatter_document['data_user']['dates'].update(first_chat=datetime.datetime.now())
                    chatter_document['data_user']['channel'].update(id=broadcaster_id, name=broadcaster_name)
                    chatter_document.save()
                    chatter_document = Users.objects.get(_id=chatter_id)
                    pass
                except Exception as g:
                    logger.error(f"{fortime()}: Error creating new document for user -- {chatter_id}/{chatter_name}/{chatter_login}\n{g}")
                    return None
            else:
                logger.error(f"{fortime()}: Error reading/creating new document for user -- {chatter_id}/{chatter_name}/{chatter_login}\n{f}")
                return None
        return chatter_document
    except Exception as e:
        logger.error(f"{fortime()}: Error in get_chatter_document -- Data Type -- {type(data)} -- {e}")
        return None


async def get_subbie_tier(data):
    try:
        if data.event.tier == "1000":
            return 250  # tier 1 subbie is == 250 bitties
        elif data.event.tier == "2000":
            return 500  # tier 2 subbie is == 500 bitties
        elif data.event.tier == "3000":
            return 1250  # tier 3 subbie is == 1250 bitties
        else:
            logger.error(f"{fortime()}: Error retrieving subbie tier -- {data.event.tier}")
            return 0
    except Exception as e:
        logger.error(f"{fortime()}: Error in get_subbie_tier -- {e}")
        return 0


async def ran_word(channel_document: Document):
    with open("data/bot/english", "r") as file:
        word_list = file.read()
    word_split = list(map(str, word_list.splitlines()))
    answer = random.choice(word_split)
    channel_document['data_games'].update(ranword=answer)
    channel_document.save()
    special_logger.info(f"Random Word = {answer}")
    return await get_channel_document(streamer.id, streamer.display_name, streamer.login)


async def select_target(channel_document, chatter_id, manual_choice: bool = False, target_user_name: str = "", game_type: str = "tag"):
    try:
        users = await bot.get_chatters(id_streamer, id_streamer)
        users_collection = twitch_database.twitch.get_collection('users')
        users_documents = users_collection.find({})
        valid_users = []
        for chatter_document in users_documents:
            if game_type == "fight" and chatter_document['data_user']['id'] in (streamer.id, id_streamloots):
                pass
            else:
                valid_users.append(str(chatter_document['data_user']['id']))
        if manual_choice:
            target = None
            for user in users.data:
                if user.user_name.lower() == target_user_name:
                    target = user
            if target is not None:
                if target.user_id not in valid_users:
                    target = None
        else:
            list_to_check = []
            if game_type == "tag":
                for entry in channel_document['data_lists']['lurk']:
                    if entry not in list_to_check:
                        list_to_check.append(entry)
                for entry in channel_document['data_lists']['non_tag']:
                    if entry not in list_to_check:
                        list_to_check.append(entry)
            while True:
                target = random.choice(users.data)
                special_logger.info(f"select_target_start {len(users.data)} {target.user_name} {target.user_id}")
                if target.user_id in valid_users and target.user_id not in list_to_check:
                    if chatter_id != target.user_id:
                        special_logger.info(f"select_target_chose {len(users.data)} {target.user_name} {target.user_id}")
                        break
                users.data.remove(target)
                special_logger.info(f"select_target_remove {len(users.data)} {target.user_name} {target.user_id}")
                if len(users.data) <= 1:
                    target = None
                    if game_type not in ("tag", "fight"):
                        await bot.send_chat_message(id_streamer, id_streamer, f"Error fetching random target... Are we thee only ones here?")
                    special_logger.info(f"select_target_none total:{users.total} list_to_check:{len(list_to_check)} ignore_list:{len(channel_document['data_lists']['ignore'])} -- dif:{abs(users.total - len(list_to_check)) - len(channel_document['data_lists']['ignore'])} -- game_type:{game_type}")
                    break
        return target
    except Exception as e:
        logger.error(f"Error selecting_target -- {e}")
        return None


async def twitch_points_transfer(chatter_document: Document, channel_document: Document, value: float, add: bool = True, gamble: bool = False):
    try:
        if chatter_document is not None:
            response_level = None
            if add and channel_document['data_channel']['hype_train']['current']:
                value = check_hype_train(channel_document, value)
            _id = chatter_document['_id']
            if not gamble:
                chatter_document, response_level = await xp_transfer(chatter_document, value, add)
            if add:
                chatter_document['data_user']['rank']['points'] += value
            else:
                chatter_document['data_user']['rank']['points'] -= value
            chatter_document['data_user']['dates']['latest_chat'] = datetime.datetime.now()
            chatter_document.save()
            chatter_document = Users.objects.get(_id=_id)
            return chatter_document, response_level
    except Exception as e:
        logger.error(f"{fortime()}: Error in twitch_points_transfer -- {chatter_document['_id']}/{chatter_document['name']}/{chatter_document['data_user']['login']} -- {e}")
        return None


async def update_tag_stats(chatter_document: Document, add_total: int, add_good: int, add_fail: int):
    response = None
    user_id = chatter_document['_id']
    chatter_document['data_games']['tag']['total'] += add_total
    chatter_document['data_games']['tag']['success'] += add_good
    chatter_document['data_games']['tag']['fail'] += add_fail
    if chatter_document['data_games']['tag']['success'] % 10 == 0 and add_good > 0:
        chatter_document['data_user']['rank']['boost'] += boost_tag
        new_boost = chatter_document['data_user']['rank']['boost']
        response = f"You have gained {boost_tag} boost points{f', your new total is {numberize(new_boost)}' if new_boost != boost_tag else ''}"
    chatter_document.save()
    chatter_document = Users.objects.get(_id=user_id)
    return chatter_document, response


async def xp_transfer(chatter_document, value: float, add: bool = True):
    try:
        break_value = 1000000
        response_level = None
        new_boost = chatter_document['data_user']['rank']['boost']
        user_id, user_name = chatter_document['_id'], chatter_document['name']
        new_user_level, start_user_level = chatter_document['data_user']['rank']['level'], chatter_document['data_user']['rank']['level']
        if add:
            value = value / 2
            if chatter_document['data_user']['rank']['boost'] > 0.0:
                if chatter_document['data_user']['rank']['boost'] > value:
                    boost_add = abs(chatter_document['data_user']['rank']['boost'] - (abs(chatter_document['data_user']['rank']['boost'] - value)))
                else:
                    boost_add = chatter_document['data_user']['rank']['boost']
                new_boost = chatter_document['data_user']['rank']['boost'] - boost_add
                value += boost_add
            new_user_xp_points = chatter_document['data_user']['rank']['xp'] + value
            x = 0
            while True:
                level_mult = 1.0
                if new_user_level > 1:
                    level_mult += float((new_user_level / 2) * new_user_level)
                xp_needed = (level_const * level_mult) * new_user_level
                special_logger.info(f"XP-INCREASE: {user_name} Level(XP): {new_user_level}({new_user_xp_points}) -- XP Needed: {xp_needed}")
                if new_user_xp_points >= xp_needed:
                    new_user_level += 1
                else:
                    break
                if x >= break_value:
                    special_logger.error(f"{fortime()}: breaking xp gain loop, something broke")
                    break
                x += 1
        else:
            new_user_xp_points = float(chatter_document['data_user']['rank']['xp'] - (value / 2))
            x = 0
            while True:
                level_mult = 1.0
                new_user_level_test = new_user_level - 1
                if new_user_level_test > 1:
                    level_mult += float((new_user_level_test / 2) * new_user_level_test)
                xp_needed = (level_const * level_mult) * new_user_level_test
                special_logger.info(f"XP-DECREASE: {user_name} Level(XP): {new_user_level}({new_user_xp_points}) -- XP Needed: {xp_needed}")
                if new_user_xp_points < xp_needed and new_user_level > 1:
                    new_user_level -= 1
                else:
                    break
                if x >= break_value:
                    special_logger.error(f"{fortime()}: breaking xp loss loop, something broke")
                    break
                x += 1
        chatter_document['data_user']['rank'].update(boost=new_boost, level=new_user_level, xp=new_user_xp_points)
        chatter_document.save()
        chatter_document = Users.objects.get(_id=user_id)
        if chatter_document['data_user']['rank']['level'] > start_user_level:
            response_level = f"{user_name} you leveled up from {numberize(start_user_level)} to {chatter_document['data_user']['rank']['level']:,}. Current XP: {numberize(chatter_document['data_user']['rank']['xp'])}"
        elif chatter_document['data_user']['rank']['level'] < start_user_level:
            response_level = f"{user_name} you lost {'a level' if abs(start_user_level - chatter_document['data_user']['rank']['level']) == 1 else 'some levels'} from {numberize(start_user_level)} to {numberize(chatter_document['data_user']['rank']['level'])}. Current XP: {numberize(chatter_document['data_user']['rank']['xp'])}"
        return chatter_document, response_level
    except Exception as e:
        logger.error(f"Error in xp_transfer -- {e}")
        return None


async def run(auto_cast_initiate):
    async def shutdown(obs_loaded: bool = True):  #, channel_document: Document = None):
        try:
            channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
            channel_document['data_counters']['stream']['bot_restart'] += 1
            channel_document.save()
            channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
            if channel_document['channel_details']['online']:
                response_shutdown = f"I am restarting. Bear with me. Much Love from {bot_name} <3"
                colour = "orange"
            else:
                response_shutdown = f"I is faded into thee shadows too. Much Love from {bot_name} <3"
                colour = "green"
            await bot.send_chat_announcement(id_streamer, id_streamer, response_shutdown, color=colour)
            logger.info(f"{long_dashes}\nAttempting to stop auto-casting. Stand By")
            try:
                users_collection = twitch_database.twitch.get_collection('users')
                users_docs = users_collection.find({})
                for user in users_docs:
                    user_document = await get_chatter_document(None, channel_document, user['_id'], user['name'], user['data_user']['login'], id_streamer, name_streamer)
                    if user_document is not None:
                        if user_document['data_games']['fish']['line']['cast']:
                            user_document['data_games']['fish']['line']['cast'] = False
                            user_document.save()
                            if user_document['data_games']['fish']['auto']['cast'] == 0:
                                await bot.send_chat_message(id_streamer, id_streamer, f"{user['name']} your cast was interrupted by a bot restart. Wait a few mins and then try again")
                        if user_document['data_games']['fish']['auto']['cast'] > 0 and user_document['name'] not in channel_document['data_games']['fish_recast']:
                            channel_document['data_games']['fish_recast'].append(user_document['name'])
                channel_document.save()
            except Exception as f:
                print(f"{fortime()}: Error in attempt to stop auto_casting;;;; {f}")
                pass
            logger.info(f"{long_dashes}\nShutting down twitch bot processes. Stand By")
            if obs_loaded:
                if channel_document is not None:
                    if channel_document['data_channel']['writing_clock']:
                        obs.set_source_visibility(obs_timer_scene, obs_timer_rate, False)
                        obs.set_source_visibility(obs_timer_scene, obs_timer_main, False)
                        obs.set_source_visibility(obs_timer_scene, obs_timer_sofar, False)
                        obs.set_source_visibility(obs_timer_scene, obs_timer_systime, False)
                        obs.set_source_visibility(obs_timer_scene, obs_timer_pause, False)
                        obs.set_source_visibility(obs_timer_scene, obs_hype_ehvent, False)
                        obs.set_source_visibility(obs_timer_scene, obs_timer_countup, False)
                await asyncio.sleep(1)
                obs.disconnect()
                logger.info(f"{long_dashes}\nDisconnected from OBS")
                await asyncio.sleep(1)
                await event_sub.stop()
            await asyncio.sleep(1)
            await bot.close()
            await asyncio.sleep(1)
            await disconnect_mongo()
            await asyncio.sleep(1)
            logger.info(f"{long_dashes}\nTwitch bot processes shut down successfully")
            await asyncio.sleep(2)
            await full_shutdown(logger_list)
            await asyncio.sleep(2)
            print(f"{long_dashes}\nShut Down Sequence Completed\n{long_dashes}")
            quit(666)
        except Exception as e:
            print(f"Error in shutdown() -- {e}")
            pass

    global level_const

    connect = obs.connect()
    if not connect:
        await shutdown(False)
        await full_shutdown(logger_list)
    logger.info(f"{long_dashes}\n{fortime()}: OBS Connection Established\n{long_dashes}")

    channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
    if channel_document is None:
        logger.error(f"{fortime()}: Error fetching channel_document... Shutting down")
        await shutdown()
        await full_shutdown(logger_list)

    if channel_document['data_games']['ranword'] == "":
        channel_document = await ran_word(channel_document)

    event_sub = EventSubWebsocket(bot)
    event_sub.start()

    await event_sub.listen_channel_ad_break_begin(streamer.id, on_stream_ad_start)
    await event_sub.listen_channel_chat_message(streamer.id, streamer.id, on_stream_chat_message)
    await event_sub.listen_channel_chat_notification(streamer.id, streamer.id, on_stream_chat_notification)
    await event_sub.listen_channel_cheer(streamer.id, on_stream_cheer)
    await event_sub.listen_channel_follow_v2(streamer.id, streamer.id, on_stream_follow)
    await event_sub.listen_hype_train_begin(streamer.id, on_stream_hype_begin)
    await event_sub.listen_hype_train_end(streamer.id, on_stream_hype_end)
    await event_sub.listen_hype_train_progress(streamer.id, on_stream_hype_progress)
    await event_sub.listen_channel_poll_begin(streamer.id, on_stream_poll_begin)
    await event_sub.listen_channel_poll_end(streamer.id, on_stream_poll_end)
    await event_sub.listen_channel_points_custom_reward_redemption_add(streamer.id, on_stream_point_redemption)
    await event_sub.listen_channel_prediction_begin(streamer.id, on_stream_prediction_begin)
    await event_sub.listen_channel_subscribe(streamer.id, on_stream_subbie)
    await event_sub.listen_channel_subscription_gift(streamer.id, on_stream_subbie_gift)
    await event_sub.listen_channel_raid(on_stream_raid_in, to_broadcaster_user_id=streamer.id)
    await event_sub.listen_channel_raid(on_stream_raid_out, from_broadcaster_user_id=streamer.id)
    await event_sub.listen_channel_update_v2(streamer.id, on_stream_update)
    await event_sub.listen_stream_online(streamer.id, on_stream_start)
    await event_sub.listen_stream_offline(streamer.id, on_stream_end)

    try:
        if len(channel_document['data_lists']['mods']) == 0:
            async for mod in bot.get_moderators(id_streamer):
                channel_document['data_lists']['mods'].append(mod.user_id)
            channel_document.save()
            channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
    except Exception as f:
        logger.error(f"{fortime()}: Error in on boot mod list == 0 attempt to add mods -- {f}")
        pass

    try:
        if len(channel_document['data_games']['fish_recast']) > 0 and auto_cast_initiate:
            for name in channel_document['data_games']['fish_recast']:
                await bot.send_chat_message(id_streamer, id_streamer, f"!fish {name} | ReCast Initiated")
                await asyncio.sleep(0.25)
            channel_document['data_games'].update(fish_recast=[])
            channel_document.save()
            channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
    except Exception as f:
        logger.error(f"{fortime()}: Error in run startup -- fishing recast -- {f}")
        pass

    try:
        if channel_document['data_channel']['writing_clock']:
            if channel_document['data_channel']['hype_train']['current']:
                set_hype_ehvent(obs, check_hype_train(channel_document, None))
            value = True
        else:
            value = False
        obs.set_source_visibility(obs_timer_scene, obs_timer_main, value)
        obs.set_source_visibility(obs_timer_scene, obs_timer_sofar, value)
        obs.set_source_visibility(obs_timer_scene, obs_timer_systime, value)
        if float(read_clock_pause()) > 0:
            value = True
        else:
            value = False
        obs.set_source_visibility(obs_timer_scene, obs_timer_pause, value)
        if float(read_clock_up_time()) > 0:
            value = True
        else:
            value = False
        obs.set_source_visibility(obs_timer_scene, obs_timer_countup, value)
        if read_clock_phase() != "norm":
            value = True
        else:
            value = False
        obs.set_source_visibility(obs_timer_scene, obs_timer_rate, value)
    except Exception as f:
        logger.error(f"{fortime()}: Error in obs scene setup(run) -- {f}")
        pass

    while True:  # Bot's Loop
        cls()
        try:
            user_input = input(f"\n".join(bot_options) + "\n")
            if user_input == "": pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await shutdown()
                    break
                elif user_input == 1:
                    while True:
                        cls()
                        user_input = input(f"\n".join(bot_options_one) + "\n")
                        if not user_input.isdigit():
                            print(f"Must enter just a number")
                            await asyncio.sleep(2)
                        else:
                            user_input = int(user_input)
                            if user_input == 0:
                                print(f"Returning to Bot's Main Loop")
                                await asyncio.sleep(1)
                                break
                            elif user_input == 1:
                                while True:
                                    cls()
                                    user_input = input("\n".join(bot_options_one_one) + "\n")
                                    if not user_input.isdigit():
                                        print(f"Invalid Input -- Put Just A Number")
                                        await asyncio.sleep(2)
                                    else:
                                        user_input = int(user_input)
                                        if user_input == 0:
                                            print("Going back..")
                                            await asyncio.sleep(2)
                                            break
                                        users_collection = twitch_database.twitch.get_collection('users')
                                        users = users_collection.find({})
                                        if user_input == 1:
                                            cls()
                                            printout = []
                                            try:
                                                users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['points'], reverse=True)
                                                printout.append(f"{long_dashes}\nkey -- Pos: Name -- Points -- Level(XP) -- Boost -- FishLevels")
                                                for n, user in enumerate(users_sorted):
                                                    printout.append(f"{n + 1}: {user['name']} -- {user['data_user']['rank']['points']:,.2f} -- {user['data_user']['rank']['level']}({user['data_user']['rank']['xp']:,.2f}) -- {user['data_user']['rank']['boost']} -- {user['data_games']['fish']['line']['stats']['level']}/{user['data_games']['fish']['lure']['level']}/{user['data_games']['fish']['reel']['level']}/{user['data_games']['fish']['rod']['level']}")
                                                special_logger.info('\n'.join(printout))
                                                special_logger.info(long_dashes)
                                                print("Done, returning to bot settings..")
                                                await asyncio.sleep(1)
                                                break
                                            except Exception as g:
                                                logger.error(f"{fortime()}: Error loading preparing user_stats  -- {g}\n{printout}")
                                                await asyncio.sleep(5)
                                                break
                                        if user_input == 2:
                                            cls()
                                            printout = []
                                            try:
                                                users_sorted = sorted(users, key=lambda user: user['data_user']['rank']['xp'], reverse=True)
                                                printout.append(f"{long_dashes}\nkey -- Pos: Name -- Points -- Level(XP) -- Boost -- FishLevels")
                                                for n, user in enumerate(users_sorted):
                                                    printout.append(f"{n + 1}: {user['name']} -- {user['data_user']['rank']['points']:,.2f} -- {user['data_user']['rank']['level']}({user['data_user']['rank']['xp']:,.2f}) -- {user['data_user']['rank']['boost']} -- {user['data_games']['fish']['line']['stats']['level']}/{user['data_games']['fish']['lure']['level']}/{user['data_games']['fish']['reel']['level']}/{user['data_games']['fish']['rod']['level']}")
                                                special_logger.info('\n'.join(printout))
                                                special_logger.info(long_dashes)
                                                print("Done, returning to bot settings..")
                                                await asyncio.sleep(1)
                                                break
                                            except Exception as g:
                                                logger.error(f"{fortime()}: Error loading preparing user_stats  -- {g}\n{printout}")
                                                await asyncio.sleep(5)
                                                break
                                        elif user_input == 5:
                                            if auto_cast_initiate:
                                                print("Autocast Already Initiated.. Returning To Main Menu")
                                                await asyncio.sleep(2)
                                                break
                                            auto_cast_initiate = True
                                            channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                                            try:
                                                if len(channel_document['data_games']['fish_recast']) > 0 and auto_cast_initiate:
                                                    for name in channel_document['data_games']['fish_recast']:
                                                        await bot.send_chat_message(id_streamer, id_streamer, f"!fish {name} | ReCast Initiated")
                                                        await asyncio.sleep(0.25)
                                                    channel_document['data_games'].update(fish_recast=[])
                                                    channel_document.save()
                                                    channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                                                    print("AutoCastInitiated.. Returning To Bot Menu")
                                                    await asyncio.sleep(1)
                                                    break
                                            except Exception as f:
                                                logger.error(f"{fortime()}: Error in run -- auto-initiate-manual -- fishing recast -- {f}")
                                                pass
                                        elif user_input == 9:
                                            while True:
                                                cls()
                                                user_input = input("Enter 1 to log users with free packs not successfully given out\nEnter 2 to carry out manual coupon giving\nEnter 8 to log current coupons\nEnter 9 to add coupons\nEnter 0 to go back\n")
                                                if user_input.isdigit():
                                                    printout = []
                                                    user_input = int(user_input)
                                                    if user_input == 0:
                                                        print("Going back...")
                                                        await asyncio.sleep(1)
                                                        break
                                                    elif user_input == 1:
                                                        try:
                                                            users_sorted = sorted(users, key=lambda user: user['data_user']['dates']['daily_cards'][0], reverse=True)
                                                            for user in users_sorted:
                                                                user_document = await get_chatter_document(None, channel_document, user['_id'], user['name'], user['data_user']['login'], id_streamer, name_streamer)
                                                                if user_document is not None:
                                                                    if user_document['data_user']['dates']['daily_cards'][0] > 0:
                                                                        printout.append(f"Packs; {user_document['data_user']['dates']['daily_cards'][0]} For; {user_document['name']}")
                                                                    else:
                                                                        printout.append(f"Detected End Of Users With FreePacks Redeemed with {user_document['name']} -- {user_document['data_user']['dates']['daily_cards'][0]}\n{long_dashes}")
                                                                        break
                                                            special_logger.info(f"{long_dashes}\n{len(printout) - 1} chatters redeemed codes;")
                                                            special_logger.info('\n'.join(printout))
                                                            print("Done...")
                                                            await asyncio.sleep(1)
                                                        except Exception as g:
                                                            logger.error(f"{fortime()}: Error loading preparing free_card_printout -- {g}\n{printout}")
                                                            await asyncio.sleep(10)
                                                            break
                                                    elif user_input == 2:
                                                        try:
                                                            users_sorted = sorted(users, key=lambda user: user['data_user']['dates']['daily_cards'][0], reverse=True)
                                                            for user in users_sorted:
                                                                user_document = await get_chatter_document(None, channel_document, user['_id'], user['name'], user['data_user']['login'], id_streamer, name_streamer)
                                                                if user_document is not None:
                                                                    if user_document['data_user']['dates']['daily_cards'][0] > 0:
                                                                        printout.append(f"Packs; {user_document['data_user']['dates']['daily_cards'][0]} For; {user_document['name']}")
                                                                        await bot.send_chat_message(id_streamer, id_streamer, f"{user_document['name']} you will have {user_document['data_user']['dates']['daily_cards'][0]} packs headed your way shortly!!")
                                                                        user_document['data_user']['dates']['daily_cards'][0] = 0
                                                                        user_document.save()
                                                                        await asyncio.sleep(0.1)
                                                                    else:
                                                                        printout.append(f"Detected End Of Users With FreePacks Redeemed with {user_document['name']} -- {user_document['data_user']['dates']['daily_cards'][0]}\n{long_dashes}")
                                                                        break
                                                            special_logger.info(f"{long_dashes}\n{len(printout) - 1} chatters redeemed codes;")
                                                            special_logger.info('\n'.join(printout))
                                                            print("Done...")
                                                            await asyncio.sleep(1)
                                                            break
                                                        except Exception as g:
                                                            logger.error(f"{fortime()}: Error loading preparing free_card_printout -- {g}\n{printout}")
                                                            await asyncio.sleep(10)
                                                            break
                                                    elif user_input == 8:
                                                        cls()
                                                        channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                                                        list_to_log = []
                                                        for coupon in channel_document['data_lists']['coupons']:
                                                            try:
                                                                list_to_log.append(coupon)
                                                            except Exception as grr:
                                                                logger.error(f"{fortime()}: Error logging current coupons -- {grr}")
                                                                break
                                                        special_logger.info(f"{long_dashes}\nCOUPONS CURRENT\n{long_dashes}")
                                                        if len(list_to_log) > 0:
                                                            special_logger.info(' '.join(list_to_log))
                                                        else:
                                                            special_logger.info("No Coupons To Log!!!")
                                                        print("Operation Completed..")
                                                        await asyncio.sleep(1)
                                                    elif user_input == 9:
                                                        try:
                                                            while True:
                                                                cls()
                                                                channel_document = await get_channel_document(streamer.id, streamer.display_name, streamer.login)
                                                                user_input = input("Enter Coupon Codes ONLY separated by ' ' or ', ' or '|'...\nEnter 0 to leave here\n")
                                                                if user_input == "0":
                                                                    print("Leaving Coupon Add Area")
                                                                    await asyncio.sleep(1)
                                                                    break
                                                                elif len(user_input) == 5:
                                                                    coupons = [user_input]
                                                                elif ' ' in user_input:
                                                                    coupons = list(
                                                                        map(str, user_input.split(' ')))
                                                                elif ', ' in user_input:
                                                                    coupons = list(
                                                                        map(str, user_input.split(', ')))
                                                                elif '|' in user_input:
                                                                    coupons = list(
                                                                        map(str, user_input.split('|')))
                                                                else:
                                                                    coupons = None
                                                                    print("Your input wasn't valid, try again...")
                                                                if coupons is not None:
                                                                    coupons_add, coupons_not = [], []
                                                                    for coupon in reversed(coupons):
                                                                        if coupon not in channel_document['data_lists']['coupons'] and len(coupon) == 5:
                                                                            coupons_add.append(coupon)
                                                                            channel_document['data_lists']['coupons'].append(coupon)
                                                                        else:
                                                                            coupons_not.append(f"{coupon}{'--LenNot5--' if len(coupon) != 5 else '--AlrdyIn--'}")
                                                                    channel_document.save()
                                                                    special_logger.info(f"{long_dashes}\n{fortime()}: Added {len(coupons_add)} new coupon codes\n{'|'.join(coupons_add) if len(coupons_add) > 0 else 'NONE'}\nSkipped {len(coupons_not)} Coupons;\n{'|'.join(coupons_not) if len(coupons_not) > 0 else 'NONE'}\n{long_dashes}")
                                                                    print("Done...")
                                                                    await asyncio.sleep(1)
                                                                    break
                                                        except Exception as g:
                                                            logger.error(f"{fortime()}: Error adding to coupon list -- {g}")
                                                            await asyncio.sleep(10)
                                                            break
                                                    else:
                                                        print("You must enter just a number")
                                                        await asyncio.sleep(2)
                                        elif user_input == 10:
                                            cls()
                                            print("Not In Operation")
                                            await asyncio.sleep(2)
                                            break
                                            # special_logger.info(f"{long_dashes}\nDOCUMENT_UPDATE\n{long_dashes}")
                                            # for user in users:
                                            #     try:
                                            #         user_document = await get_chatter_document(None, channel_document, user['_id'], user['name'], user['data_user']['login'], id_streamer, name_streamer)
                                            #         if user_document is not None:
                                            #             # # For fishing item updates
                                            #             # var1 = 'a taped up brick of coke'
                                            #             # var1_new = 'a taped up brick of cocaine'
                                            #             #
                                            #             #     if var1 in user_document['data_games']['fish']['auto']['catches']:
                                            #             #         user_document['data_games']['fish']['auto']['catches'][var1_new] = user_document['data_games']['fish']['auto']['catches'][var1]
                                            #             #         user_document['data_games']['fish']['auto']['catches'][var1] = None
                                            #             #         special_logger.info(f"{user['name']} updated -- {var1} auto")
                                            #             #     if var1 in user_document['data_games']['fish']['totals']['auto']['catches']:
                                            #             #         user_document['data_games']['fish']['totals']['auto']['catches'][var1_new] = user_document['data_games']['fish']['totals']['auto']['catches'][var1]
                                            #             #         user_document['data_games']['fish']['totals']['auto']['catches'][var1] = None
                                            #             #         special_logger.info(f"{user['name']} updated -- {var1} auto totals")
                                            #             #     if var1 in user_document['data_games']['fish']['totals']['manual']['catches']:
                                            #             #         user_document['data_games']['fish']['totals']['manual']['catches'][var1_new] = user_document['data_games']['fish']['totals']['manual']['catches'][var1]
                                            #             #         user_document['data_games']['fish']['totals']['manual']['catches'][var1] = None
                                            #             #         special_logger.info(f"{user['name']} updated -- {var1} manual totals")
                                            #             user_document['data_games']['other'] = {"bite": {"times_bite": 0, "times_bit": 0}, "burn": {"times_burn": 0, "times_burned": 0}, "kick": {"times_kick": 0, "times_kicked": 0}, "lick": {"times_lick": 0, "times_licked": 0}, "pants": {"times_pants": 0, "times_pantsed": 0}, "pinch": {"times_pinch": 0, "times_pinched": 0}, "pounce": {"times_pounce": 0, "times_pounced": 0}, "punch": {"times_punch": 0, "times_punched": 0}, "slap": {"times_slap": 0, "times_slapped": 0}, "tickle": {"times_tickle": 0, "times_tickled": 0}}
                                            #             special_logger.info(f"{user['name']} reset other game stats")
                                            #             user_document.save()
                                            #     except Exception as grr:
                                            #         logger.error(f"{fortime()}: Error in data_restructure for user_docs -- {grr}")
                                            #         await asyncio.sleep(10)
                                            #         break
                                            # special_logger.info(f"{long_dashes}\nOperation Carried Out\n{long_dashes}")
                                            # print("Operation Carried out... Returning to Main Menu")
                                            # await asyncio.sleep(1)
                                            # break
                                        else:
                                            print("Invalid Input")
                                            await asyncio.sleep(2)
                            elif user_input == 2:
                                while True:
                                    cls()
                                    user_input = input(f"\n".join(bot_options_one_two) + "\n")
                                    if not user_input.isdigit():
                                        print("Must enter just a number")
                                        await asyncio.sleep(2)
                                    else:
                                        user_input = int(user_input)
                                        if user_input == 0:
                                            print("Going Back")
                                            await asyncio.sleep(1)
                                            break
                                        elif user_input == 1:
                                            configure_write_to_clock(await get_channel_document(streamer.id, streamer.display_name, streamer.login), obs)
                                            await asyncio.sleep(1)
                                        elif user_input == 2:
                                            configure_hype_ehvent(await get_channel_document(streamer.id, streamer.display_name, streamer.login), obs)
                                            await asyncio.sleep(1)
                                        elif user_input == 3:
                                            reset_current_time()
                                            await asyncio.sleep(1)
                                        elif user_input == 4:
                                            reset_max_time()
                                            await asyncio.sleep(1)
                                        elif user_input == 5:
                                            reset_total_time()
                                            await asyncio.sleep(1)
                                        elif user_input == 6:
                                            reset_clock_accel_rate(obs)
                                            await asyncio.sleep(1)
                                        elif user_input == 7:
                                            reset_clock_slow_rate(obs)
                                            await asyncio.sleep(1)
                                        elif user_input == 8:
                                            reset_clock_pause(obs)
                                            await asyncio.sleep(1)
                                        elif user_input == 9:
                                            reset_flash_settings()
                                            await asyncio.sleep(1)
                                        else:
                                            print("Not valid, try again..")
                                            await asyncio.sleep(2)
                            else:
                                print("Not valid, try again..")
                                await asyncio.sleep(2)
                elif user_input == 3:
                    cls()
                    while True:
                        number, add = loop_get_user_input_clock()
                        if number.isdigit():
                            write_clock(float(number), logger, add, obs=obs, manual=True)
                            await asyncio.sleep(1)
                            break
                        else:
                            print(f"Invalid Input -- You put '{number}' - If None, see error logs - which is a {type(number)} -- USE NUMPAD +/-!!")
                            await asyncio.sleep(2)
                elif user_input == 4:
                    cls()
                    reset_bot_raid()
                    await asyncio.sleep(1)
                elif user_input == 5:
                    reset_night_mode()
                    await asyncio.sleep(1)
                else:
                    print(f"Invalid Input -- You put '{user_input}'")
                    await asyncio.sleep(2)
            else:
                print(f"Invalid Input -- You put '{user_input}' which is a {type(user_input)}")
                await asyncio.sleep(2)
        except KeyboardInterrupt:
            await shutdown()
            break
        except Exception as e:
            logger.error(f"{fortime()}: Error in BOT Loop -- {e}")
            try:
                continue
            except Exception as grrrr:
                logger.error(f"{fortime()}: ERROR TRYING TO CONTINUE UPON LAST ERROR -- {grrrr} -- ATTEMPTING TO HALT BOT")
                await shutdown()


async def auth_bot():
    twitch_helper = UserAuthenticationStorageHelper(bot, target_scopes)
    await twitch_helper.bind()
    streamer = await first(bot.get_users(user_ids=id_streamer))
    logger.info(f"{long_dashes}\n{fortime()}: Twitch Bot Authenticated Successfully")
    return twitch_helper, streamer


if __name__ == "__main__":
    os.system(f"color 02")
    auto_cast_initiate = True
    bot_options = ["Enter 1 to for options",
                   # "Enter 2 to fetch stats",
                   "Enter 3 to +/- time",
                   "Enter 4 for Bot Protection",
                   "Enter 5 for Sleep Mode",
                   "Enter 0 to Halt Bot"]
    bot_options_one = ["Enter 1 for bot settings",
                       "Enter 2 for timer settings",
                       "Enter 0 to to return to Main Menu"]
    bot_options_one_one = ["Enter 1 to print out general user stats sorted by points",
                           "Enter 2 to print out general user stats sorted by xp",
                           "Enter 5 to initiate auto casts",
                           "Enter 9 to see free pack options",
                           "Enter 10 to add new field to user_docs",
                           "Enter 0 to go back"]
    bot_options_one_two = ["Enter 1 to Enable/Disable Writing to Clock",
                           "Enter 2 to Enable/Disable Thee Hype EhVent",
                           "Enter 3 to Change Current time left",
                           "Enter 4 to Change Max Time",
                           "Enter 5 to Change Total Time",
                           "Enter 6 to Change Countdown ACCEL Rate",
                           "Enter 7 to Change Countdown SLOW Rate",
                           "Enter 8 to Change Countdown Pause",
                           "Enter 9 to Configure Flash Settings",
                           "Enter 0 To Go Up"]
    main_options = ["Enter 1 to start twitch bot",
                    "Enter 2 to start twitch bot WITH NO AUTO CAST",
                    "Enter 3 to +/- time",
                    "Enter 0 to Exit Program"]

    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger("logger", f"main_log--{init_time}.log", logger_list)
    chat_logger = setup_logger("chat_logger", f"chat_log--{init_time}.log", logger_list)
    fish_logger = setup_logger("fish_logger", f"fish_log--{init_time}.log", logger_list)
    gamble_logger = setup_logger("gamble_logger", f"gamble_log--{init_time}.log", logger_list)
    special_logger = setup_logger("special_logger", f"special_log--{init_time}.log", logger_list)  #, logging.WARN)

    # if None in (logger, chat_logger, gamble_logger, special_logger):
    if None in logger_list:
        print(f"One of thee loggers isn't setup right -- {logger}/{chat_logger}/{fish_logger}/{gamble_logger}/{special_logger} -- Quitting program")
        asyncio.run(full_shutdown(logger_list))

    bot = BotSetup(id_twitch_client, id_twitch_secret)
    obs = WebsocketsManager()

    # Main Loop
    while True:
        cls()
        try:
            user_input = input("\n".join(main_options) + "\n")
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    print(f"Exiting Program")
                    break
                elif user_input == 1:
                    twitch_helper, streamer = asyncio.run(auth_bot())
                    try:
                        logger.info(long_dashes)
                        twitch_database = connect_mongo(mongo_twitch_collection, DEFAULT_CONNECTION_NAME)
                        time.sleep(1)
                        if twitch_database is None:
                            asyncio.run(disconnect_mongo())
                            logger.error(f"{fortime()}: Error connecting to twitch_database -- Quitting Program..")
                            break
                    except Exception as f:
                        logger.error(f"{fortime()}: Error Loading Database(s) -- {f}")
                        break
                    asyncio.run(run(auto_cast_initiate))
                    break
                elif user_input == 2:
                    auto_cast_initiate = False
                    twitch_helper, streamer = asyncio.run(auth_bot())
                    try:
                        logger.info(long_dashes)
                        twitch_database = connect_mongo(mongo_twitch_collection, DEFAULT_CONNECTION_NAME)
                        time.sleep(1)
                        if twitch_database is None:
                            asyncio.run(disconnect_mongo())
                            logger.error(f"{fortime()}: Error connecting to twitch_database -- Quitting Program..")
                            break
                    except Exception as f:
                        logger.error(f"{fortime()}: Error Loading Database(s) -- {f}")
                        break
                    asyncio.run(run(auto_cast_initiate))
                    break
                elif user_input == 3:
                    while True:
                        number, add = loop_get_user_input_clock()
                        if number.isdigit():
                            write_clock(float(number), logger, add, manual=True)
                            break
                        else:
                            print(f"Invalid Input -- You put '{number}' - If None, see error logs -  which is a {type(number)} -- USE NUMPAD +/-!!")
                else:
                    print(f"Invalid Input -- You Entered '{user_input}'")
            else:
                print(f"Invalid Input -- You entered '{user_input}' and it's type is a {type(user_input)}")
        except KeyboardInterrupt:
            print(f"Exiting Program")
            break
        except TwitchBackendException:
            logger.error(f"{fortime()}: Error on TwitchBackendException -- Exiting Program.."), time.sleep(20)
            sys._exit()
        except Exception as e:
            logger.error(f"{fortime()}: Error in MAIN loop -- {e} - Exiting Program"), time.sleep(20)
            sys._exit()
