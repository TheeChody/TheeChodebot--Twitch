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
    ChannelCheerEvent, ChannelFollowEvent, ChannelPollBeginEvent, ChannelPollEndEvent, ChannelPointsCustomRewardRedemptionAddEvent, \
    ChannelPredictionEvent, ChannelRaidEvent, ChannelSubscribeEvent, ChannelSubscriptionGiftEvent, ChannelUpdateEvent, HypeTrainEvent, \
    HypeTrainEndEvent, StreamOnlineEvent, StreamOfflineEvent  #, GoalEvent
from functions import long_dashes, loop_get_user_input_clock, read_clock, reset_clock_slow_rate, reset_current_time, \
    reset_clock_pause, reset_max_time, reset_total_time, read_clock_sofar, write_clock, read_clock_max, read_clock_total, \
    standard_seconds, WebsocketsManager, setup_logger, fortime, load_dotenv, configure_write_to_clock, full_shutdown, \
    logs_directory, countdown_rate_strict, write_clock_pause, read_clock_pause, cls, standard_direct_dono, set_timer_pause, \
    read_clock_phase, reset_clock_accel_rate, reset_night_mode, read_night_mode, reset_flash_settings, read_bot_raid, \
    reset_bot_raid, write_clock_accel_time, write_clock_slow_time, write_clock_phase, set_timer_rate, read_clock_accel_time, \
    read_clock_slow_time, read_clock_up_time, write_clock_up_time, set_timer_count_up, strict_pause, flash_window, \
    set_hype_ehvent, check_hype_train, standard_ehvent_mult, obs_timer_main, obs_timer_sofar, obs_timer_countup, obs_timer_pause, \
    obs_timer_rate, obs_hype_ehvent, obs_timer_scene, write_clock_slow_rate_time, clock_direction

# ToDo List ------------------------------------------------------------------------------------------------------------
#  Figure out music queueing system, gonna need ability to manipulate VLC player. or make my own? haha yeah right
#  addon to ^^ use pytube to gather track info/download video if not downloaded already
#  Add Translation from MorseCode to English  -- Still unsure of this one..
#  ---------------------------------------------------- End of List ----------------------------------------------------

load_dotenv()
name_streamer = os.getenv("name")
id_streamer = os.getenv("broadcaster")  # Your Twitch User ID
id_twitch_client = os.getenv("client")  # Your Twitch Dev App Client ID
id_twitch_secret = os.getenv("secret")  # Your Twitch Dev App Secret ID

mongo_login_string = os.getenv("monlog_string")  # MongoDB Login String
mongo_twitch_collection = os.getenv("montwi_string")  # Mongo Collection To Use

link_tip = os.getenv("link_tip")  # Link to direct dono
link_discord = os.getenv("link_discord")  # Link to Discord
link_loots = os.getenv("link_loots")  # Link to streamloots page (if one)
link_loots_discount = os.getenv("link_loots_discount")  # Link to streamloots discount code (if one)
link_throne = os.getenv("link_throne")  # Link to Throne Wishlist
link_treatstream = os.getenv("link_treatstream")
link_clips = f"https://www.twitch.tv/{name_streamer}/clip/"
response_thanks = os.getenv("response_thanks")  # A response message one wants to be repeated at thee end of monetary things
channel_point_name = os.getenv("channel_point_name")  # Your channel point name
id_streamloots = "451658633"
id_chodebot = "1023291886"
marathon_name = "Hell-A-Thon"

cmd = ("$", "!")  # What thee commands can start with
delete_phrases = ["bestviewers",
                  "cheapviewers"]
keywords = {r"bot": {"response": "What?"}}
target_scopes = [AuthScope.BITS_READ, AuthScope.CLIPS_EDIT, AuthScope.CHANNEL_BOT, AuthScope.USER_READ_CHAT, AuthScope.USER_WRITE_CHAT,
                 AuthScope.CHANNEL_MODERATE, AuthScope.CHANNEL_READ_ADS, AuthScope.CHANNEL_MANAGE_ADS, AuthScope.CHANNEL_READ_GOALS,
                 AuthScope.USER_READ_BROADCAST, AuthScope.CHANNEL_MANAGE_POLLS, AuthScope.USER_MANAGE_WHISPERS, AuthScope.CHANNEL_SUBSCRIPTIONS,
                 AuthScope.CHANNEL_READ_HYPE_TRAIN, AuthScope.MODERATOR_READ_CHATTERS, AuthScope.MODERATOR_READ_FOLLOWERS,
                 AuthScope.CHANNEL_READ_PREDICTIONS, AuthScope.MODERATOR_MANAGE_SHOUTOUTS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
                 AuthScope.CHANNEL_READ_SUBSCRIPTIONS, AuthScope.CHANNEL_MANAGE_PREDICTIONS, AuthScope.MODERATOR_MANAGE_BANNED_USERS,
                 AuthScope.MODERATOR_MANAGE_CHAT_MESSAGES, AuthScope.MODERATION_READ, AuthScope.CHANNEL_MANAGE_MODERATORS, AuthScope.MODERATOR_MANAGE_ANNOUNCEMENTS]  # ToDo: FIGURE OUT WHY THEE PREDICTION SHIT FLIPS OUT ON END/LOCK CALL!!!!!!!!!!!
logger_list = []

options_webcam = ("Colour", "Flip", "Spin")
options_webcam_colours = ("None", "Blue", "Green", "Hidden", "Magenta", "Red")
options_eq_colour = ("Blue", "Green", "Magenta", "Red", "White")

bot_name = "ChodyBot"
level_const = 100  # Base level Value
raid_seconds = 15  # Only for points now
follow_seconds = 30  # Only for points now
standard_points = 1  # Base value -- points for chatting, bitties, subbing/resubbing, gifting subbies etc.
stream_loots_seconds = 1.8  # How many seconds per CARD purchased is added
stream_loots_pack_quantity = 3  # How many cards are in ONE Pack
fish_auto_cost = 25  # AutoCast Cost
fish_cut_cost = 1000  # CastCut Cost
fish_cut_time = 7200  # CastCut CoolDown
jail_cost = 5000  # JailAttempt Cost
jail_time = 300  # TimeIn Jail
jail_wait_time = 1800  # JailCoolDown "Probation"
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
            # channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
            ad_schedule = await bot.get_ad_schedule(id_streamer)
            ad_till_next_seconds, now_time_seconds = await get_ad_time(ad_schedule)
            ad_length = float(ad_schedule.duration)
            seconds_till_ad = ad_till_next_seconds - now_time_seconds
            await bot.send_chat_announcement(id_streamer, id_streamer, f"Incoming ad break, {auto_response} and should only last {datetime.timedelta(seconds=ad_length)}. Next ad inbound in {datetime.timedelta(seconds=seconds_till_ad)}.{f' {marathon_response}.' if marathon_response is not None else ''}", color="purple")
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

    async def chatter_doc_swap(user_name: str, channel_document: Document, points: float):
        try:
            chatter_document = Users.objects.get(name=user_name)
            chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points)  # / 2)
            return chatter_document, response_level, None
        except Exception as g:
            if FileNotFoundError:
                return None, None, f"Hey {user_name}, make sure your StreamLoots name is thee same as your Twitch UserName eh? You missed out on {points} points."
            else:
                logger.error(f"{fortime()}: Error in chatter_doc_swap -- {g}")
                return None, None, None

    start = timer()
    try:
        response_was_lurk = None
        chatter_id = data.event.chatter_user_id
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if chatter_id in channel_document['data_lists']['ignore'] and not data.event.message.text.startswith(cmd):
            end_timer("chatter_id_in_ignore_list")
            return
        if chatter_id == id_streamer and not data.event.message.text.startswith(cmd):
            end_timer("streamer_id_no_cmd")
            return
        if chatter_id == id_streamloots and not data.event.message.text.startswith(cmd):
            """darktrobbit has gifted QUANTITY packs to the community. Claim yours now! LINK_HERE"""
            msg = data.event.message.text
            if "has gifted" in msg:
                name, quantity = msg.split(" has gifted ")
                quantity, _ = quantity.split(" packs")
                if not quantity.isdigit():
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- streamloots gifted community packs -- {name} {type(name)} - {quantity} {type(quantity)}")
                    end_timer("has gifted bit -- quantity is NOT a digit")
                    return
                seconds = int(quantity) * ((stream_loots_seconds * 100) * stream_loots_pack_quantity)
                if channel_document['data_channel']['hype_train']['current']:
                    seconds = check_hype_train(channel_document, seconds)
                seconds, time_not = write_clock(seconds, True, obs)
                chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                await bot.send_chat_message(id_streamer, id_streamer, f"{name} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
        chatter_username = data.event.chatter_user_name
        chatter_document = await get_chatter_document(data, channel_document)
        if chatter_document is None and chatter_id not in channel_document['data_lists']['ignore']:
            special_logger.error(f"Chatter/Channel Document is None!! -- chatter-{chatter_username} -- channel-{channel_document}")
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
                        users_board.append(f"#{user.rank:02d}: {user.user_name}: {user.score:,}")
                    await bot.send_chat_message(id_streamer, id_streamer,
                                                f"Bitties 4 Titties Leaderboard: {' - '.join(users_board)}",
                                                reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - bittiesleader command -- {f}")
                    end_timer("bittiesleader command")
                    return
            elif command_check.startswith("clip"):
                try:
                    now_time = datetime.datetime.now()
                    if channel_document['data_channel']['last_clip'] is None:
                        pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(channel_document['data_channel']['last_clip'])) < 30 and chatter_id != id_streamer:
                        await bot.send_chat_message(id_streamer, id_streamer, f"There has already been a clip taken within thee last 30 seconds")
                        end_timer("clip command")
                        return
                    created_clip = await bot.create_clip(id_streamer, False)
                    channel_document['data_channel'].update(last_clip=datetime.datetime.now())
                    channel_document.save()
                    await asyncio.sleep(5)
                    await bot.send_chat_message(id_streamer, id_streamer, f"Clip can be seen at; {link_clips}{created_clip.id}", reply_parent_message_id=data.event.message_id)
                    logger.info(f"Clip Created by: {chatter_username}\nWATCH: {link_clips}{created_clip.id}\nEDIT: {created_clip.edit_url}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - clip command -- {f}")
                    end_timer("clip command")
                    return
            elif command_check.startswith(("command", "cmd", "commandlist", "cmdlist")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Registered commands can be found in the 'BIP' extension activated in Component 1", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - commands command -- {f}")
                    end_timer("commands command")
                    return
            elif command_check.startswith("discord"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee discord link is: {link_discord}",
                                                reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- discord command -- {f}")
                    end_timer("discord command")
                    return
            elif command_check.startswith(("directdono", "tip")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, link_tip)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - tip command -- {f}")
                    end_timer("tip command")
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
                        chatter = await bot.get_channel_followers(id_streamer, user_id=target_id)
                    else:
                        if chatter_id == id_streamer:
                            end_timer("")
                            return
                        chatter = await bot.get_channel_followers(id_streamer, user_id=chatter_id)
                        target_id = chatter_id
                    user_follow_seconds = await get_long_sec(fortime_long(chatter.data[0].followed_at.astimezone()))
                    # ToDo: Format thee followed time string to look more nicer than just days and hours..
                    now_seconds = await get_long_sec(fortime_long(datetime.datetime.now()))
                    await bot.send_chat_message(id_streamer, id_streamer, f"{f'You have' if chatter_id == target_id else f'{target_name} has'} been following for {str(datetime.timedelta(seconds=abs(user_follow_seconds - now_seconds))).title()}.", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- followage command -- {f}")
                    end_timer("followage command")
                    return
            elif command_check.startswith(("lastcomment", "lastmessage")):
                if chatter_id == id_streamer:
                    end_timer("lastcomment command")
                    return
                try:
                    last_message = None
                    with open(f"{logs_directory}{init_time}-chat_log.log", "r", encoding="utf-8") as file:
                        chat_logs = file.read()
                    chat_logs = list(map(str, chat_logs.splitlines()))
                    for last in reversed(chat_logs):
                        if last.startswith(chatter_id):
                            user_name, last_message = last.split(": ", maxsplit=1)
                            break
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name}!! {chatter_username}'s last message was: {last_message if not None else 'Not Found!!!'}")
                    await flash_window("attn")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - lastcomment command -- {f}")
                    end_timer("lastcomment command")
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
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - lurk command -- {f}")
                    end_timer("lurk command")
                    return
            elif command_check.startswith(("throne", "wishlist")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, link_throne)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - throne command -- {f}")
                    end_timer("throne command")
                    return
            elif command_check.startswith(("treat", "food")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, link_treatstream)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - treat command -- {f}")
                    end_timer("treat command")
                    return
            # OBS Commands
            elif command_check.startswith("eqcolour"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"This is temp not available")
                    end_timer("eqcoulour command")
                    return
                    # if chatter_document['data_user']['points'] < 100 and chatter_id != id_streamer:
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enuff points for that, need 100 CP you have {chatter_document['data_user']['points']:,.2f} CP", reply_parent_message_id=data.event.message_id)
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
                    #         new_user_points = chatter_document['data_user']['points'] - 100
                    #         chatter_document['data_user'].update(points=new_user_points)
                    #         chatter_document.save()
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} changes thee colour to {colour.title()} with 100 chodybot points")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- eqcolour command -- {f}")
                    end_timer("eqcolour command")
                    return
            elif command_check.startswith("webcam"):
                try:  # Flip, filters, (un)hide
                    new_colour = ""
                    if chatter_document['data_user']['points'] < 100 and chatter_id != id_streamer:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enuff points for that, need 100 CP you have {chatter_document['data_user']['points']:,.2f} CP", reply_parent_message_id=data.event.message_id)
                        end_timer("webcam command")
                        return
                    action = command.replace(" ", "").removeprefix("webcam").title()
                    if not action.startswith(options_webcam):
                        await bot.send_chat_message(id_streamer, id_streamer, f"Valid options are: '{'/'.join(list(options_webcam))}'", reply_parent_message_id=data.event.message_id)
                        end_timer("webcam command")
                        return
                    if action.startswith("Colour"):
                        await bot.send_chat_message(id_streamer, id_streamer, f"This part is temp not available")
                        end_timer("webcam command -- colour")
                        return
                        # new_colour = action.removeprefix("Colour")
                        # action = action.removesuffix(new_colour)
                        # success = await change_webcam("colour", new_colour=new_colour.title())
                    else:
                        success = await change_webcam("transform", new_transform=action)
                    if success:
                        if chatter_id != id_streamer:
                            new_user_points = chatter_document['data_user']['points'] - 100
                            chatter_document['data_user'].update(points=new_user_points)
                            chatter_document.save()
                        response_webcam = f"{chatter_username} {f'{action}s {data.event.broadcaster_user_name}' if action != 'Colour' else f'changed thee {action} of {data.event.broadcaster_user_name} to {new_colour.title()}'} for 100 {bot_name} Points"
                    else:
                        response_webcam = f"{chatter_username} your command was not registered, no points taken.", f"Valid colours are: {f'|'.join(list(options_webcam_colours))}" if action.startswith("Colour") else ""
                    await bot.send_chat_message(id_streamer, id_streamer, response_webcam)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- webcam command -- {f}")
                    end_timer("webcam command")
                    return
            # Level/Points Commands
            elif command_check.startswith(("levelcheck", "levelscheck", "checklevel")):  # ToDo: Add Manual Targeting
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
                            users_sorted = sorted(users, key=lambda user: user['data_rank']['xp'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == target_document['_id']:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- levelcheck command -- fetching user rank on leaderboard -- {target_username} -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']} is Level(XP): {target_document['data_rank']['level']:,}({target_document['data_rank']['xp']:,.2f}) & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    elif chatter_document is not None:
                        try:
                            users_collection = twitch_database.twitch.get_collection('users')
                            users = users_collection.find({})
                            users_sorted = sorted(users, key=lambda user: user['data_rank']['xp'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == chatter_id:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- levelcheck command -- fetching user rank on leaderboard -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are Level(XP): {chatter_document['data_rank']['level']:,}({chatter_document['data_rank']['xp']:,.2f}) & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong getting your chatter_document", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- levelcheck command -- {f}")
                    end_timer("levelcheck command")
                    return
            elif command_check.startswith(("levelleader", "levelsleader", "leaderlevel")):
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    users = users_collection.find({})
                    users_sorted = sorted(users, key=lambda user: user['data_rank']['xp'], reverse=True)
                    response_leader = []
                    for n, user in enumerate(users_sorted[:5]):
                        response_leader.append(f"{n+1}: {user['name']} Lvl(XP):{user['data_rank']['level']:,}({user['data_rank']['xp']:,.2f})")
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
                    #     response_leader.append(f"{n + 1}: {user['name']} Lvl(XP):{user['data_rank']['level']:,}({user['data_rank']['xp']:,.2f})")
                    # await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name}'s Leaderboard: {' - '.join(response_leader)}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- leaderboard command -- {f}")
                    end_timer("levelleader command")
                    return
            elif command_check.startswith(("pointscheck", "pointcheck", "checkpoint")):
                rank = None
                try:
                    command_points = command_check.removeprefix("pointscheck")
                    command_points = command_points.removeprefix("pointcheck")
                    command_points = command_points.removeprefix("checkpoint")
                    if command_points.startswith(("s@", "@")) or command_points != "":
                        target_username = command_points
                        if command_points.startswith("s"):
                            target_username = target_username.removeprefix("s")
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
                            users_sorted = sorted(users, key=lambda user: user['data_rank']['xp'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == target_document['_id']:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- pointscheck command -- fetching user rank on leaderboard -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']} has {target_document['data_user']['points']:,.2f} points & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    elif chatter_document is not None:
                        try:
                            users_collection = twitch_database.twitch.get_collection('users')
                            users = users_collection.find({})
                            users_sorted = sorted(users, key=lambda user: user['data_user']['points'], reverse=True)
                            for n, user in enumerate(users_sorted):
                                if user['_id'] == chatter_id:
                                    rank = n + 1
                                    break
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- pointscheck command -- fetching user rank on leaderboard -- {g}")
                            pass
                        await bot.send_chat_message(id_streamer, id_streamer, f"You have {chatter_document['data_user']['points']:,.2f} points & Rank: {f'{rank:,}' if rank is not None else 'ERROR FETCHING RANK'} on thee leaderboard.", reply_parent_message_id=data.event.message_id)
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong getting your chatter_document", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - points check command -- {f}")
                    end_timer("pointscheck command")
                    return
            elif command_check.startswith(("pointsleader", "pointleader", "leaderpoint")):
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    users = users_collection.find({})
                    users_sorted = sorted(users, key=lambda user: user['data_user']['points'], reverse=True)
                    response_points_leader = ""
                    for n, user in enumerate(users_sorted[:5]):
                        response_points_leader += f"{n+1}: {user['name']}/{user['data_user']['points']:,.2f} - "
                    await bot.send_chat_message(id_streamer, id_streamer, response_points_leader[:-3], reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- command pointsleader -- {f}")
                    end_timer("pointsleader command")
                    return
            # Mini-Game Commands
            elif command_check.startswith("bite"):
                try:
                    if command.replace(" ", "").replace("bite", "").startswith("@"):
                        target_user_name = command.replace(" ", "").replace("bite@", "")
                        target = await select_target(channel_document, chatter_id, True, target_user_name, "bite")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target_user_name} isn't a valid target!", reply_parent_message_id=data.event.message_id)
                            end_timer("bite command")
                            return
                    else:
                        target = await select_target(channel_document, chatter_id, game_type="bite")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"Couldn't locate a valid target!!", reply_parent_message_id=data.event.message_id)
                            end_timer("bite command")
                            return
                    with open("data/options_bite", "r") as file:
                        bite_options = file.read()
                    bite_choices = list(map(str, bite_options.splitlines()))
                    bite_choice = random.choice(bite_choices)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} bit {target.user_name} {bite_choice.format(chatter_username)}!")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- bite command -- {f}")
                    end_timer("bite command")
                    return
            elif command_check.startswith("cutline"):
                try:
                    if chatter_document['data_user']['points'] < fish_cut_cost:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points for that! Need {fish_cut_cost}, you have {chatter_document['data_user']['points']:,.2f}")
                        end_timer("cutline chatter not enough points")
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
                    if target_document['data_games']['fish']['line']['cut_last'] is None:
                        pass
                    elif await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(target_document['data_games']['fish']['line']['cut_last'])) < fish_cut_time:
                        wait_time = fish_cut_time - (await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(target_document['data_games']['fish']['line']['cut_last'])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line has been recently cut already. Gotta wait {datetime.timedelta(seconds=wait_time)}.", reply_parent_message_id=data.event.message_id)
                        end_timer("cutline target's line been cut recently")
                        return
                    elif target_document['data_games']['fish']['line']['cut']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line is already cut!!")
                        end_timer("cutline target's line been cut already")
                        return
                    chatter_document['data_user']['points'] -= fish_cut_cost
                    chatter_document.save()
                    chatter_document = await get_chatter_document(data)
                    target_document['data_games']['fish']['line']['cut'] = True
                    target_document['data_games']['fish']['line']['cut_by'] = chatter_username
                    target_document['data_games']['fish']['line']['cut_last'] = datetime.datetime.now()
                    target_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line has been cut successfully!! You now have {chatter_document['data_user']['points']:,.2f} points remaining", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- cutline command -- {f}")
                    end_timer("cutline command")
                    return
            elif command_check.startswith("fight"):
                try:
                    if command.replace(" ", "").replace("fight", "").startswith("@"):
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
                    fight_chance = random.randint(1, 3)
                    if fight_chance == 1:
                        fight_response = "won"
                    elif fight_chance == 2:
                        fight_response = "lost"
                    else:
                        fight_response = "tied"
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} challenged {target.user_name} to a fight and {fight_response}!")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- fight command -- {f}")
                    end_timer("fight command")
                    return
            elif command_check.startswith("fish"):  # Moist Dude's Line
                async def refresh_chatter_document(data, target_id, target_name, target_login):
                    if target_id is not None:
                        chatter_document = await get_chatter_document(None, user_id=target_id, user_name=target_name, user_login=target_login, b_id=id_streamer, b_name=name_streamer)
                    else:
                        chatter_document = await get_chatter_document(data)
                    return chatter_document
                target_id, target_name, target_login = None, None, None
                initial_auto, final_auto, total_rewards = False, False, []
                gain, difference = "lost", 0.0
                cost_value = 0
                fish_start, fish_limit = 5, 90
                try:
                    # if chatter_id == id_streamer:
                    if chatter_document['data_games']['fish']['line']['cast'] and not command_check.removeprefix("fish").isdigit():
                        auto_response = ""
                        if chatter_document['data_games']['fish']['auto']['cast'] != 0:
                            auto_response = f" You have {chatter_document['data_games']['fish']['auto']['cast']:,} auto casts remaining."
                        await bot.send_chat_message(id_streamer, id_streamer, f"You have already cast your line, wait a few.{auto_response}", reply_parent_message_id=data.event.message_id)
                        end_timer("fish game already fishing")
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
                            new_cost = difference_casts * fish_auto_cost
                            if new_cost > chatter_document['data_user']['points']:
                                await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points for {new_casts} to be set, need {int(new_cost):,} {bot_name} Points, you have {chatter_document['data_user']['points']:,.2f} {bot_name} Points.", reply_parent_message_id=data.event.message_id)
                                end_timer("fish_auto_cast_not_points")
                                return
                            chatter_document['data_user']['points'] -= new_cost
                            chatter_document['data_games']['fish']['auto']['cast'] = new_casts
                            chatter_document['data_games']['fish']['auto']['cost'] += new_cost
                            chatter_document.save()
                            chatter_document = await get_chatter_document(data)
                            if cap_reached:
                                response_fish_auto_cast = f"You cannot set above 100 AutoCasts, added {difference_casts} for {int(new_cost):,} {bot_name} Points. You now have {chatter_document['data_user']['points']:,.2f} {bot_name} Points."
                            else:
                                response_fish_auto_cast = f"You have added {difference_casts} to your AutoCasts for {int(new_cost):,} {bot_name} Points. You now have {chatter_document['data_user']['points']:,.2f} {bot_name} Points."
                            await bot.send_chat_message(id_streamer, id_streamer, response_fish_auto_cast, reply_parent_message_id=data.event.message_id)
                            end_timer("fish add auto fishing command")
                            return
                        else:
                            auto_casts = int(command_check.removeprefix("fish"))
                            if auto_casts <= 0:
                                await bot.send_chat_message(id_streamer, id_streamer, f"You must choose a number between 1 and 50!!", reply_parent_message_id=data.event.message_id)
                                end_timer("fish auto cast need more than 1 command")
                                return
                            elif auto_casts > 100:
                                await bot.send_chat_message(id_streamer, id_streamer, f"You can only go for a maximum of 100", reply_parent_message_id=data.event.message_id)
                                end_timer("fish add auto fishing command too many attempt")
                                return
                            cost = auto_casts * fish_auto_cost
                            if chatter_document['data_user']['points'] >= cost:
                                initial_auto = True
                                chatter_document['data_games']['fish']['auto']['cast'] = auto_casts
                                chatter_document['data_games']['fish']['auto']['cost'] = cost
                                chatter_document['data_user']['points'] -= cost
                                chatter_document.save()
                                chatter_document = await get_chatter_document(data)
                                await bot.send_chat_message(id_streamer, id_streamer, f"You have successfully set your auto cast to {auto_casts:,} for {cost:,} {bot_name} Points. You now have {chatter_document['data_user']['points']:,.2f} {bot_name} Points.", reply_parent_message_id=data.event.message_id)
                            else:
                                await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points for that. Need {cost:,} and you have {chatter_document['data_user']['points']:,.2f}", reply_parent_message_id=data.event.message_id)
                                end_timer("fish auto cast not enuff points")
                                return
                    elif chatter_id == id_streamer and command_check.removeprefix("fish") != "":
                        fist_start, fish_limit = 30, 180
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
                        target_id, target_name, target_login = chatter_document['_id'], chatter_document['name'], chatter_document['data_user']['login']
                    chatter_document['data_games']['fish']['line']['cast'] = True
                    chatter_document.save()
                    # chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    await asyncio.sleep(random.randint(fish_start, fish_limit))
                    # chatter_document['data_games']['fish']['line']['cast'] = False
                    # chatter_document.save()
                    # chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    with open("data/fish_rewards", "r") as file:
                        fish_rewards = file.read()
                    fish_rewards = list(map(str, fish_rewards.splitlines()))
                    fish = random.choice(fish_rewards)
                    fish, value = fish.split(",")
                    raw_value = float(value)
                    fish_response = f"caught {fish} worth {raw_value:,} point{'s' if raw_value != 1 else ''}"
                    chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    line_cut = False
                    if chatter_document['data_games']['fish']['line']['cut']:
                        line_cut = True
                        old_fish = fish
                        fish = f"line was cut by {chatter_document['data_games']['fish']['line']['cut_by']} loosing a {old_fish} worth {value}"
                        fish_response = f"line was cut by {chatter_document['data_games']['fish']['line']['cut_by']} loosing a {old_fish} worth {value}"
                        value, raw_value = 0, 0
                        chatter_document['data_games']['fish']['line']['cut'] = False
                        chatter_document['data_games']['fish']['line']['cut_by'] = ""
                        chatter_document.save()
                        chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    total_gained, total_lost = chatter_document['data_games']['fish']['auto']['gain'], chatter_document['data_games']['fish']['auto']['lost']
                    if not line_cut and fish == "a Free2Escape Jail Card":
                        if chatter_document['data_games']['jail']['escapes'] == 0:
                            fish_response += f" | You keep it not gaining any points"
                            value, raw_value = 0, 0
                            chatter_document['data_games']['jail']['escapes'] += 1
                        else:
                            fish_response += f" | You already have one saved"
                    if float(value) < 0:
                        value = abs(float(value))
                        add = False
                        total_lost += raw_value
                    else:
                        value = float(value)
                        add = True
                        total_gained += raw_value
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, value, add)
                    if chatter_document['data_games']['fish']['auto']['cast'] > 0 and not initial_auto:
                        def rewards(fish: str, value: float):
                            return f"{fish}/{value:,.2f}"
                        chatter_document['data_games']['fish']['auto']['cast'] -= 1
                        if chatter_document['data_games']['fish']['auto']['cast'] == 0:
                            final_auto = True
                            total_rewards = chatter_document['data_games']['fish']['auto']['rewards']
                            cost_value = chatter_document['data_games']['fish']['auto']['cost']
                            total_rewards.append(rewards(fish, raw_value))
                            chatter_document['data_games']['fish']['auto']['cast'] = 0
                            chatter_document['data_games']['fish']['auto']['cost'] = 0
                            chatter_document['data_games']['fish']['auto']['gain'] = 0.0
                            chatter_document['data_games']['fish']['auto']['lost'] = 0.0
                            chatter_document['data_games']['fish']['auto']['rewards'] = []
                        else:
                            chatter_document['data_games']['fish']['auto']['gain'] = total_gained
                            chatter_document['data_games']['fish']['auto']['lost'] = total_lost
                            chatter_document['data_games']['fish']['auto']['rewards'].append(rewards(fish, raw_value))
                    chatter_document['data_games']['fish']['line']['cast'] = False
                    chatter_document.save()
                    chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    if chatter_document['data_games']['fish']['auto']['cast'] > 0:
                        await bot.send_chat_message(id_streamer, id_streamer, f"!fish {chatter_document['name']} | You{'r' if line_cut else ''} {fish_response}! Your new points are: {chatter_document['data_user']['points']:,.2f}{f' {response_level}' if response_level is not None else ''}. You have {chatter_document['data_games']['fish']['auto']['cast']} Auto Casts Remaining.")
                    elif final_auto:
                        difference = (total_gained + total_lost) - cost_value
                        if difference > 0:
                            gain = "gained"
                        elif difference == 0:
                            gain = ""
                        response_auto = f"Auto Cast Expired! You {f'{gain} {abs(difference):,.2f} points' if gain != '' else f'broke even from the Auto-Cast Cost ({cost_value:,})'} from {len(total_rewards)} casts."  # points with; {', '.join(total_rewards)}")
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_document['name']} you{'r' if line_cut else ''} {fish_response}! Your new points are: {chatter_document['data_user']['points']:,.2f}.{f' {response_level}.' if response_level is not None else ''} {response_auto}")
                        special_logger.info(f"{fortime()}: AUTO CAST EXPIRED FOR {chatter_document['name']}\n{response_auto}")
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_document['name']} you{'r' if line_cut else ''} {fish_response}! Your new points are: {chatter_document['data_user']['points']:,.2f}.{f' {response_level}.' if response_level is not None else ''}")
                    # else:
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"Temp Not Avail")
                # ToDo: Monitor Below...
                except TwitchBackendException:
                    await asyncio.sleep(1)
                    try:
                        chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                        if chatter_document['data_games']['fish']['auto']['cast'] > 0 or final_auto:
                            await bot.send_chat_message(id_streamer, id_streamer, f"!fish {chatter_document['name']} | Your Cast Message failed to send. Your last caught item was; {chatter_document['data_games']['fish']['line']['rewards'][-1]}. You have {chatter_document['data_games']['fish']['auto']['cast'] if not final_auto else 'no'} casts left")
                        else:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_document['name']} your cast message failed to send. Your current points are {chatter_document['data_user']['points']:,.2f}")
                        logger.info(f"{fortime()}: TwitchBackendException handled OK. -- {chatter_document['name']}'s fish message")
                        end_timer("fish command retry server error success")
                        return
                    except Exception as g:
                        logger.error( f"{fortime()}: Error in on_stream_chat_message -- fish command -- TwitchBackendException handled FAIL -- {g}")
                        end_timer("fish command TwitchBackendException handled FAIL")
                        return
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- fish command -- {f}")
                    end_timer("fish command")
                    return
            elif command_check.startswith("gamble"):
                try:
                    bet_value = command.removeprefix("gamble ")
                    if bet_value.isdigit():
                        bet_value = int(bet_value)
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Your command should resemble '{f' or '.join(cmd)}' gamble X where X, put your bet value. Try again", reply_parent_message_id=data.event.message_id)
                        end_timer("gamble command")
                        return
                    # if chatter_document['data_games']['gamble'] is None:
                    #     pass
                    # elif await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(chatter_document['data_games']['gamble'])) < 600:
                    #     await bot.send_chat_message(id_streamer, id_streamer, f"You have to wait {datetime.timedelta(seconds=abs(600 - (await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(chatter_document['data_games']['gamble'])))))} to use thee command again")
                    print(f"{bet_value} vs {chatter_document['data_user']['points']}")
                    if bet_value > chatter_document['data_user']['points']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You do not have enough points to bet that. You currently have {chatter_document['data_user']['points']:,.2f}", reply_parent_message_id=data.event.message_id)
                        end_timer("gamble command")
                        return
                    elif bet_value <= chatter_document['data_user']['points']:
                        chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, bet_value, False, True)
                        if pr.prob(99.95/100):
                            response_gamble = f"lost {bet_value:,}"
                            await bot.send_chat_message(id_streamer, id_streamer, f"You lost thee gamble, I ate your points. They tasted yummy! You now have {chatter_document['data_user']['points']:,.2f} points.", reply_parent_message_id=data.event.message_id)
                        else:
                            won_amount = bet_value * 100000
                            response_gamble = f"won {won_amount:,} with a bet of {bet_value:,}"
                            chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, won_amount)
                            await bot.send_chat_message(id_streamer, id_streamer, f"You won thee gamble, winning {won_amount:,} making your new total {chatter_document['data_user']['points']:,.2f}!! Congratz!!!", reply_parent_message_id=data.event.message_id)
                        gamble_logger.info(f"{fortime()}: {chatter_id}/{chatter_username} gambled and {response_gamble}.")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - gamble command -- {f}")
                    gamble_logger.error(f"{fortime()}: Error in on_stream_chat_message - gamble command -- {f}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong, TheeChody will fix it sooner than later. Error logged in thee background", reply_parent_message_id=data.event.message_id)
                    end_timer("gamble command")
                    return
            elif command_check.startswith("iq"):
                try:
                    now_time = datetime.datetime.now()
                    if command.replace(" ", "").removeprefix("iq").startswith("history"):
                        response_iq = []
                        for entry in reversed(chatter_document['data_games']['iq']['history'][-10:]):
                            response_iq.append(str(entry))
                        await bot.send_chat_message(id_streamer, id_streamer, f"Your last 10 IQ's were; {' | '.join(response_iq)}", reply_parent_message_id=data.event.message_id)
                        end_timer("iq command history")
                        return
                    elif chatter_document['data_games']['iq']['last'] is None:
                        pass
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
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- iq command -- {f}")
                    end_timer("iq command error")
                    return
            elif command_check.startswith("jail"):
                try:
                    now_time = datetime.datetime.now()
                    if chatter_document['data_user']['points'] < jail_cost:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you don't have enough points! Need {jail_cost:,} points, you have {chatter_document['data_user']['points']:,.2f} points.")
                        end_timer("jail command - not enuff points")
                        return
                    elif chatter_document['data_games']['jail']['last'] is None:
                        pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])) < jail_wait_time:
                        wait_time = jail_wait_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you cannot attempt to jail someone right now as you're on 'Probation' and will have to wait {str(datetime.timedelta(seconds=wait_time)).title()} till it expires.")
                        end_timer("jail command - been in jail, cannot attempt")
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
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you cannot attempt to jail {name_streamer} or StreamLootsBot", reply_parent_message_id=data.event.message_id)
                        end_timer("jail command - target not valid -- streamer/streamloots bot")
                        return
                    target_document = await get_chatter_document(None, channel_document, target.user_id, target.user_name, target.user_login, id_streamer, name_streamer)
                    if target_document is None:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name}'s document couldn't be loaded!!! Aborting jail attempt.", reply_parent_message_id=data.event.message_id)
                        return
                    elif target_document['data_games']['jail']['last'] is None:
                        pass
                    elif target_document['data_games']['jail']['in']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} is already in jail right now!!", reply_parent_message_id=data.event.message_id)
                        return
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['last'])) < jail_wait_time:
                        wait_time = jail_wait_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['last'])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} has been jailed too recently to attempt, must wait {str(datetime.timedelta(seconds=wait_time)).title()}. Aborting jail attempt.")
                        return
                    chatter_document['data_user']['points'] -= jail_cost
                    chatter_document.save()
                    chatter_document = await get_chatter_document(data)
                    if pr.prob(80/100) or chatter_id == id_streamer:
                        if target_document['data_games']['jail']['escapes'] > 0:
                            target_document['data_games']['jail']['escapes'] -= 1
                            target_document.save()
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} had a 'Free2Escape Jail Card' and escapes {chatter_username}'s jail attempt!!", reply_parent_message_id=data.event.message_id)
                            end_timer("jail attempt escaped")
                            return
                        target_document['data_games']['jail']['in'] = True
                        target_document['data_games']['jail']['last'] = now_time
                        target_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} jailed {target.user_name} for {datetime.timedelta(seconds=jail_time)}!! {chatter_username} you now have {chatter_document['data_user']['points']:,.2f} points.", reply_parent_message_id=data.event.message_id)
                        await bot.ban_user(id_streamer, id_streamer, target.user_id, f"You've been jailed by {chatter_username} for {datetime.timedelta(seconds=jail_time)}.", jail_time)
                        await asyncio.sleep(jail_time + 1)
                        target_document = await get_chatter_document(None, channel_document, target.user_id, target.user_name, target.user_login, id_streamer, name_streamer)
                        target_document['data_games']['jail']['in'] = False
                        target_document.save()
                        if target.user_id in channel_document['data_lists']['mods']:
                            await bot.add_channel_moderator(id_streamer, target.user_id)
                    else:
                        chatter_document['data_games']['jail']['in'] = True
                        chatter_document['data_games']['jail']['last'] = now_time
                        chatter_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} attempted to jail {target.user_name} for {datetime.timedelta(seconds=jail_time)} but was caught in thee act and was instead jailed themselves!! {chatter_username} you now have {chatter_document['data_user']['points']:,.2f} points.", reply_parent_message_id=data.event.message_id)
                        await bot.ban_user(id_streamer, id_streamer, chatter_id, f"You've been jailed for your attempt to jail {target.user_name} for {datetime.timedelta(seconds=jail_time)}.", jail_time)
                        await asyncio.sleep(jail_time + 1)
                        chatter_document = await get_chatter_document(data)
                        chatter_document['data_games']['jail']['in'] = False
                        chatter_document.save()
                        if chatter_id in channel_document['data_lists']['mods']:
                            await bot.add_channel_moderator(id_streamer, chatter_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- jail command -- {f}")
                    end_timer("jail command - error")
                    return
            elif command_check.startswith("pants"):
                try:
                    if command.replace(" ", "").replace("pants", "").startswith("@"):
                        target_user_name = command.replace(" ", "").replace("pants@", "")
                        target = await select_target(channel_document, chatter_id, True, target_user_name, "pants")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target_user_name} isn't a valid target!")
                            end_timer("pants command")
                            return
                    else:
                        target = await select_target(channel_document, chatter_id, game_type="pants")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"Couldn't locate a valid target!!", reply_parent_message_id=data.event.message_id)
                            end_timer("pants command")
                            return
                    with open("data/pants_choices", "r") as file:
                        pants_options = file.read()
                    pants_options = list(map(str, pants_options.splitlines()))
                    pants_choice = random.choice(pants_options)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} pulls down thee pants of {target.user_name} whom is {pants_choice}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- pants command -- {f}")
                    end_timer("pants command")
                    return
            elif command_check.startswith("pp"):
                async def already_done():
                    size = chatter_document['data_games']['pp'][0]
                    await bot.send_chat_message(id_streamer, id_streamer, f"You've already checked your pp size today, it's a {f'{size} inch pecker' if size > 0 else f'{size} inch innie'}", reply_parent_message_id=data.event.message_id)
                    end_timer("pp_already command")
                try:
                    now_time = datetime.datetime.now()
                    if command.replace(" ", "").removeprefix("pp").startswith("history"):
                        response_pp = []
                        if chatter_id == "627417784":  # Chrispy's ID
                            final_response = "".join(chatter_document['data_games']['pp'][2])
                        else:
                            # pp_history = sorted(chatter_document['data_games']['pp'][2], reverse=False)
                            for entry in reversed(chatter_document['data_games']['pp'][2][-10:]):
                                response_pp.append(f"{entry} inch pecker" if entry > 0 else f"{entry} inch innie")

                            final_response = f"Your last 10 pp sizes were: {' | '.join(response_pp)}"
                        await bot.send_chat_message(id_streamer, id_streamer, final_response, reply_parent_message_id=data.event.message_id)
                        end_timer("pp_history command")
                        return
                    elif chatter_id == "627417784":  # Chrispy's ID
                        size = -69
                        chatter_document['data_games'].update(pp=[size, now_time, ["Always -69 inches depth"]])
                        chatter_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} is The King of Thee Innie's, as such has Thee Deepest of Deep Innie's at {size} inch innie")
                        end_timer("pp_moist command")
                        return
                    elif chatter_document['data_games']['pp'][0] is None:
                        pass
                    elif now_time.day == chatter_document['data_games']['pp'][1].day:
                        if now_time.month == chatter_document['data_games']['pp'][1].month:
                            if now_time.year == chatter_document['data_games']['pp'][1].year:
                                await already_done()
                                return
                    #         else:
                    #             pass
                    #     else:
                    #         pass
                    # else:
                    #     await already_done()
                    #     return
                    size = random.randint(-4, 18)
                    new_history = chatter_document['data_games']['pp'][2]
                    new_history.append(size)
                    chatter_document['data_games'].update(pp=[size, now_time, new_history])
                    chatter_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username}'s packin' a {f'{size} inch pecker' if size > 0 else f'{size} inch innie'}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- pp command -- {f}")
                    end_timer("pp command")
                    return
            elif command_check.startswith("slap"):
                try:
                    if command.replace(" ", "").replace("slap", "").startswith("@"):
                        target_user_name = command.replace(" ", "").replace("slap@", "")
                        target = await select_target(channel_document, chatter_id, True, target_user_name, "slap")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"{target_user_name} isn't a valid target!")
                            end_timer("slap command")
                            return
                    else:
                        target = await select_target(channel_document, chatter_id, game_type="slap")
                        if target is None:
                            await bot.send_chat_message(id_streamer, id_streamer, f"Couldn't locate a valid target!!", reply_parent_message_id=data.event.message_id)
                            end_timer("slap command")
                            return
                    with open("data/slap_choices", "r") as file:
                        slap_options = file.read()
                    slap_options = list(map(str, slap_options.splitlines()))
                    slap_choice = random.choice(slap_options)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} slaps {target.user_name} {slap_choice.format(chatter_username)}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- pants command -- {f}")
                    end_timer("pants command")
                    return
            elif command_check.startswith("tag"):
                try:
                    re_tag = False
                    if command.replace(" ", "").removeprefix("tag").startswith(("history", "stats")):
                        await bot.send_chat_message(id_streamer, id_streamer, f"Your tag stats are (Total/Valid/Fail): {chatter_document['data_games']['tag'][0]}/{chatter_document['data_games']['tag'][1]}/{chatter_document['data_games']['tag'][2]}", reply_parent_message_id=data.event.message_id)
                        end_timer("tag history command")
                        return
                    rem_response, target_rem_response, response_level = None, None, None
                    if chatter_id in channel_document['data_lists']['non_tag']:
                        channel_document['data_lists']['non_tag'].remove(chatter_id)
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                        rem_response = f"You have been removed from thee untag list"
                    if channel_document['data_games']['tag'][0] is None:
                        last_tag_id, last_tag_name, time_since_tagged = chatter_id, chatter_username, datetime.datetime.now()
                    else:
                        last_tag_id, last_tag_name, time_since_tagged = channel_document['data_games']['tag'][0], channel_document['data_games']['tag'][1], await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(channel_document['data_games']['tag'][2]))
                    if chatter_id != last_tag_id and time_since_tagged < 120:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are not last tagged, {last_tag_name} is last to be tagged. {abs(time_since_tagged - 120)} seconds till able to tag.{f' {rem_response}' if rem_response is not None else ''}", reply_parent_message_id=data.event.message_id)
                        end_timer("tag command")
                        return
                    else:
                        while True:
                            target = await select_target(channel_document, chatter_id)
                            if target is None:
                                channel_document['data_games'].update(tag=[None, None, None])
                                channel_document.save()
                                await bot.send_chat_message(id_streamer, id_streamer, f"Error fetching a random tag target.. Are we thee only ones here??{f' {rem_response}.' if rem_response is not None else ''}{f' {target_rem_response}.' if target_rem_response is not None else ''}")
                                end_timer("tag command")
                                return
                            elif chatter_id != last_tag_id and last_tag_id != "":
                                if last_tag_id not in channel_document['data_lists']['non_tag']:
                                    prior_target_chatter_doc = Users.objects.get(_id=last_tag_id)
                                    channel_document['data_lists']['non_tag'].append(last_tag_id)
                                    channel_document['data_games'].update(tag=[None, None, None])
                                    channel_document.save()
                                    channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                                    last_tag_id = ""
                                    target_rem_response = f"{prior_target_chatter_doc['name']} has been added to untag list"  #" and lost 5 XP"
                                    # await twitch_points_transfer(prior_target_chatter_doc, channel_document, 0, False)
                                    await update_tag_stats(prior_target_chatter_doc, 1, 0, 1)
                            elif chatter_id == last_tag_id or last_tag_id == "":
                                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, 2.5)
                                chatter_document, response_tag = await update_tag_stats(chatter_document, 1, 1, 0)
                                break
                        channel_document['data_games'].update(tag=[target.user_id, target.user_name, datetime.datetime.now()])
                        channel_document.save()
                        if target is not None:
                            if target.user_id == id_streamer:
                                re_tag = True
                        await bot.send_chat_message(id_streamer, id_streamer, f"{'!tag ' if re_tag else ''}{chatter_username} tags {target.user_name}{f' {rem_response}.' if rem_response is not None else '.'}{f' {target_rem_response}' if target_rem_response is not None else ''}{f' {response_tag}.' if response_tag is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- tag command -- {f}")
                    end_timer("tag command")
                    return
            elif command_check.startswith(("notag", "untag")):
                try:
                    if chatter_id not in channel_document['data_lists']['non_tag']:
                        channel_document['data_lists']['non_tag'].append(chatter_id)
                        channel_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are now out of thee tag game", reply_parent_message_id=data.event.message_id)
                    elif chatter_id in channel_document['data_lists']['non_tag']:
                        channel_document['data_lists']['non_tag'].remove(chatter_id)
                        channel_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are now back in thee tag game", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- untag command -- {f}")
                    end_timer("untag command")
                    return
            # Counter Commands
            elif command_check.startswith("atscount"):
                try:
                    if chatter_id == id_streamer or chatter_id in channel_document['data_lists']['mods']:
                        tractor, game = 0, 0
                        if command.replace(" ", "").removeprefix("atscount").isdigit():
                            value = int(command.replace(" ", "").removeprefix("atscount"))
                            tractor += value
                        elif command.replace(" ", "").removeprefix("atscount").startswith("-"):
                            if command.replace(" ", "").removeprefix("atscount-").isdigit():
                                value = int(f"-{int(command.replace(' ', '').removeprefix('atscount-'))}")
                                tractor += value
                            else:
                                logger.error(f"{fortime()}: Error in on_stream_chat_message atscount command -- value isn't a digit -- {command} -- {command.replace(' ', '').removeprefix('atscount-')}")
                                end_timer("atscount command")
                                return
                        elif command.replace(" ", "").removeprefix("atscount").startswith("crash"):
                            game += 1
                        elif command.replace(" ", "").removeprefix("atscount").startswith("reset"):
                            tractor = int(f"-{channel_document['data_counters']['ats'][0]}")
                            game = int(f"-{channel_document['data_counters']['ats'][1]}")
                        new_tractor = channel_document['data_counters']['ats'][0] + tractor
                        new_game = channel_document['data_counters']['ats'][1] + game
                        channel_document['data_counters'].update(ats=[new_tractor, new_game])
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    await bot.send_chat_message(id_streamer, id_streamer, f"American Truck Sim Crash Count (Tractor/Game): {channel_document['data_counters']['ats'][0]}/{channel_document['data_counters']['ats'][1]}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message atscount command -- {f}")
                    end_timer("atscount command")
                    return
            elif command_check.startswith("codcount"):
                try:
                    if chatter_id == id_streamer or chatter_id in channel_document['data_lists']['mods']:
                        total, win, lost, crash = 0, 0, 0, 0
                        if command.replace(" ", "").removeprefix("codcount").isdigit():
                            value = int(command.replace(" ", "").removeprefix("codcount"))
                            total += value
                            win += value
                        elif command.replace(" ", "").removeprefix("codcount").startswith("-"):
                            if command.replace(" ", "").removeprefix("codcount-").isdigit():
                                value = int(command.replace(' ', '').removeprefix('codcount-'))
                                total += value
                                lost += value
                            else:
                                logger.error(f"{fortime()}: Error in on_stream_chat_message codcount command -- value isn't a digit -- {command} -- {command.replace(' ', '').removeprefix('codcount-')}")
                                end_timer("codcount command")
                                return
                        elif command.replace(" ", "").removeprefix("codcount").startswith("crash"):
                            crash += 1
                        elif command.replace(" ", "").removeprefix("codcount").startswith("reset"):
                            total = int(f"-{channel_document['data_counters']['cod'][0]}")
                            win = int(f"-{channel_document['data_counters']['cod'][1]}")
                            lost = int(f"-{channel_document['data_counters']['cod'][2]}")
                            crash = int(f"-{channel_document['data_counters']['cod'][3]}")
                        new_total = channel_document['data_counters']['cod'][0] + total
                        new_win = channel_document['data_counters']['cod'][1] + win
                        new_lost = channel_document['data_counters']['cod'][2] + lost
                        new_crash = channel_document['data_counters']['cod'][3] + crash
                        channel_document['data_counters'].update(cod=[new_total, new_win, new_lost, new_crash])
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    await bot.send_chat_message(id_streamer, id_streamer, f"CoD Counter (Matches/Wins/Losses/Crashes): {channel_document['data_counters']['cod'][0]}/{channel_document['data_counters']['cod'][1]}/{channel_document['data_counters']['cod'][2]}/{channel_document['data_counters']['cod'][3]}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message codcount command -- {f}")
                    end_timer("codcount command")
                    return
            elif command_check.startswith("jointscount"):
                try:
                    total = 0
                    response_joints_day_reset, last_smoked, last_smoked_nice = None, None, None
                    if chatter_id == id_streamer or chatter_id in channel_document['data_lists']['mods']:
                        now_time = datetime.datetime.now()
                        if command.replace(" ", "").removeprefix("jointscount").isdigit():
                            value = int(command.replace(" ", "").removeprefix("jointscount"))
                            total += value
                            last_smoked = now_time
                        elif command.replace(" ", "").removeprefix("jointscount").startswith("-"):
                            if command.replace(" ", "").removeprefix("jointscount-").isdigit():
                                value = int(command.replace(' ', '').removeprefix('jointscount-'))
                                total -= value
                                last_smoked = now_time
                            else:
                                logger.error(f"{fortime()}: Error in on_stream_chat_message jointscount command -- value isn't a digit -- {command} -- {command.replace(' ', '').removeprefix('jointscount-')}")
                                end_timer("jointscount command")
                                return
                        elif command.replace(" ", "").removeprefix("jointscount").startswith("reset"):
                            total = int(f"-{channel_document['data_counters']['joints'][0]}")
                            last_smoked = None
                        if total != 0:
                            new_total = channel_document['data_counters']['joints'][0] + total
                            if new_total > 0 and last_smoked is not None and channel_document['data_counters']['joints'][1] is not None:
                                if last_smoked.day != channel_document['data_counters']['joints'][1].day:
                                    new_total, last_smoked = total, now_time
                                    response_joints_day_reset = "New day detected, joints count has been reset."
                            channel_document['data_counters'].update(joints=[new_total, last_smoked])
                            channel_document.save()
                            channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    if channel_document['data_counters']['joints'][1] is not None:
                        if total == 0:
                            last_smoked_nice = channel_document['data_counters']['joints'][1].strftime('%H:%M:%S')
                        else:
                            last_smoked_nice = last_smoked.strftime('%H:%M')
                    await bot.send_chat_message(id_streamer, id_streamer, f"{response_joints_day_reset if response_joints_day_reset is not None else ''} Joints Smoked Count (Total | Last): {channel_document['data_counters']['joints'][0]:,} | {f'{last_smoked_nice} MST' if last_smoked_nice is not None else 'None'}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- jointscount command -- {f}")
                    end_timer("jointscount command")
                    return
            elif command_check.startswith("streamcount"):
                try:
                    if chatter_id == id_streamer or chatter_id in channel_document['data_lists']['mods']:
                        if command.replace(" ", "").removeprefix("streamcount").isdigit():
                            value = int(command.replace(" ", "").removeprefix("streamcount"))
                        elif command.replace(" ", "").removeprefix("streamcount").startswith("-"):
                            if command.replace(' ', '').removeprefix('streamcount-').isdigit():
                                value = int(f"-{int(command.replace(' ', '').removeprefix('streamcount-'))}")
                            else:
                                logger.error(f"{fortime()}: Error in on_stream_chat_message streamcount command -- value isn't a digit -- {command} -- {command.replace(' ', '').removeprefix('streamcount-')}")
                                end_timer("streamcount command")
                                return
                        elif command.replace(" ", "").removeprefix("streamcount").startswith("reset"):
                            value = int(f"-{int(channel_document['data_counters']['stream_crash'])}")
                        else:
                            value = 0
                        new_value = channel_document['data_counters']['stream_crash'] + value
                        channel_document['data_counters']['stream_crash'].update(stream=new_value)
                        channel_document.save()
                        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{marathon_name} Stream Crash Count: {channel_document['data_counters']['stream_crash']}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message streamcount command -- {f}")
                    end_timer("streamcount command")
                    return
            # Marathon Commands
            elif command_check.startswith("freepack"):
                try:
                    now_time = datetime.datetime.now()
                    if chatter_document['data_user']['points'] < free_pack_cost:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points, you need {free_pack_cost:,} and you have {chatter_document['data_user']['points']:,.2f} {bot_name} Points. You currently have {chatter_document['data_user']['dates']['daily_cards'][0]} packs waiting to be sent.", reply_parent_message_id=data.event.message_id)
                        end_timer("freepack Command")
                        return
                    elif chatter_document['data_user']['dates']['daily_cards'][1] is None:
                        pass
                    elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_user']['dates']['daily_cards'][1])) < free_pack_time:
                        wait_time = free_pack_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_user']['dates']['daily_cards'][1])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"You gotta wait {str(datetime.timedelta(seconds=wait_time)).title()} for your next redeem. You currently have {chatter_document['data_user']['dates']['daily_cards'][0]} packs waiting to be sent.", reply_parent_message_id=data.event.message_id)
                        end_timer("freepack command")
                        return
                    chatter_document['data_user']['points'] -= free_pack_cost
                    chatter_document['data_user']['dates']['daily_cards'][0] += 1
                    chatter_document['data_user']['dates']['daily_cards'][1] = now_time
                    chatter_document.save()
                    chatter_document = await get_chatter_document(data)
                    wait_time = free_pack_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_user']['dates']['daily_cards'][1])))
                    await bot.send_chat_message(id_streamer, id_streamer, f"You have redeemed {free_pack_cost:,} {bot_name} Points for 1 Pack of 3 Cards. You now have {chatter_document['data_user']['points']:,.2f} {bot_name} Points. You currently have {chatter_document['data_user']['dates']['daily_cards'][0]} packs waiting to be sent. {str(datetime.timedelta(seconds=wait_time)).title()} till your next redeem.", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- freepack command -- {f}")
                    end_timer(f"freepack command")
                    return
            elif command_check.startswith(("streamloot", "loot", marathon_name.lower(), marathon_name.replace("-", "").lower(), "pack", "coupon")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{link_loots} | Monthly use 20% off coupon: {link_loots_discount}")
                    with open("data/pack_link", "r") as file:
                        link = file.read()
                    response_pack = list(map(str, link.splitlines()))
                    for i in range(0, len(response_pack), 10):
                        await bot.send_chat_message(id_streamer, id_streamer, " | ".join(response_pack[i:i + 10]))
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- loot command -- {f}")
                    end_timer("loot command")
                    return
            elif command_check.startswith(("points4time", "points4timerate")):
                await bot.send_chat_message(id_streamer, id_streamer, f"This command is currently disabled")
                # try:
                #     await bot.send_chat_message(id_streamer, id_streamer, f"Valid times are 10, 20, 30. Cost 10k-10M/18k-20M/26k-30M", reply_parent_message_id=data.event.message_id)
                # except Exception as f:
                #     logger.error(f"{fortime()}: Error in on_stream_chat_message - points4time command -- {f}")
                #     end_timer("points4time command")
                #     return
            elif command_check.startswith(("time2add", "timeadd")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Time that can still be added to thee clock is: {str(datetime.timedelta(seconds=abs(float(read_clock_max()) - float(read_clock_total())))).title()}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timeadd command -- {f}")
                    end_timer("timeadd command")
                    return
            elif command_check.startswith(("timecurrent", "timeremain", "timeleft")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee current time remaining: {str(datetime.timedelta(seconds=int(float(read_clock())))).title()}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timecurrent command -- {f}")
                    end_timer("timecurrent command")
                    return
            elif command_check.startswith(("timemax", "timecap")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee Marathon Cap is: {str(datetime.timedelta(seconds=float(read_clock_max()))).title()}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timemax command -- {f}")
                    end_timer("timemax command")
                    return
            elif command_check.startswith(("timepause", "timepaused")):
                try:
                    time_pause = float(read_clock_pause())
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee timer is {f'currently paused for {str(datetime.timedelta(seconds=time_pause)).title()}' if time_pause != 0.0 else 'not currently paused'}.", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timepause command -- {f}")
                    end_timer("timepause command")
                    return
            elif command_check.startswith(("timerate", "timedown")):
                try:
                    phase = read_clock_phase()
                    if phase == "accel":
                        time_left = float(read_clock_accel_time())
                        response_phase = f"Timer Rate @ {int(strict_pause)} real sec/{int(countdown_rate_strict)} Timer Sec; {str(datetime.timedelta(seconds=time_left)).title()}"
                    elif phase == "slow":
                        time_left = float(read_clock_slow_time())
                        response_phase = f"Timer Rate @ {int(countdown_rate_strict)} real sec/{int(strict_pause)} Timer Sec; {str(datetime.timedelta(seconds=time_left)).title()}"
                    else:
                        response_phase = f"Timer Rate @ 1 Real Sec/1 Timer Sec"
                    await bot.send_chat_message(id_streamer, id_streamer, response_phase, reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timerate command -- {f}")
                    end_timer("timerate command")
                    return
            elif command_check.startswith("timesofar"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee total elapsed time so far is: {str(datetime.timedelta(seconds=float(read_clock_sofar()))).title()}.", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timesofar command -- {f}")
                    end_timer("timesofar command")
                    return
            elif command_check.startswith("time"):
                try:
                    response_throne = f"{standard_seconds * 2} Seconds / Cent Contributed ($1 = {str(datetime.timedelta(seconds=(standard_seconds * 2) * 100)).title()})"
                    response_direct_dono = f"{standard_direct_dono} Seconds / Cent Received ($1 = {str(datetime.timedelta(seconds=standard_direct_dono * 100)).title()})"
                    response_twitch = f"{standard_seconds} Seconds / Cent Received (100 bitties = {str(datetime.timedelta(seconds=standard_seconds * 100)).title()} -- 1 T1 subbie = {str(datetime.timedelta(seconds=standard_seconds * 250)).title()} -- 1 T2 subbie = {str(datetime.timedelta(seconds=standard_seconds * 500)).title()} -- 1 T3 subbie = {str(datetime.timedelta(seconds=standard_seconds * 1250)).title()})"
                    response_streamloots = f"{stream_loots_seconds} Seconds / Cent Received (1 card = {str(datetime.timedelta(seconds=stream_loots_seconds * 100)).title()})"
                    await bot.send_chat_message(id_streamer, id_streamer, f"Throne & TreatStream Contributions; {response_throne} | DirectDono; {response_direct_dono} | Twitch; {response_twitch} | Streamloots; {response_streamloots}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- times command -- {f}")
                    end_timer("times command")
                    return
            # Special Commands
            elif command_check.startswith("ak"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Shooting AK's, While downing shine, Sounds like a decent way to spend thee day", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- ak command -- {f}")
                    end_timer("ak command")
                    return
            elif command_check.startswith(("beckky", "carnage")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"We're going on a trip, in our flavourite rocket ship.. Zooming through thee skies, Little Einsteins!!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- beckky/carnage command -- {f}")
                    end_timer("beckky/carnage command")
                    return
            elif command_check.startswith(("chicken", "xbox", "boxboy")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Love Peace n' Chicken Grease", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- chickenboy command -- {f}")
                    end_timer("chicken(boy) command")
                    return
            elif command_check.startswith(("clammy", "moist")):
                try:
                    if command.replace(" ", "").startswith("clammy"):
                        moist_response = f"First"
                    else:
                        moist_response = f"Second"
                    await bot.send_chat_message(id_streamer, id_streamer, f"Chrispy_Turtle's {moist_response} Flavourite word!!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- clammy/moist command -- {f}")
                    end_timer("clammy/moist command")
                    return
            elif command_check.startswith("dark"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} and me go Throbbin in thee Dark.", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- dark command -- {f}")
                    end_timer("dark command")
                    return
            elif command_check.startswith(("deecoy", "decoy")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "PettyMassacre is thee decoy, toss her in! Let thee rage consume them", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - deecoy command -- {f}")
                    end_timer("deecoy command")
                    return
            elif command_check.startswith("fire"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"@FireGMC08, we gonna need you to turn up thee heat bro, ya skills are freezing cold!! :P", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- fire command -- {f}")
                    end_timer("fire command")
                    return
            elif command_check.startswith("flip"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"(╯°□°）╯︵ ┻━┻", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- flip command -- {f}")
                    end_timer("flip command")
                    return
            elif command_check.startswith("free"):
                try:
                    random_usernames = await bot.get_chatters(id_streamer, id_streamer)
                    target = random.choice(random_usernames.data)
                    await bot.send_chat_message(id_streamer, id_streamer, f"Free2Escape's name is now {target.user_name}. :P", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- free command -- {f}")
                    end_timer("free command")
                    return
            elif command_check.startswith("fuck"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"I'ma bout outta fucks to give. Time to light up me thinks", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- fuck command -- {f}")
                    end_timer("fuck command")
                    return
            elif command_check.startswith(("hug", "chodyhug")):
                try:
                    if command_check.removeprefix("hug").startswith("@"):
                        target_username = command_check.removeprefix("hug@")
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} gives Big Chody Hugs to {target_username}!")
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Big Chody Hugs!!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- hug command -- {f}")
                    end_timer("hug command")
                    return
            elif command_check.startswith("hour"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Tic Tok on thee Clock. Till thee party don't st.. Nopeee", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - hour command -- {f}")
                    end_timer("hour command")
                    return
            elif command_check.startswith("joe"):  # and chatter_id == "806552159":
                try:
                    if chatter_id == "806552159":  # Joe's id
                        response_joe = f"Dammit Me!!! Wait... I mean Dammit Joe!!!"
                    else:
                        response_joe = f"Dammit Joe!!!"
                    await bot.send_chat_message(id_streamer, id_streamer, response_joe, reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - joe command -- {f}")
                    end_timer("joe command")
                    return
            elif command_check.startswith("lore"):  # and chatter_id == "170147951":
                try:
                    if chatter_id == "170147951":  # Maylore's id
                        response_lore = f"Fucking run Chody!! Run! It's Maylore himself here to taunt you"
                    else:
                        response_lore = f"{chatter_username} is taunting you with Maylore's command"
                    await bot.send_chat_message(id_streamer, id_streamer, response_lore, reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - lore command -- {f}")
                    end_timer("lore command")
                    return
            elif command_check.startswith(("moony", "stardust")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Have some star dust on behalf of MoonyStarDust", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- moony command -- {f}")
                    end_timer("moony command")
                    return
            elif command_check.startswith("mullen"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Toasted Crap Is Delicious!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - mullen command -- {f}")
                    end_timer("mullen command")
                    return
            elif command_check.startswith("mull"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Joe Say's \"Its !mullens try again\"", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - mull command -- {f}")
                    end_timer("mull command")
                    return
            elif command_check.startswith("petty"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"🧩 If you know, you know 🧩", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- petty command -- {f}")
                    end_timer("petty command")
                    return
            elif command_check.startswith("pious"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Something badass for sure!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- pious command -- {f}")
                    end_timer("pious command")
                    return
            elif command_check.startswith("queenpenguin"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Queen of Penguins.. Who'm cannot fly", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- queenpenguin command -- {f}")
                    end_timer("queenpenguin command")
                    return
            elif command_check.startswith("ronin"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"RoninGT, his Pettiness, thee Royal Leader of The Petty Squad. https://discord.gg/pettysquad", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- ronin command -- {f}")
                    end_timer("ronin command")
                    return
            elif command_check.startswith("rubi"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "Shine bright like a dia... RUBI!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - rubi command -- {f}")
                    end_timer("rubi command")
                    return
            elif command_check.startswith(("sarah", "rexarah", "fuckinggiggity", "giggity", "rawr")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "rexara1Giggity rexara1Wink rexara1Giggity rexara1Wink", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - sarah command -- {f}")
                    end_timer("sarah command")
                    return
            elif command_check.startswith(("shat", "shathiris")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Guess who's back back back.. Back again gain gain.. TheeShat is back back back... {data.event.broadcaster_user_name} better RUN RUN RUN!!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- shat command -- {f}")
                    end_timer("shat command")
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
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- shit command -- {f}")
                    end_timer("shit command")
                    return
            elif command_check.startswith("silencer"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name} be sneaky like silencer56", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - silencer command -- {f}")
                    end_timer("silencer command")
                    return
            elif command_check.startswith("toodles"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, "TTTOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOODDDDDDDDDDDDDDDLLLLLLLLLLLLLLEEEEEEEEEEEESSSSSSSSSSSSSSSSSSSSSSSSSS", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - toodles command -- {f}")
                    end_timer("toodles command")
                    return
            elif command_check.startswith("vanish"):
                try:
                    await bot.ban_user(id_streamer, id_streamer, chatter_id, f"{chatter_username} vanishes", 1)
                    if chatter_id in channel_document['data_lists']['mods']:
                        await asyncio.sleep(2)
                        await bot.add_channel_moderator(id_streamer, chatter_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- vanish command -- {f}")
                    end_timer("vanish command")
                    return
            elif command_check.startswith("whoudini"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Whoooo.. Whoooooo... Whoooooooooooooooooooooooooooo", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - whoudini command -- {f}")
                    end_timer("whoudini command")
                    return
            elif command_check.startswith("willsmash"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Hul... Will Smash!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - willsmash command -- {f}")
                    end_timer("willsmash command")
                    return
            # Mod Commands
            elif command_check.startswith("resetobs") and (chatter_id in channel_document['data_lists']['mods'] or chatter_id == id_streamer):
                try:
                    change_colour_eq("Reset")
                    await change_webcam("reset")
                    await bot.send_chat_message(id_streamer, id_streamer, f"OBS filters reset to default values", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- resetobs command -- {f}")
                    end_timer("resetobs command")
                    return
            elif command_check.startswith("shutdown") and (chatter_id in channel_document['data_lists']['mods'] or chatter_id == id_streamer):
                try:
                    logger.info(f"{fortime()}: {data.event.chatter_user_name} is attempting to shut me down!! {data.event.message.text}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Attempting to shut down", reply_parent_message_id=data.event.message_id)
                    obs.disconnect()
                    sys._exit(666)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- shutdown command -- {f}")
                    end_timer("shutdown command")
                    return
            # Un-Listed Commands
            elif command_check.startswith("addtime") and chatter_id in (id_streamer, id_streamloots):
                try:
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
                    else:
                        time_value, name = time_value.split("by", maxsplit=1)
                        name, _ = name.split("via")
                        if not time_value.isdigit():
                            logger.error(f"{fortime()}: {time_value}, {type(time_value)}, not valid")
                            end_timer("addtime command")
                            return
                        time_add = float(time_value)
                    if channel_document['data_channel']['hype_train']['current']:
                        time_add = check_hype_train(channel_document, time_add)
                    seconds, time_not = write_clock(time_add, True, obs)
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}", reply_parent_message_id=data.event.message_id)
                    special_logger.info(f"timeadded -- {datetime.timedelta(seconds=int(seconds))} -- {seconds} by {chatter_username}{f' -- MAX TIME HIT {time_not} not added.' if time_not is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - addtime command -- {f}")
                    end_timer("addtime command")
                    return
            elif command_check.startswith("remtime") and chatter_id in (id_streamer, id_streamloots):
                try:
                    time_value = command.replace(" ", "").replace("remtime", "")
                    time_value, name = time_value.split("by", maxsplit=1)
                    name, _ = name.split("via", maxsplit=1)
                    if not time_value.isdigit():
                        print(time_value, type(time_value), "not valid")
                        return
                    time_rem = float(time_value)
                    if channel_document['data_channel']['hype_train']['current']:
                        time_rem = check_hype_train(channel_document, time_rem)
                    seconds, time_not = write_clock(time_rem, False, obs)
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} removed {datetime.timedelta(seconds=int(seconds))} from thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}", reply_parent_message_id=data.event.message_id)
                    special_logger.info(f"timeadded -- {datetime.timedelta(seconds=int(seconds))} -- {seconds} by {chatter_username}{f' -- MAX TIME HIT {time_not} not added.' if time_not is not None else ''}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- remtime command -- {f}")
                    end_timer("remtime command")
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
                        new_time = write_clock_accel_time(last_time)
                    elif phase == "slow":
                        if float(read_clock_slow_time()) == 0:
                            write_clock_slow_rate_time(countdown_rate_strict)
                        write_clock_phase(phase)
                        new_time = write_clock_slow_time(float(last_time))
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
                    set_timer_rate(obs, new_time)
                    obs.set_source_visibility(obs_timer_scene, obs_timer_rate, True)
                    last_time, new_rate = last_time, new_rate
                    points_add = last_time * new_rate
                    # if channel_document['data_channel']['hype_train']['current']:
                    #     points_add = check_hype_train(channel_document, points_add)
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, points_add)
                    response_changerate = f"{name} has set Thee Timer Rate to; {new_rate if phase == 'slow' else '1'} Real Sec/{'1' if phase == 'slow' else new_rate} Timer Sec for; {str(datetime.timedelta(seconds=last_time)).title()}.{f' {str(datetime.timedelta(seconds=new_time)).title()} now remaining.' if new_time != last_time else ''}"
                    special_logger.info(f"{fortime()}: {response_changerate}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"{response_changerate}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                    # while True:
                    #     await asyncio.sleep(float(read_clock_accel_time()) + float(read_clock_slow_time()))
                    #     if float(read_clock_accel_time()) + float(read_clock_slow_time()) == 0:
                    #         obs.set_source_visibility(obs_timer_scene, obs_timer_rate, False)
                    #         break
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- {f}")
                    end_timer("changerate command")
                    return
            elif command_check.startswith("pausetime") and chatter_id in (id_streamer, id_streamloots):  # ToDo: Re Work Thee WhileTrue To Properly adjust if not in accel down mode when started..
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} paused thee timer for {str(datetime.timedelta(seconds=time_pause)).title()}.{f' Timer paused for a total of {str(datetime.timedelta(seconds=int(total_pause))).title()}.' if time_pause != total_pause else ''}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                    # while True:  # ToDo: Maybe else will if over a period of time (eg 1 hour) will then / 2 and keep trying to account for if accel down card played after already sleep
                    #     phase = read_clock_phase()
                    #     if phase == "accel":
                    #         sleep_time = (float(read_clock_accel_time()) / countdown_rate_strict) + 1
                    #         special_logger.info(f"{fortime()}: Sleeping in pause function for {sleep_time};; Time left on pause; {float(read_clock_pause())};; Phase; {phase}")
                    #         await asyncio.sleep(sleep_time)
                    #     elif phase == "slow":
                    #         sleep_time = (float(read_clock_slow_time()) * countdown_rate_strict) + 1
                    #         special_logger.info(f"{fortime()}: Sleeping in pause function for {sleep_time};; Time left on pause; {float(read_clock_pause())};; Phase; {phase}")
                    #         await asyncio.sleep(sleep_time)
                    #     else:
                    #         sleep_time = total_pause + 1
                    #         special_logger.info(f"{fortime()}: Sleeping in pause function for {sleep_time};; Time left on pause; {float(read_clock_pause())};; Phase; {phase}")
                    #         await asyncio.sleep(sleep_time)
                    #     pause_time = float(read_clock_pause())
                    #     if pause_time == 0:
                    #         obs.set_source_visibility(obs_timer_scene, obs_timer_pause, False)
                    #         special_logger.info(f"{fortime()}: Breaking pause loop and turning off OBS filter")
                    #         break
                    #     else:
                    #         total_pause = float(read_clock_pause())
                    #         special_logger.info(f"{fortime()}: Sleeping in pause function for {total_pause};; Time left on pause; {pause_time};; Phase; {phase}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- pausetime command -- {f}")
                    end_timer("pausetime command")
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
                    with open(clock_direction, "w") as file:
                        file.write("up")
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, time_value)
                    special_logger.info(f"{fortime()}: Count Up -- Old Value; {old_value} -- New Value; {total_direct_time} -- By; {name} -- Via; {origin}")
                    set_timer_count_up(obs, total_direct_time)
                    obs.set_source_visibility(obs_timer_scene, obs_timer_countup, True)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} {f'made thee timer count UP for {datetime.timedelta(seconds=time_value)}' if time_value == total_direct_time else f'added {datetime.timedelta(seconds=time_value)} to thee timer counting UP. Total time left {datetime.timedelta(seconds=total_direct_time)}'}.{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                    # while True:
                    #     await asyncio.sleep(float(read_clock_up_time()))
                    #     if float(read_clock_up_time()) == 0:
                    #         obs.set_source_visibility(obs_timer_scene, obs_timer_countup, False)
                    #         break
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- directtime command -- {f}")
                    end_timer("directtime command")
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
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- addlurk command -- {f}")
                    end_timer("addlurk command")
                    return
            elif command_check.startswith("clearlists") and chatter_id == id_streamer:
                try:
                    channel_document['data_lists'].update(lurk=[], non_tag=[])
                    channel_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"Lurk and Non-Tag List cleared")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- clearlists command -- {f}")
                    end_timer("clearlists command")
                    return
            elif command_check.startswith("rtag") and chatter_id == id_streamer:
                try:
                    response_rtag = None
                    if channel_document['data_games']['tag'][2] is not None:
                        if channel_document['data_games']['tag'][0] not in channel_document['data_lists']['non_tag']:
                            channel_document['data_lists']['non_tag'].append(channel_document['data_games']['tag'][0])
                            response_rtag = f"{channel_document['data_games']['tag'][1]} has been moved to thee untag list"
                    channel_document['data_games'].update(tag=[None, None, None])
                    channel_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"Tag game reset{f', {response_rtag}' if response_rtag is not None else '.'}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- tagreset command -- {f}")
                    end_timer("tagreset command")
                    return
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
                except Exception as f:
                    print(f)
            end_timer(f"{command} command")
        else:
            phrase_del = False
            messagecont = data.event.message.text.replace(" ", "").lower()
            try:
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
                if channel_document['data_games']['ranword'] in messagecont:  # ToDo: Future feature full Game, add on screen hints, till then quiet about it
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, 10000)
                    response_ranword = f"You used thee random word!! It was {channel_document['data_games']['ranword']}. You gained 10,000 points!"
                    ran_word(channel_document)
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
                seconds, not_added = write_clock(seconds, True, obs)
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
        logger.error(f"{fortime()}: Error in on_stream_chat_message -- {e}")
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
        response, response_level = "!", None
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        if data.event.is_anonymous:
            chatter_username = "Anonymous"
        else:
            chatter_username = data.event.user_name
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = float((standard_points * data.event.bits) / 2)
                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
        if channel_document['data_channel']['writing_clock']:
            seconds = float(standard_seconds * data.event.bits)
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, True, obs)
            response = f", adding {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!!{f' Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}{f' {response_level}.' if response_level is not None else ''}"
        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} has cheered {data.event.bits}{response}")
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
                #     seconds, time_not_added = write_clock(follow_seconds, True, channel_document, obs)
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
        try:
            top_contributors = data.event.top_contributions
            special_logger.info(f"{fortime()}:HypeTrainEnd TopContributors -- {len(top_contributors)}")
            for user in top_contributors:
                special_logger.info(f"{fortime()}: {user.user_id}, {user.user_name}, {user.user_login}, {user.type}, {user.total}")
        except Exception as f:
            logger.error(f"{fortime()}: Error in top_contributors test area, passing on -- {f}")
            pass
        special_logger.info(f"Thee Hype EhVent DISABLED" if channel_document['data_channel']['writing_clock'] else f"Hype Train Ended")
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Hype Train Completed @ {data.event.level}!!{f' New local record reached at {new_hype_train_record_level}!!' if record_beat else ''}{f' Thee Hype EhVent is now over, all contributions to thee clock have returned to normal.' if channel_document['data_channel']['writing_clock'] else ''} {response_thanks}", color="orange")
        channel_document['data_channel']['hype_train'].update(current=False, current_level=1, last=fortime(),
                                                              last_level=data.event.level, record_level=new_hype_train_record_level)
        channel_document.save()
        if channel_document['data_channel']['writing_clock']:
            set_hype_ehvent(obs, standard_ehvent_mult, "Disabled")
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
            await bot.send_chat_announcement(id_streamer, id_streamer, f"New Hype Train Level!! Currently @ {data.event.level}.{response}", color="purple")
            special_logger.info(f"New Hype Train Level!! Currently @ {data.event.level}.{response}")
            channel_document['data_channel']['hype_train'].update(current_level=new_hype_train_current_level)
            channel_document.save()
            if channel_document['data_channel']['writing_clock']:
                mult = check_hype_train(channel_document, None)
                set_hype_ehvent(obs, mult)
                response_writing_to_log = f"New Hype EhVent Level -- {mult:.1f}X -- {data.event.level} -- {response}"
            else:
                response_writing_to_log = f"New Hype Train Level!! Currently @ {data.event.level} -- {response}"
        else:
            response_writing_to_log = f"New Hype Train Level!! Currently @ {data.event.level} -- {response}"
            new_hype_train_current_level = channel_document['data_channel']['hype_train']['current_level']
        special_logger.info(response_writing_to_log)
        channel_document['data_channel']['hype_train'].update(current_level=new_hype_train_current_level)
        channel_document.save()
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
        chatter_username = data.event.user_name
        check_in, multiple_spin, jail = True, False, False
        response_redemption, response_check_in, times_spun = None, None, None
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        special_logger.info(f"fin--RewardID: {data.event.reward.id} -- {data.event.reward.title}")
        if data.event.reward.title == "Text-to-Speech":
            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} used Text-To-Speech to say; {data.event.user_input}")
            return
        elif data.event.reward.title == "Daily Check-In":
            chatter_document = await get_chatter_document(data, channel_document)
            response_boost, now_time = None, datetime.datetime.now()
            if chatter_document['data_user']['dates']['checkin_streak'][1] is None:
                pass
            # elif await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(chatter_document['data_user']['dates']['checkin_streak'][1])) < cmd_reset_seconds:
            elif now_time.day == chatter_document['data_user']['dates']['checkin_streak'][1].day:
                if now_time.month == chatter_document['data_user']['dates']['checkin_streak'][1].month:
                    if now_time.year == chatter_document['data_user']['dates']['checkin_streak'][1].year:
                        check_in = False
                        response_check_in = f"check-ins are restricted to daily use! :P"
            if check_in:
                new_checkin_streak = chatter_document['data_user']['dates']['checkin_streak'][0] + 1
                if new_checkin_streak % 5 == 0:
                    new_boost = chatter_document['data_rank']['boost'] + 500.0
                    response_boost = f"You now have {new_boost} boosted Experience Points!!"
                else:
                    new_boost = chatter_document['data_rank']['boost']
                chatter_document['data_rank'].update(boost=new_boost)
                chatter_document['data_user']['dates'].update(checkin_streak=[new_checkin_streak, now_time])
                chatter_document.save()
                response_check_in = f"check-in registered. Your next boost is in {abs(5 - new_checkin_streak % 5)} check-ins.{f' {response_boost}' if response_boost is not None else ''}"
        elif data.event.reward.title == "Add 10 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 600
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, True, obs)
            response_redemption = f"added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {data.event.reward.cost:,} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        elif data.event.reward.title == "Add 20 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 1200
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, True, obs)
            response_redemption = f"{chatter_username} added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {data.event.reward.cost:,} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        elif data.event.reward.title == "Add 30 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 1800
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, True, obs)
            response_redemption = f"added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {data.event.reward.cost:,} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        elif data.event.reward.title == "Jail Time":
            try:
                now_time = datetime.datetime.now()
                chatter_document = await get_chatter_document(data)
                if chatter_document['data_games']['jail']['last'] is None:
                    pass
                elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])) < jail_wait_time:
                    wait_time = jail_wait_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['jail']['last'])))
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you cannot attempt to jail someone right now as you're on 'Probation' and will have to wait {str(datetime.timedelta(seconds=wait_time)).title()} till it expires.")
                    return
                jail = True
                chatter_id = data.event.user_id
                target_username = data.event.user_input.removeprefix("@").lower()
                jail_error_msg = f"{chatter_username} tried jailing {target_username} but it didn't work automagically!!"
                if " " in target_username:
                    target_username, _ = target_username.split(" ", maxsplit=1)
                target = await select_target(channel_document, chatter_id, True, target_username, "jail")
                if target is None:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username}, {target_username} is not in chat right now or just joined chat. Try again later")
                    logger.error(f"{fortime()}: Error in channel_point_redemption - timeout (target IS NONE) - jail user\n{data.event}")
                    await bot.send_chat_message(id_streamer, id_streamer, jail_error_msg)
                    return
                elif target.user_id in (id_streamer, id_streamloots):
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} you cannot attempt to jail {name_streamer} or StreamLootsBot. Mods please give back {chatter_username}'s {data.event.reward.cost:,} {channel_point_name} back.")
                    return
                target_document = await get_chatter_document(None, channel_document, target.user_id, target.user_name, target.user_login, id_streamer, name_streamer)
                if target_document is None:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name}'s document couldn't be loaded!!! Aborting jail attempt.")
                    return
                elif target_document['data_games']['jail']['last'] is None:
                    pass
                elif target_document['data_games']['jail']['in']:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} is already in jail right now!!")
                    return
                elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['last'])) < jail_wait_time:
                    wait_time = jail_wait_time - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(target_document['data_games']['jail']['last'])))
                    await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} has been jailed too recently to attempt, must wait {str(datetime.timedelta(seconds=wait_time)).title()}. Aborting jail attempt.")
                    return
                if pr.prob(80/100) or chatter_id == id_streamer:
                    if target_document['data_games']['jail']['escapes'] > 0:
                        target_document['data_games']['jail']['escapes'] -= 1
                        target_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target.user_name} had a 'Free2Escape Jail Card and escapes {chatter_username}'s jail attempt!!")
                        return
                    target_document['data_games']['jail']['in'] = True
                    target_document['data_games']['jail']['last'] = now_time
                    target_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} jailed {target.user_name} for {datetime.timedelta(seconds=jail_time)}!!")
                    await bot.ban_user(id_streamer, id_streamer, target.user_id, f"You've been jailed by {chatter_username} for {datetime.timedelta(seconds=jail_time)}.", jail_time)
                    await asyncio.sleep(jail_time + 1)
                    target_document = await get_chatter_document(None, channel_document, target.user_id, target.user_name, target.user_login, id_streamer, name_streamer)
                    target_document['data_games']['jail']['in'] = False
                    target_document.save()
                    if target.user_id in channel_document['data_lists']['mods']:
                        await bot.add_channel_moderator(id_streamer, target.user_id)
                else:
                    chatter_document['data_games']['jail']['in'] = True
                    chatter_document['data_games']['jail']['last'] = now_time
                    chatter_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} attempted to jail {target.user_name} for {datetime.timedelta(seconds=jail_time)} but was caught in thee act and was instead jailed themselves!!")
                    await bot.ban_user(id_streamer, id_streamer, chatter_id, f"You've been jailed for your attempt to jail {target.user_name} for {datetime.timedelta(seconds=jail_time)}.", jail_time)
                    await asyncio.sleep(jail_time + 1)
                    chatter_document = await get_chatter_document(data)
                    chatter_document['data_games']['jail']['in'] = False
                    chatter_document.save()
                    if chatter_id in channel_document['data_lists']['mods']:
                        await bot.add_channel_moderator(id_streamer, chatter_id)
            except Exception as f:
                logger.error(f"{fortime()}: Error in channel_point_redemption - jail -- {f}")
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
        if not jail:
            await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} {response_check_in if response_check_in is not None else response_redemption if response_redemption is not None else f'used {data.event.reward.cost:,} {channel_point_name} to redeem {data.event.reward.title}'}{f' {times_spun} times spun.' if multiple_spin else ''}")
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
        await bot.send_chat_message(id_streamer, id_streamer, f"Prediction '{data.event.title}' has started. Choices are: {outcomes[:-3]}. Prediction will end in {datetime.timedelta(seconds=time_till_end - seconds_now)}.")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_prediction_begin' -- {e}")
        return


async def on_stream_subbie(data: ChannelSubscribeEvent):
    try:
        if not data.event.is_gift:
            response_level = None
            channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
            sub_tier = await get_subbie_tier(data)
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = float((standard_seconds * sub_tier) / 2)
                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
            if channel_document['data_channel']['writing_clock']:
                seconds = float(standard_seconds * sub_tier)
                if channel_document['data_channel']['hype_train']['current']:
                    seconds = check_hype_train(channel_document, seconds)
                seconds, time_not_added = write_clock(seconds, True, obs)
                response = f", adding {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!! {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
            else:
                response = '.'
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} subscribed to Thee Nest{response} {response_thanks}{f' {response_level}' if response_level is not None else ''}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_subbie' -- {e}")
        return


async def on_stream_subbie_gift(data: ChannelSubscriptionGiftEvent):
    try:
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
                chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
        if channel_document['data_channel']['writing_clock']:
            seconds = float((standard_seconds * sub_tier) * data.event.total)
            if channel_document['data_channel']['hype_train']['current']:
                seconds = check_hype_train(channel_document, seconds)
            seconds, time_not_added = write_clock(seconds, True, obs)
            response = f" Added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!! {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        await bot.send_chat_message(id_streamer, id_streamer, f"{user} gifted out {data.event.total} {'subbie' if data.event.total == 1 else 'subbies'} to Thee Chodelings. {user_response} {response_thanks}{response}{f' {response_level}' if response_level is not None else ''}")
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
            #     seconds, time_not_added = write_clock(seconds, True, channel_document, obs)
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
            new_ats_count, new_cod_count, new_crash_count, new_tag = [0, 0], [0, 0, 0, 0], 0, [None, None, None]
            if channel_document['channel_details']['online_last'] is not None:
                if await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(channel_document['channel_details']['online_last'])) < 7200:
                    new_ats_count = channel_document['data_counters']['ats']
                    new_cod_count = channel_document['data_counters']['cod']
                    new_crash_count = channel_document['data_counters']['stream_crash']
                    new_tag = channel_document['data_games']['tag']
            channel_info = await bot.get_channel_information(id_streamer)
            channel_mods = []
            async for mod in bot.get_moderators(id_streamer):
                channel_mods.append(mod.user_id)
            channel_document['channel_details'].update(online=True, branded=channel_info[0].is_branded_content, title=channel_info[0].title,
                                                       game_id=channel_info[0].game_id, game_name=channel_info[0].game_name,
                                                       content_class=channel_info[0].content_classification_labels, tags=channel_info[0].tags)
            channel_document['data_channel']['hype_train'].update(current=False, current_level=1)
            channel_document['data_counters'].update(ats=new_ats_count, cod=new_cod_count, stream_crash=new_crash_count)
            channel_document['data_games'].update(tag=new_tag)
            channel_document['data_lists'].update(mods=channel_mods)
            channel_document.save()
        await bot.send_chat_announcement(id_streamer, id_streamer, f"Hola. I is here :D Big Chody Hugs.", color="green")
        if channel_document['data_channel']['writing_clock']:
            await bot.send_chat_message(id_streamer, id_streamer, f"{link_loots} | Monthly use 20% off coupon: {link_loots_discount}")
            with open("data/pack_link", "r") as file:
                link = file.read()
            response_pack = list(map(str, link.splitlines()))
            for i in range(0, len(response_pack), 10):
                await bot.send_chat_message(id_streamer, id_streamer, " | ".join(response_pack[i:i + 10]))
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
                    position_x = 664.0
                    position_y = 1726.0
                    rotation = 0.0
                    reset_position_x = 664.0
                    reset_position_y = 434.0
                    reset_rotation = 180.0
                else:
                    position_x = 664.0
                    position_y = 434.0
                    rotation = 180.0
                    reset_position_x = 664.0
                    reset_position_y = 1726.0
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
                if old_rotation == 0 and check_position["positionY"] == 434:
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
                elif old_rotation == 180 and check_position["positionY"] == 1726:
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
        logger.info(f"{fortime()}: Database Loaded\n{long_dashes}")
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
            channel_document = Channels.objects.get(_id=int(b_id))
        except Exception as f:
            if FileNotFoundError:
                try:
                    channel_collection = twitch_database.twitch.get_collection('channels')
                    new_channel_document = Channels(_id=int(b_id), user_name=name, user_login=login)
                    new_channel_document_dict = new_channel_document.to_mongo()
                    channel_collection.insert_one(new_channel_document_dict)
                    channel_document = Channels.objects.get(_id=int(b_id))
                    pass
                except Exception as g:
                    logger.error(f"{fortime()}: Error creating new document for channel -- {int(b_id)}/{name}/{login} -- {g}")
                    return None
            else:
                logger.error(f"{fortime()}: Error fetching/creating channel document -- {int(b_id)}/{name}/{login} -- {f}")
                return None
        return channel_document
    except Exception as e:
        logger.error(f"{fortime()}: Error in get_channel_document -- {int(b_id)}/{name}/{login} -- {e}")
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


def ran_word(channel_document: Document):
    with open("data/english", "r") as file:
        word_list = file.read()
    word_split = list(map(str, word_list.splitlines()))
    answer = random.choice(word_split)
    channel_document['data_games'].update(ranword=answer)
    channel_document.save()
    special_logger.info(f"Random Word = {answer}")


async def select_target(channel_document, chatter_id, manual_choice: bool = False, target_user_name: str = "", game_type: str = "tag"):
    try:
        users = await bot.get_chatters(id_streamer, id_streamer)
        users_collection = twitch_database.twitch.get_collection('users')
        users_documents = users_collection.find({})
        valid_users = []
        for chatter_document in users_documents:
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
                    if game_type != "tag":
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
            if not add and gamble:
                pass
            else:
                chatter_document, response_level = await xp_transfer(chatter_document, value, add)
            if add:
                new_user_points = chatter_document['data_user']['points'] + value
            else:
                new_user_points = chatter_document['data_user']['points'] - value
            chatter_document['data_user'].update(points=new_user_points)
            chatter_document['data_user']['dates'].update(latest_chat=datetime.datetime.now())
            chatter_document.save()
            chatter_document = Users.objects.get(_id=_id)
            return chatter_document, response_level
    except Exception as e:
        logger.error(f"{fortime()}: Error in twitch_points_transfer -- {chatter_document['_id']}/{chatter_document['name']}/{chatter_document['data_user']['login']} -- {e}")
        return None


async def update_tag_stats(chatter_document: Document, add_total: int, add_good: int, add_fail: int):
    response = None
    user_id = chatter_document['_id']
    new_tag_total = chatter_document['data_games']['tag'][0] + add_total
    new_tag_good = chatter_document['data_games']['tag'][1] + add_good
    new_tag_fail = chatter_document['data_games']['tag'][2] + add_fail
    new_boost = chatter_document['data_rank']['boost']
    if new_tag_good % 10 == 0 and add_good > 0:
        new_boost += 25
        response = f"You have gained 25 boost points{f', your new total is {new_boost:,.2f}' if new_boost != 25 else ''}"
    chatter_document['data_rank'].update(boost=new_boost)
    chatter_document['data_games'].update(tag=[new_tag_total, new_tag_good, new_tag_fail])
    chatter_document.save()
    chatter_document = Users.objects.get(_id=user_id)
    return chatter_document, response


async def xp_transfer(chatter_document, value: float, add: bool = True):
    try:
        break_value = 1000000
        response_level = None
        new_boost = chatter_document['data_rank']['boost']
        user_id, user_name = chatter_document['_id'], chatter_document['name']
        new_user_level, start_user_level = chatter_document['data_rank']['level'], chatter_document['data_rank']['level']
        if add:
            value = value / 2
            if chatter_document['data_rank']['boost'] > 0.0:
                if chatter_document['data_rank']['boost'] > value:
                    boost_add = abs(chatter_document['data_rank']['boost'] - (abs(chatter_document['data_rank']['boost'] - value)))
                else:
                    boost_add = chatter_document['data_rank']['boost']
                new_boost = chatter_document['data_rank']['boost'] - boost_add
                value += boost_add
            new_user_xp_points = chatter_document['data_rank']['xp'] + value
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
            new_user_xp_points = float(chatter_document['data_rank']['xp'] - value)
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
        chatter_document['data_rank'].update(boost=new_boost, level=new_user_level, xp=new_user_xp_points)
        chatter_document.save()
        chatter_document = Users.objects.get(_id=user_id)
        if chatter_document['data_rank']['level'] > start_user_level:
            response_level = f"{user_name} you leveled up from {start_user_level:,} to {chatter_document['data_rank']['level']:,}. Current XP: {chatter_document['data_rank']['xp']:,.2f}"
        elif chatter_document['data_rank']['level'] < start_user_level:
            response_level = f"{user_name} you lost {'a level' if abs(start_user_level - chatter_document['data_rank']['level']) == 1 else 'some levels'} from {start_user_level:,} to {chatter_document['data_rank']['level']:,}. Current XP: {chatter_document['data_rank']['xp']:,.2f}"
        return chatter_document, response_level
    except Exception as e:
        logger.error(f"Error in xp_transfer -- {e}")
        return None


async def run():
    async def shutdown(obs_loaded: bool = True):  #, channel_document: Document = None):
        try:
            await bot.send_chat_announcement(id_streamer, id_streamer, f"I am restarting... Bear with me... Much love from {bot_name} <3", color="orange")
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
                                await bot.send_chat_message(id_streamer, id_streamer, f"{user_document['name']} your cast was interrupted by a bot restart. Wait a few mins and then try again")
                        if user_document['data_games']['fish']['auto']['cast'] > 0:
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
        except Exception as e:
            print(f"Error in shutdown() -- {e}")
            pass

    global level_const

    connect = obs.connect()
    if not connect:
        await shutdown(False)
        await full_shutdown(logger_list)
    logger.info(f"{fortime()}: OBS Connection Established\n{long_dashes}")

    twitch_helper = UserAuthenticationStorageHelper(bot, target_scopes)  #, storage_path=data_directory  # ToDo: FUCK THEE PATHING BULLSHIT
    await twitch_helper.bind()

    user = await first(bot.get_users(user_ids=id_streamer))

    channel_document = await get_channel_document(user.id, user.display_name, user.login)
    if channel_document is None:
        logger.error(f"{fortime()}: Error fetching channel_document... Shutting down")
        await shutdown()
        await full_shutdown(logger_list)

    if channel_document['data_games']['ranword'] == "":
        ran_word(channel_document)

    event_sub = EventSubWebsocket(bot)
    event_sub.start()

    await event_sub.listen_channel_ad_break_begin(user.id, on_stream_ad_start)
    await event_sub.listen_channel_chat_message(user.id, user.id, on_stream_chat_message)
    await event_sub.listen_channel_chat_notification(user.id, user.id, on_stream_chat_notification)
    await event_sub.listen_channel_cheer(user.id, on_stream_cheer)
    await event_sub.listen_channel_follow_v2(user.id, user.id, on_stream_follow)
    await event_sub.listen_hype_train_begin(user.id, on_stream_hype_begin)
    await event_sub.listen_hype_train_end(user.id, on_stream_hype_end)
    await event_sub.listen_hype_train_progress(user.id, on_stream_hype_progress)
    await event_sub.listen_channel_poll_begin(user.id, on_stream_poll_begin)
    await event_sub.listen_channel_poll_end(user.id, on_stream_poll_end)
    await event_sub.listen_channel_points_custom_reward_redemption_add(user.id, on_stream_point_redemption)
    await event_sub.listen_channel_prediction_begin(user.id, on_stream_prediction_begin)
    await event_sub.listen_channel_subscribe(user.id, on_stream_subbie)
    await event_sub.listen_channel_subscription_gift(user.id, on_stream_subbie_gift)
    await event_sub.listen_channel_raid(on_stream_raid_in, to_broadcaster_user_id=user.id)
    await event_sub.listen_channel_raid(on_stream_raid_out, from_broadcaster_user_id=user.id)
    await event_sub.listen_channel_update_v2(user.id, on_stream_update)
    await event_sub.listen_stream_online(user.id, on_stream_start)
    await event_sub.listen_stream_offline(user.id, on_stream_end)

    try:
        if len(channel_document['data_games']['fish_recast']) > 0:
            for name in channel_document['data_games']['fish_recast']:
                await bot.send_chat_message(id_streamer, id_streamer, f"!fish {name} | ReCast Initiated")
                await asyncio.sleep(0.25)
            channel_document['data_games'].update(fish_recast=[])
            channel_document.save()
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
            if user_input.isdigit():
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
                                break
                            elif user_input == 1:
                                configure_write_to_clock(await get_channel_document(user.id, user.display_name, user.login), obs)
                                await asyncio.sleep(2)
                            elif user_input == 2:
                                print("This is out of service ATM")
                                # configure_hype_ehvent(await get_channel_document(user.id, user.display_name, user.login), obs)
                                await asyncio.sleep(2)
                            elif user_input == 3:
                                reset_current_time()
                                await asyncio.sleep(2)
                            elif user_input == 4:
                                reset_max_time()
                                await asyncio.sleep(2)
                            elif user_input == 5:
                                reset_total_time()
                                await asyncio.sleep(2)
                            elif user_input == 6:
                                reset_clock_accel_rate(obs)
                                await asyncio.sleep(2)
                            elif user_input == 7:
                                reset_clock_slow_rate(obs)
                                await asyncio.sleep(2)
                            elif user_input == 8:
                                reset_clock_pause(obs)
                                await asyncio.sleep(2)
                            elif user_input == 10:
                                reset_flash_settings()
                                await asyncio.sleep(2)
                            else:
                                print("Not valid, try again..")
                                await asyncio.sleep(2)
                elif user_input == 2:
                    while True:
                        cls()
                        user_input = input(f"Enter 1 to print out general user stats\nEnter 2 to print out chatters with redeemed free packs\nEnter 10 to add new field to user_docs\nEnter 0 to go back\n")
                        if not user_input.isdigit():
                            print(f"Invalid Input -- Put Just A Number")
                        else:
                            users_collection = twitch_database.twitch.get_collection('users')
                            users = users_collection.find({})
                            user_input = int(user_input)
                            if user_input == 0:
                                print("Going back..")
                                await asyncio.sleep(2)
                                break
                            elif user_input == 1:
                                cls()
                                printout = []
                                try:
                                    users_sorted = sorted(users, key=lambda user: user['data_user']['points'], reverse=True)
                                    printout.append(f"{long_dashes}\nkey -- Pos: Name -- Points -- Level(XP) -- Boost")
                                    for n, user in enumerate(users_sorted):
                                        printout.append(f"{n+1}: {user['name']} -- {user['data_user']['points']:,.2f} -- {user['data_rank']['level']}({user['data_rank']['xp']:,.2f}) -- {user['data_rank']['boost']}")
                                    special_logger.info('\n'.join(printout))
                                    special_logger.info(long_dashes)
                                    print("Done, returning to main menu...")
                                    await asyncio.sleep(2)
                                    break
                                except Exception as g:
                                    logger.error(f"{fortime()}: Error loading preparing user_stats  -- {g}\n{printout}")
                                    await asyncio.sleep(2)
                                    break
                            elif user_input == 2:
                                cls()
                                printout = []
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
                                    print("Done, returning to main menu...")
                                    await asyncio.sleep(2)
                                    break
                                except Exception as g:
                                    logger.error(f"{fortime()}: Error loading preparing free_card_printout -- {g}\n{printout}")
                                    await asyncio.sleep(10)
                                    break
                            elif user_input == 10:
                                cls()
                                print("Not In Operation")
                                await asyncio.sleep(2)
                                break
                                # for user in users:
                                #     try:
                                #         user_document = await get_chatter_document(None, channel_document, user['_id'], user['name'], user['data_user']['login'], id_streamer, name_streamer)
                                #         if user_document is not None:
                                #             if 'fis1' in user_document['data_games']:
                                #                 user_document['data_games'].pop('fis1', None)
                                #             if 'jail' in user_document['data_games']:
                                #                 if user_document['data_games']['jail'] == "":
                                #                     user_document['data_games']['jail'] = {"in": False, "last": None, "escapes": 0}
                                #             elif 'jail' not in user_document['data_games']:
                                #                 user_document['data_games']['jail'] = {"in": False, "last": None, "escapes": 0}
                                #             if 'iq' in user_document['data_games']:
                                #                 if user_document['data_games']['iq'] == "":
                                #                     user_document['data_games']['iq'] = {"current": 0.0, "last": None, "history": []}
                                #             elif 'iq' not in user_document['data_games']:
                                #                 user_document['data_games']['iq'] = {"current": 0.0, "last": None, "history": []}
                                #             user_document.save()
                                #             special_logger.info(f"{user_document['name']} updated")
                                #     except Exception as grr:
                                #         logger.error(f"{fortime()}: Error in data_restructure for user_docs -- {grr}")
                                #         await asyncio.sleep(10)
                                #         break
                                # print("Operation Carried out... Returning to Main Menu")
                                # await asyncio.sleep(2)
                                # break
                            else:
                                print("Invalid Input (1/10/0 are valid only)")
                                await asyncio.sleep(2)
                    await asyncio.sleep(2)
                elif user_input == 3:
                    cls()
                    while True:
                        number, add = loop_get_user_input_clock()
                        if number.isdigit():
                            write_clock(float(number), add, obs=obs, manual=True)
                            break
                        else:
                            print(f"Invalid Input -- You put '{number}' - If None, see error logs - which is a {type(number)} -- USE NUMPAD +/-!!")
                elif user_input == 4:
                    cls()
                    reset_bot_raid()
                    await asyncio.sleep(2)
                elif user_input == 5:
                    reset_night_mode()
                    await asyncio.sleep(2)
                else:
                    print(f"Invalid Input -- You put '{user_input}'")
            else:
                print(f"Invalid Input -- You put '{user_input}' which is a {type(user_input)}")
        except KeyboardInterrupt:
            await shutdown()
        except Exception as e:
            logger.error(f"{fortime()}: Error in BOT Loop -- {e}")
            try:
                continue
            except Exception as grrrr:
                logger.error(f"{fortime()}: ERROR TRYING TO CONTINUE UPON LAST ERROR -- {grrrr} -- ATTEMPTING TO HALT BOT")
                await shutdown()


if __name__ == "__main__":
    bot_options = ["Enter 1 to configure timer",
                   "Enter 2 to fetch stats",
                   "Enter 3 to +/- time",
                   "Enter 4 for Bot Protection",
                   "Enter 5 for Sleep Mode",
                   "Enter 0 to Halt Bot"]
    bot_options_one = ["Enter 1 to Enable/Disable Writing to Clock",
                       # "Enter 2 to Enable/Disable Thee Hype EhVent",
                       "Enter 3 to Change Current time left",
                       "Enter 4 to Change Max Time",
                       "Enter 5 to Change Total Time",
                       "Enter 6 to Change Countdown ACCEL Rate",
                       "Enter 7 to Change Countdown SLOW Rate",
                       "Enter 8 to Change Countdown Pause",
                       "Enter 10 to Configure Flash Settings",
                       "Enter 0 To Go Up"]
    main_options = ["Enter 1 to start twitch bot",
                    "Enter 3 to +/- time",
                    "Enter 0 to Exit Program"]

    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger('logger', f'{init_time}-log.log', logger_list)
    chat_logger = setup_logger('chat_logger', f'{init_time}-chat_log.log', logger_list)
    gamble_logger = setup_logger('gamble_logger', f'{init_time}-gamble_log.log', logger_list)
    special_logger = setup_logger('special_logger', f'{init_time}-special_log.log', logger_list)  #, logging.WARN)

    if None in (logger, chat_logger, gamble_logger, special_logger):
        print(f"One of thee loggers isn't setup right -- {logger}/{chat_logger}/{gamble_logger}/{special_logger} -- Quitting program")
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
                    try:
                        logger.info(long_dashes)
                        twitch_database = connect_mongo(mongo_twitch_collection, DEFAULT_CONNECTION_NAME)
                        time.sleep(1)
                        if twitch_database is None:
                            asyncio.run(disconnect_mongo())
                            logger.error(f"{fortime()}: Error connecting to twitch_database -- Quitting Program..")
                            break
                        # discord_database = connect_mongo(mongo_discord_collection, "Discord_Database")
                        # time.sleep(1)
                        # if None in (twitch_database, discord_database):
                        #     asyncio.run(disconnect_mongo())
                        #     logger.error(f"{fortime()}: Error connecting one of thee databases -- {twitch_database}/{discord_database} -- Quitting program")
                        #     break
                    except Exception as f:
                        logger.error(f"{fortime()}: Error Loading Database(s) -- {f}")
                        break
                    asyncio.run(run())
                    break
                elif user_input == 2:
                    print("Logic Not Coded")
                    # Might try asyncio.create_subprocess_shell() or something alike later on, for now 2 programs
                elif user_input == 3:
                    while True:
                        number, add = loop_get_user_input_clock()
                        if number.isdigit():
                            write_clock(float(number), add, manual=True)
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
        except Exception as e:
            logger.error(f"{fortime()}: Error in MAIN loop -- {e} - Exiting Program")
            break
    # asyncio.run(disconnect_mongo())
    # asyncio.run(full_shutdown(logger_list))
