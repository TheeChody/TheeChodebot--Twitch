import os
import sys
import time
import random
import asyncio
import datetime
from timeit import default_timer as timer
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from pyprobs import Probability as pr
from mondocs import Channels, Users
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.oauth import UserAuthenticationStorageHelper
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME, Document
from functions import long_dashes, loop_get_user_input_clock, read_clock, \
    reset_clock_slow_rate, reset_current_time, reset_clock_pause, reset_max_time, reset_total_time, read_clock_sofar, \
    write_clock, read_clock_max, read_clock_total, standard_seconds, WebsocketsManager, setup_logger, fortime, load_dotenv, \
    configure_write_to_clock, full_shutdown, logs_directory, read_clock_rate, write_clock_pause, read_clock_pause, \
    cls, standard_direct_dono, set_timer_pause, read_clock_slow_strict, reset_clock_accel_rate, read_clock_accel_state, \
    read_clock_slow_state, reset_night_mode, read_night_mode, reset_flash_settings, read_bot_raid, reset_bot_raid,\
    write_clock_accel_time, write_clock_slow_time, write_clock_phase, set_timer_rate, read_clock_accel_time, read_clock_slow_time, \
    read_clock_up_time, write_clock_up_time, set_timer_count_up  #, flash_window
from twitchAPI.object.eventsub import ChannelAdBreakBeginEvent, ChannelChatMessageEvent, ChannelChatNotificationEvent, \
    ChannelCheerEvent, ChannelFollowEvent, ChannelPollBeginEvent, ChannelPollEndEvent, ChannelPointsCustomRewardRedemptionAddEvent, \
    ChannelPredictionEvent, ChannelPredictionEndEvent, ChannelRaidEvent, ChannelSubscribeEvent, ChannelSubscriptionGiftEvent, \
    ChannelUpdateEvent, ExtensionBitsTransactionCreateEvent, HypeTrainEvent, HypeTrainEndEvent, StreamOnlineEvent, StreamOfflineEvent  #, GoalEvent

# ToDo List ------------------------------------------------------------------------------------------------------------
#  Figure out music queueing system, gonna need ability to manipulate VLC player. or make my own? haha yeah right
#  addon to ^^ use pytube to gather track info/download video if not downloaded already
#  Add Translation from MorseCode to English
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
                 AuthScope.MODERATOR_MANAGE_CHAT_MESSAGES, AuthScope.MODERATION_READ, AuthScope.CHANNEL_MANAGE_MODERATORS]  # ToDo: FIGURE OUT WHY THEE PREDICTION SHIT FLIPS OUT ON END/LOCK CALL!!!!!!!!!!!
logger_list = []

pants_choices = ["Commando",
                 "flexing a Loin Cloth",
                 "wearing Boxers",
                 "wearing a thong",
                 "wearing tighty whities"]
slap_choices = ["with a telephone book",
                "with a frying pan",
                "because {} felt like it",
                "to wake up",
                "to shut up",
                "for fun",
                "to stahhp",
                "with a fish",
                "until there was no Shat left in their body",
                "with a thick slice o' ham",
                "with a 9in dildo",
                "across thee chin with Shats' Brass Balls",
                "with an empty beer bottle"]
marathon_rewards = ["8099f524-c2e8-41de-b31f-35de4ff7f084",  # 10
                    "55ec31e9-98f8-46ef-939e-c7835514fd1b",  # 20
                    "dc306b71-9fd2-422e-968b-61690c1b7387"]  # 30  # ToDo: FIGURE OUT WHY THIS SHIT SAYS IT'S NOT MINE
options_webcam = ("Colour", "Flip", "Spin")
options_webcam_colours = ("None", "Blue", "Green", "Hidden", "Magenta", "Red")
options_eq_colour = ("Blue", "Green", "Magenta", "Red", "White")

level_const = 100  # How levels are determined
raid_seconds = 15  # Only for points now
follow_seconds = 30  # Only for points now
stream_loots_seconds = 1.8  # How many seconds per CARD purchased is added
standard_points = 1  # Base value -- points for chatting, bitties, subbing/resubbing, gifting subbies etc.
stream_loots_pack_quantity = 3
fish_auto_cost = 25


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
            await bot.send_chat_message(id_streamer, id_streamer, f"Incoming ad break, {auto_response} and should only last {datetime.timedelta(seconds=ad_length)}. Next ad inbound in {datetime.timedelta(seconds=seconds_till_ad)}.{f' {marathon_response}.' if marathon_response is not None else ''}")
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


async def on_stream_bits_ext_transfer(data: ExtensionBitsTransactionCreateEvent):  # WebHooks Needed For This
    try:
        response, response_level = "!", None
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        chatter_document = await get_chatter_document(data)
        if chatter_document is not None:
            points_to_add = float((standard_points * data.event.product.bits) / 2)
            chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, points_to_add)
        if channel_document['data_channel']['writing_clock']:
            seconds = float(standard_seconds * data.event.product.bits)
            seconds, time_not_added = write_clock(seconds, True, obs)
            response = f", adding {str(datetime.timedelta(seconds=seconds)).title()} to thee clock!! {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} used {data.event.product.bits} on {data.event.product.name}{response}{f' {response_level}' if response_level is not None else ''}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_bits_ext_transfer' -- {e}")
        return


async def on_stream_chat_message(data: ChannelChatMessageEvent):
    # ToDo: ------------------------------------------------------------------------------------------------------------
    #  Little 'mini-games' --fish(in progress), bet, etc
    #  Jail mini-game? Send someone to jail, they get timed out or alike? idk. Maybe random chance to 'escape'
    #  -------------------------------------- End of on_stream_chat_message List ---------------------------------------
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
                seconds, time_not = write_clock(seconds, True, obs)
                chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                await bot.send_chat_message(id_streamer, id_streamer, f"{name} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
        chatter_username = data.event.chatter_user_name
        chatter_document = await get_chatter_document(data, channel_document)
        if chatter_document is None and chatter_id not in channel_document['data_lists']['ignore']:  # ToDo: Make This UGLY Shit Cleaner...
            special_logger.error(f"Chatter/Channel Document is None!! -- chatter-{chatter_username} -- channel-{channel_document}")
        if chatter_id in channel_document['data_lists']['lurk']:
            try:
                channel_document['data_lists']['lurk'].remove(chatter_id)
                channel_document.save()
                channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                await bot.send_chat_message(id_streamer, id_streamer, f"Well, lookie who came back from thee shadows, {chatter_username}.")
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
                    # obs.set_text("LastComment", f"{chatter_username}'s last message was: {last_message if not None else 'Not Found!!!'}")
                    # obs.set_source_visibility("NS-Twitch", "LastComment", True)  # ToDo: Re ADD THIS STUFF
                    # await asyncio.sleep(10)
                    # obs.set_source_visibility("NS-Twitch", "LastComment", False)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - lastcomment command -- {f}")
                    end_timer("lastcomment command")
                    return
            elif command_check.startswith(("lurk", "brb")):
                try:
                    if chatter_id not in channel_document['data_lists']['lurk'] and chatter_id != id_streamer:
                        channel_document['data_lists']['lurk'].append(chatter_id)
                        channel_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} fades off into thee shadows. {response_thanks}")
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
                        response_webcam = f"{chatter_username} {f'{action}s {data.event.broadcaster_user_name}' if action != 'Colour' else f'changed thee {action} of {data.event.broadcaster_user_name} to {new_colour.title()}'} for 100 chodybot points"
                    else:
                        response_webcam = f"{chatter_username} your command was not registered, no points taken.", f"Valid colours are: {f'|'.join(list(options_webcam_colours))}" if action.startswith("Colour") else ""
                    await bot.send_chat_message(id_streamer, id_streamer, response_webcam)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- webcam command -- {f}")
                    end_timer("webcam command")
                    return
            # Level/Points Commands
            elif command_check.startswith(("levelcheck", "levelscheck", "levelcheck")):  # ToDo: Add Manual Targeting
                try:
                    if chatter_document is not None:
                        rank = None
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
                try:
                    if chatter_document is not None:
                        rank = None
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
            elif command_check.startswith("pt"):
                await bot.send_chat_message(id_streamer, id_streamer, f"This command is not available")
                # try:
                #     # await bot.send_chat_message(id_streamer, id_streamer, f"This command is currently under construction", reply_parent_message_id=data.event.message_id)
                #     if chatter_document['data_user']['discord_id'] == "":
                #         chatter_document['data_user'].update(discord_id=chatter_document['_id'])
                #         chatter_document.save()
                #         await bot.send_chat_message(id_streamer, id_streamer, f"You do not have your discord ID linked to your twitch yet. Will attempt to DM you a special code with instructions to link account", reply_parent_message_id=data.event.message_id)
                #         await bot.send_whisper(id_streamer, chatter_id, f"Hola, your special discord link code is: {chatter_document['_id']} . Head to any discord server TheeChodebot runs in and use this command: $link_twitch {chatter_document['_id']} . Thee code will automatically expire and your message will be deleted in discord and a response confirming will appear")
                #         end_timer("pt command")
                #         return
                #     elif chatter_document['data_user']['discord_id'].startswith(chatter_id):
                #         await bot.send_chat_message(id_streamer, id_streamer, f"Check your DM's. If not reach out to {data.event.broadcaster_user_name} to figure it out", reply_parent_message_id=data.event.message_id)
                #         end_timer("pt command")
                #         return
                #     chatter_document_discord = await get_discord_document(chatter_document)
                #     if chatter_document_discord is None:
                #         special_logger.error(f"{fortime()}: {chatter_username}'s discord document is NONE. Something went wrong.")
                #         end_timer("pt command")
                #         return
                #     if command.removeprefix("pt ").startswith("twitch"):
                #         transfer_value = command.removeprefix("pt twitch ")
                #         if transfer_value.isdigit():
                #             await document_points_transfer("twitch", transfer_value, chatter_document, chatter_document_discord)
                #         else:
                #             await bot.send_chat_message(id_streamer, id_streamer, f"I couldn't ID thee number you're trying to transfer", reply_parent_message_id=data.event.message_id)
                #             special_logger.error(f"{fortime()}: transfer value invalid--{chatter_username}--{transfer_value}--{type(transfer_value)}")
                #             end_timer("pt command")
                #             return
                #     elif command.removeprefix("pt ").startswith("discord"):
                #         transfer_value = command.removeprefix("pt discord ")
                #         if transfer_value.isdigit():
                #             await document_points_transfer("discord", transfer_value, chatter_document, chatter_document_discord)
                #         else:
                #             await bot.send_chat_message(id_streamer, id_streamer, f"I couldn't ID thee number you're trying to transfer", reply_parent_message_id=data.event.message_id)
                #             print(f"--{transfer_value}--{type(transfer_value)}")
                #             end_timer("pt command")
                #             return
                # except Exception as f:
                #     logger.error(f"{fortime()}: Error in on_stream_chat_message - pt command -- {f}")
                #     end_timer("pt command")
                #     return
            # Mini-Game Commands
            elif command_check.startswith("cutline"):
                line_cut_cost = 2500
                line_wait_time = 7200
                try:
                    if chatter_document['data_user']['points'] < line_cut_cost:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points for that! Need {line_cut_cost}, you have {chatter_document['data_user']['points']:,.2f}")
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
                    if target_document['data_games']['fish'] == "" or not target_document['data_games']['fish']:
                        target_document['data_games']['fish'] = {"auto": {"cast": 0, "cost": 0, "gain": 0.0, "lost": 0.0, "rewards": []}, "line": {"cast": False, "cut": False, "cut_by": "", "cut_last": None}}
                        target_document.save()
                        target_document = Users.objects.get(_id=target_document['_id'])
                    elif target_document['data_games']['fish']['line']['cut_last'] is None:
                        pass
                    elif await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(target_document['data_games']['fish']['line']['cut_last'])) < line_wait_time:
                        wait_time = line_wait_time - (await get_long_sec(fortime_long(datetime.datetime.now())) - await get_long_sec(fortime_long(target_document['data_games']['fish']['line']['cut_last'])))
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line has been recently cut already. Gotta wait {datetime.timedelta(seconds=wait_time)}.", reply_parent_message_id=data.event.message_id)
                        end_timer("cutline target's line been cut recently")
                        return
                    elif target_document['data_games']['fish']['line']['cut']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line is already cut!!")
                        end_timer("cutline target's line been cut already")
                        return
                    chatter_document['data_user']['points'] -= line_cut_cost
                    chatter_document.save()
                    chatter_document = await get_chatter_document(data)
                    target_document['data_games']['fish']['line']['cut'] = True
                    target_document['data_games']['fish']['line']['cut_by'] = chatter_username
                    target_document['data_games']['fish']['line']['cut_last'] = datetime.datetime.now()
                    target_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"{target_document['name']}'s line has been cut successfully!! Your now have {chatter_document['data_user']['points']:,.2f} points remaining", reply_parent_message_id=data.event.message_id)
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
            # ToDo: ADD UNFISH COMMAND FOR BOT RESTARTS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            elif command_check.startswith("fish"):  # Moist Dude's Line
                async def refresh_chatter_document(data, target_id, target_name, target_login):
                    if target_id is not None:
                        chatter_document = await get_chatter_document(None, user_id=target_id, user_name=target_name, user_login=target_login, b_id=id_streamer, b_name=name_streamer)
                    else:
                        chatter_document = await get_chatter_document(data)
                    return chatter_document
                initial_auto, final_auto, total_rewards = False, False, []
                gain, difference = "lost", 0.0
                cost_value = 0
                fish_start, fish_limit = 5, 90
                try:
                    if chatter_document['data_games']['fish'] == "" or not chatter_document['data_games']['fish']:
                        chatter_document['data_games']['fish'] = {"auto": {"cast": 0, "cost": 0, "gain": 0.0, "lost": 0.0, "rewards": []}, "line": {"cast": False, "cut": False, "cut_by": "", "cut_last": None}}
                        chatter_document.save()
                        chatter_document = await get_chatter_document(data)
                except Exception as g:
                    logger.error(f"{fortime()}: {chatter_username} is trying to fish but 'fish' isn't setup right!!!! - {g}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"There was an error with your fishing document, {name_streamer} is aware/will be now", reply_parent_message_id=data.event.message_id)
                    end_timer("fish command fish error")
                    return
                target_id, target_name, target_login = None, None, None
                try:
                    # if chatter_id == id_streamer and command_check.removeprefix("fish") != "" or not command_check.removeprefix("fish").isdigit():
                    #     fist_start, fish_limit = 30, 180
                    #     target = command_check.removeprefix("fish")
                    #     if target.startswith("@"):
                    #         target = target.removeprefix("@")
                    #     if "|" in target:
                    #         target_fisher, _ = target.split("|", maxsplit=1)
                    #     else:
                    #         target_fisher = target
                    #     try:
                    #         chatter_document = Users.objects.get(name=target_fisher)
                    #     except Exception as g:
                    #         logger.error(f"{fortime()}: Error in fish command -- document swap -- {target_fisher} -- {g}")
                    #         end_timer("fish doc swap command")
                    #         return
                    if chatter_document['data_games']['fish']['line']['cast']:
                        auto_response = ""
                        if chatter_document['data_games']['fish']['auto']['cast'] != 0:
                            auto_response = f" You have {chatter_document['data_games']['fish']['auto']['cast']:,} auto casts remaining."
                        await bot.send_chat_message(id_streamer, id_streamer, f"You have already cast your line, wait a few.{auto_response}", reply_parent_message_id=data.event.message_id)
                        end_timer("fish game already fishing")
                        return
                    elif command_check.removeprefix("fish").isdigit():
                        if chatter_document['data_games']['fish']['auto']['cast'] != 0:
                            await bot.send_chat_message(id_streamer, id_streamer, f"!fish {chatter_document['name']} | You've already setup auto fishing!! You have {chatter_document['data_games']['fish']['auto']['cast']:,} auto casts remaining", reply_parent_message_id=data.event.message_id)
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
                                await bot.send_chat_message(id_streamer, id_streamer, f"You have successfully set your auto cast to {auto_casts:,} for {cost:,} Chodybot Points", reply_parent_message_id=data.event.message_id)
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
                    chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    await asyncio.sleep(random.randint(fish_start, fish_limit))
                    chatter_document['data_games']['fish']['line']['cast'] = False
                    chatter_document.save()
                    chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    with open("data/fish_rewards", "r") as file:
                        fish_rewards = file.read()
                    fish_rewards = list(map(str, fish_rewards.splitlines()))
                    fish = random.choice(fish_rewards)
                    fish, value = fish.split(",")
                    raw_value = float(value)
                    fish_response = f"caught {fish} worth {raw_value:,} point{'s' if raw_value != 1 else ''}"
                    line_cut = False
                    if chatter_document['data_games']['fish']['line']['cut']:
                        line_cut = True
                        fish = f"line was cut by {chatter_document['data_games']['fish']['line']['cut_by']} loosing a {fish} worth {value}"
                        fish_response = fish
                        value, raw_value = 0, 0
                        chatter_document['data_games']['fish']['line']['cut'] = False
                        chatter_document['data_games']['fish']['line']['cut_by'] = ""
                        chatter_document.save()
                        chatter_document = await refresh_chatter_document(data, target_id, target_name, target_login)
                    total_gained, total_lost = chatter_document['data_games']['fish']['auto']['gain'], chatter_document['data_games']['fish']['auto']['lost']
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
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_document['name']} you{'r' if line_cut else ''} {fish_response}! Your new points are: {chatter_document['data_user']['points']:,.2f}.{f' {response_level}.' if response_level is not None else ''}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    if f == "Internal Server Error":
                        try:
                            await asyncio.sleep(1)
                            if chatter_document['data_games']['fish']['auto']['cast'] > 0 or final_auto:
                                await bot.send_chat_message(id_streamer, id_streamer, f"!fish {chatter_document['name']} | Your Cast Message failed to send. Your last caught item was; {chatter_document['data_games']['fish']['line']['rewards'][-1]}. You have {chatter_document['data_games']['fish']['auto']['cast'] if not final_auto else 'no'} casts left")
                            else:
                                await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_document['name']} your cast message failed to send. Your current points are {chatter_document['data_user']['points']:,.2f}")
                            end_timer("fish command retry server error success")
                            return
                        except Exception as g:
                            logger.error(f"{fortime()}: Error in on_stream_chat_message -- fish internal server error retry -- {g}")
                            end_timer("fish command retry server error fail")
                            return
                    else:
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
                        if pr.prob(99.995/100):
                            response_gamble = f"lost {bet_value:,}"
                            await bot.send_chat_message(id_streamer, id_streamer, f"You lost thee gamble, I ate your points. They tasted yummy! You now have {chatter_document['data_user']['points']:,.2f} points.", reply_parent_message_id=data.event.message_id)
                        else:
                            won_amount = bet_value * 100000
                            # won_amount = (bet_value /  5) * 5000
                            # won_amount = bet_value * 2
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
                            end_timer("pants command")
                            return
                    pants_response = random.choice(pants_choices)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} pulls down thee pants of {target.user_name} whom is {pants_response}")
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
                            for entry in chatter_document['data_games']['pp'][2]:
                                response_pp.append(f"{entry} inch pecker" if entry > 0 else f"{entry} inch innie")
                            response_sorted = sorted(response_pp, reverse=True)
                            final_response = f"Your last 10 pp sizes were: {' | '.join(response_sorted[:10])}"
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
                    # elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(chatter_document['data_games']['pp'][1])) > cmd_reset_seconds:
                    elif now_time.day == chatter_document['data_games']['pp'][1].day:
                        if now_time.month == chatter_document['data_games']['pp'][1].month:
                            if now_time.year == chatter_document['data_games']['pp'][1].year:
                                await already_done()
                                return
                            else:
                                pass
                        else:
                            pass
                    elif now_time.day != chatter_document['data_games']['pp'][1].day:
                        pass
                    else:
                        await already_done()
                        return
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
                            end_timer("slap command")
                            return
                    slap_response = random.choice(slap_choices)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} slaps {target.user_name} {slap_response.format(chatter_username)}")
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"American Truck Sim Crash Count (Tractor/Game): {channel_document['data_counters']['ats'][0]}/{channel_document['data_counters']['ats'][1]}")
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"CoD Counter (Matches/Wins/Losses/Crashes): {channel_document['data_counters']['cod'][0]}/{channel_document['data_counters']['cod'][1]}/{channel_document['data_counters']['cod'][2]}/{channel_document['data_counters']['cod'][3]}")
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"{response_joints_day_reset if response_joints_day_reset is not None else ''} Joints Smoked Count (Total | Last): {channel_document['data_counters']['joints'][0]:,} | {f'{last_smoked_nice} MST' if last_smoked_nice is not None else 'None'}")
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"{marathon_name} Stream Crash Count: {channel_document['data_counters']['stream_crash']}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message streamcount command -- {f}")
                    end_timer("streamcount command")
                    return
            # Marathon Commands
            elif command_check.startswith("addtime"):
                try:
                    if not channel_document['data_channel']['writing_clock']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Writing to clock is currently disabled")
                        end_timer("addtime command")
                        return
                    time_value = command.replace(" ", "").replace("addtime", "")
                    if chatter_id == id_streamloots or chatter_id == id_streamer:
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
                        # ToDo: Add points add when packs purchased & cards played
                        seconds, time_not = write_clock(time_add, True, obs)
                        chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                        await bot.send_chat_message(id_streamer, id_streamer, f"{name} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                        special_logger.info(f"timeadded -- {datetime.timedelta(seconds=int(seconds))} -- {seconds} by {chatter_username}{f' -- MAX TIME HIT {time_not} not added.' if time_not is not None else ''}{f' {response_level}' if response_level is not None else ''}")
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"This command is currently disabled")
                        # if not time_value.isdigit():
                        #     await bot.send_chat_message(id_streamer, id_streamer, f"Your command should resemble, where NUMBER_HERE put thee minutes, valid mins are 10, 20, 30: {' or '.join(cmd)} addtime NUMBER_HERE", reply_parent_message_id=data.event.message_id)
                        #     end_timer("addtime command")
                        #     return
                        # time_value = int(time_value)
                        # if time_value == 10:
                        #     if not chatter_document['data_user']['points'] >= points_for_time:
                        #         await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points to do that", reply_parent_message_id=data.event.message_id)
                        #         end_timer("addtime command")
                        #         return
                        #     new_user_points = chatter_document['data_user']['points'] - points_for_time
                        #     time_add = 600.0
                        # elif time_value == 20:
                        #     if not chatter_document['data_user']['points'] >= points_for_time * 2 - 200:
                        #         await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points to do that", reply_parent_message_id=data.event.message_id)
                        #         end_timer("addtime command")
                        #         return
                        #     new_user_points = chatter_document['data_user']['points'] - points_for_time * 2 - 200
                        #     time_add = 1200.0
                        # elif time_value == 30:
                        #     if not chatter_document['data_user']['points'] >= points_for_time * 3 - 400:
                        #         await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points to do that", reply_parent_message_id=data.event.message_id)
                        #         end_timer("addtime command")
                        #         return
                        #     new_user_points = chatter_document['data_user']['points'] - points_for_time * 3 - 400
                        #     time_add = 1800.0
                        # else:
                        #     await bot.send_chat_message(id_streamer, id_streamer, f"{time_value} isn't a valid time choice. Valid choices are 10, 20, 30.", reply_parent_message_id=data.event.message_id)
                        #     end_timer("addtime command")
                        #     return
                        # chatter_document['data_user'].update(points=new_user_points)
                        # chatter_document.save()
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - addtime command -- {f}")
                    end_timer("addtime command")
                    return
            elif command_check.startswith(("loot", marathon_name.lower(), marathon_name.replace("-", "").lower())):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"$pack | {link_loots} | Monthly use 20% off coupon: {link_loots_discount}")
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
            elif command_check.startswith("remtime"):
                try:
                    time_value = command.replace(" ", "").replace("remtime", "")
                    if chatter_id == id_streamloots or chatter_id == id_streamer:  # StreamLoots ID
                        time_value, name = time_value.split("by", maxsplit=1)
                        name, _ = name.split("via", maxsplit=1)
                        if not time_value.isdigit():
                            print(time_value, type(time_value), "not valid")
                            return
                        time_rem = float(time_value)
                        seconds, time_not = write_clock(time_rem, False, obs)
                        chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, seconds)
                        await bot.send_chat_message(id_streamer, id_streamer, f"{name} removed {datetime.timedelta(seconds=int(seconds))} from thee clock{f', MAX TIME HIT {time_not} not added.' if time_not is not None else '.'}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                        special_logger.info(f"timeadded -- {datetime.timedelta(seconds=int(seconds))} -- {seconds} by {chatter_username}{f' -- MAX TIME HIT {time_not} not added.' if time_not is not None else ''}")
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"This command is currently disabled")
                        # if not time_value.isdigit():
                        #     await bot.send_chat_message(id_streamer, id_streamer, f"Your command should resemble, where NUMBER_HERE put thee minutes, valid mins are 10, 20, 30: {' or '.join(cmd)} addtime NUMBER_HERE", reply_parent_message_id=data.event.message_id)
                        #     end_timer("remtime command")
                        #     return
                        # time_value = int(time_value)
                        # if time_value == 10:
                        #     if not chatter_document['data_user']['points'] >= points_for_time:
                        #         await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points to do that", reply_parent_message_id=data.event.message_id)
                        #         end_timer("remtime command")
                        #         return
                        #     new_user_points = chatter_document['data_user']['points'] - points_for_time
                        #     time_rem = 600.0
                        # elif time_value == 20:
                        #     if not chatter_document['data_user']['points'] >= points_for_time * 2 - 200:
                        #         await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points to do that", reply_parent_message_id=data.event.message_id)
                        #         end_timer("remtime command")
                        #         return
                        #     new_user_points = chatter_document['data_user']['points'] - points_for_time * 2 - 200
                        #     time_rem = 1200.0
                        # elif time_value == 30:
                        #     if not chatter_document['data_user']['points'] >= points_for_time * 3 - 400:
                        #         await bot.send_chat_message(id_streamer, id_streamer, f"You don't have enough points to do that", reply_parent_message_id=data.event.message_id)
                        #         end_timer("remtime command")
                        #         return
                        #     new_user_points = chatter_document['data_user']['points'] - points_for_time * 3 - 400
                        #     time_rem = 1800.0
                        # else:
                        #     await bot.send_chat_message(id_streamer, id_streamer, f"{time_value} isn't a valid time choice. Valid choices are 10, 20, 30.", reply_parent_message_id=data.event.message_id)
                        #     end_timer("remtime command")
                        #     return
                        # chatter_document['data_user'].update(points=new_user_points)
                        # chatter_document.save()
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- remtime command -- {f}")
                    end_timer("remtime command")
                    return
            elif command_check.startswith(("time2add", "timeadd")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Time that can still be added to thee clock is: {str(datetime.timedelta(seconds=abs(float(read_clock_max()) - float(read_clock_total())))).title()}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timeadd command -- {f}")
                    end_timer("timeadd command")
                    return
            elif command_check.startswith(("timecurrent", "timeremaining", "timeleft")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee current time remaining: {str(datetime.timedelta(seconds=int(float(read_clock())))).title()}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timecurrent command -- {f}")
                    end_timer("timecurrent command")
                    return
            elif command_check.startswith(("timemax", "timecap")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee Marathon Cap is: {str(datetime.timedelta(seconds=float(read_clock_max()))).title()}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timemax command -- {f}")
                    end_timer("timemax command")
                    return
            elif command_check.startswith(("timepause", "timepaused")):
                try:
                    time_pause = float(read_clock_pause())
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee timer is {f'currently paused for {str(datetime.timedelta(seconds=time_pause)).title()}' if time_pause != 0.0 else 'not currently paused'}.")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timepause command -- {f}")
                    end_timer("timepause command")
                    return
            elif command_check.startswith(("timerate", "timedown")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"We are currently counting down at: {read_clock_rate()} real second(s)/countdown second.")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timerate command -- {f}")
                    end_timer("timerate command")
                    return
            elif command_check.startswith("timesofar"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee total elapsed time so far is: {str(datetime.timedelta(seconds=float(read_clock_sofar()))).title()}.")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- timesofar command -- {f}")
                    end_timer("timesofar command")
                    return
            elif command_check.startswith("times"):
                try:
                    response_throne = f"{standard_seconds * 2} Seconds / Cent Contributed ($1 = {str(datetime.timedelta(seconds=(standard_seconds * 2) * 100)).title()})"
                    response_direct_dono = f"{standard_direct_dono} Seconds / Cent Received ($1 = {str(datetime.timedelta(seconds=standard_direct_dono * 100)).title()})"
                    response_twitch = f"{standard_seconds} Seconds / Cent Received (100 bitties = {str(datetime.timedelta(seconds=standard_seconds * 100)).title()} -- 1 T1 subbie = {str(datetime.timedelta(seconds=standard_seconds * 250)).title()} -- 1 T2 subbie = {str(datetime.timedelta(seconds=standard_seconds * 500)).title()} -- 1 T3 subbie = {str(datetime.timedelta(seconds=standard_seconds * 1250)).title()})"
                    response_streamloots = f"{stream_loots_seconds} Seconds / Cent Received (1 card = {str(datetime.timedelta(seconds=stream_loots_seconds * 100)).title()})"
                    await bot.send_chat_message(id_streamer, id_streamer, f"Throne & TreatStream Contributions; {response_throne} | DirectDono; {response_direct_dono} | Twitch; {response_twitch} | Streamloots; {response_streamloots}")
                    # if channel_document['data_channel']['hype_train']['current']:
                    #     if channel_document['data_channel']['hype_train']['current_level'] > 1:
                    #         mult = f"{((channel_document['data_channel']['hype_train']['current_level'] - 1) / 10) + standard_ehvent_mult:.1f}X"
                    #         response_twitch = f"{standard_seconds * ((channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult):.2f} Seconds / Cent Received"
                    #         # response_streamloots = f"{stream_loots_const * ((channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult):.2f} Seconds / Pack Purchased"
                    #         response_streamloots = f"{stream_loots_seconds_const * ((channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult):.2f} Seconds / Cent Received"
                    #     else:
                    #         mult = f"{standard_ehvent_mult:.1f}x"
                    #         response_twitch = f"{standard_seconds * standard_ehvent_mult:.2f} Seconds / Cent Received"
                    #         # response_streamloots = f"{stream_loots_const * standard_ehvent_mult:.2f} Seconds / Pack Purchased"
                    #         response_streamloots = f"{stream_loots_seconds_const * standard_ehvent_mult:.2f} Seconds / Cent Received"
                    # else:
                    #     mult = f"1x"
                    #     response_twitch = f"{standard_seconds} Seconds / Cent Received"
                    #     # response_streamloots = f"{stream_loots_const} Seconds / Pack Purchased"
                    #     response_streamloots = f"{stream_loots_seconds_const} Seconds / Cent Received"
                    # await bot.send_chat_message(id_streamer, id_streamer, f"Rate: {mult} | Twitch: {response_twitch} | Streamloots: {response_streamloots}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- times command -- {f}")
                    end_timer("times command")
                    return
            elif command_check.startswith("pack"):
                try:
                    with open("data/pack_link", "r") as file:
                        link = file.read()
                    response_pack = list(map(str, link.splitlines()))
                    for i in range(0, len(response_pack), 10):
                        await bot.send_chat_message(id_streamer, id_streamer, " | ".join(response_pack[i:i + 10]))
                    # await bot.send_chat_message(id_streamer, id_streamer, " | ".join(response_pack), reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- pack command -- {f}")
                    end_timer("pack command")
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} and me go Throbbin in thee Dark.")
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"@FireGMC08, we gonna need you to turn up thee heat bro, ya skills are freezing cold!! :P")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- fire command -- {f}")
                    end_timer("fire command")
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
                    if command.replace(" ", "").replace("hug", "").startswith("@"):
                        target_username = command.replace(" ", "").replace("hug@", "")
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} gives Big Chody Hugs to {target_username}!")
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Big Chody Hugs!!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- hug command -- {f}")
                    end_timer("hug command")
                    return
            elif command_check.startswith("hour"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Tic Tok on thee Clock. Till thee party don't st.. Nopeee")
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
                    await bot.send_chat_message(id_streamer, id_streamer, response_joe)
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
                    await bot.send_chat_message(id_streamer, id_streamer, response_lore)
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"Queen of Penguins.. Who'm cannot fly")
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"Guess who's back back back.. Back again gain gain.. TheeShat is back back back... {data.event.broadcaster_user_name} better RUN RUN RUN!!!")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- shat command -- {f}")
                    end_timer("shat command")
                    return
            elif command_check.startswith(("shit", "holyshit", "unholyshit")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee UnHoliest Of ALLLL UnHoly SHIT!!! eh?", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- shit command -- {f}")
                    end_timer("shit command")
                    return
            elif command_check.startswith("silencer"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name} be sneaky like silencer56")
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
            elif command_check.startswith("whoudini"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Whoooo.. Whoooooo... Whoooooooooooooooooooooooooooo")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - whoudini command -- {f}")
                    end_timer("whoudini command")
                    return
            elif command_check.startswith("willsmash"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Hul... Will Smash!!")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message - willsmash command -- {f}")
                    end_timer("willsmash command")
                    return
            # Mod Commands
            elif command_check.startswith("ad") and (chatter_id in channel_document['data_lists']['mods'] or chatter_id == id_streamer):
                try:
                    pass
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- ad command -- {f}")
                    end_timer("ad command")
                    return
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
                    await bot.send_chat_message(id_streamer, id_streamer, f"Attempting to shut down")
                    obs.disconnect()
                    sys._exit(666)
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- shutdown command -- {f}")
                    end_timer("shutdown command")
                    return
            # Un-Listed Commands
            # elif command_check.startswith("stopfishing") and chatter_id in (id_streamer, channel_document['data_lists']['mods']):
            #     user_document = None
            #     try:
            #         # auto = ""
            #         users_collection = twitch_database.twitch.get_collection('users')
            #         users = users_collection.find({})
            #         for user in users:
            #             user_document = Users.objects.get(_id=user['_id'])
            #             user_document['data_games']['fish']['line']['cast'] = False
            #             if user_document['data_games']['fish']['auto']['cast'] > 0:
            #                 channel_document['data_games']['fish_recast'].append(user_document['name'])
            #             # print(f"UserDoc loaded (ID/NAME/CAST_STATUS); {user_document['_id']}/{user_document['name']}/{user_document['data_games']['fish']['line']['cast']}")
            #             # if user_document['data_games']['fish']['line']['cast']:
            #             #     print(f"{user_document['name']} is fishing")
            #             #     user_document['data_games']['fish']['line'].update(cast=False)
            #             #     print(f"{user_document['name']} cast is set to false")
            #             #     if user_document['data_games']['fish']['auto']['cast'] > 0:
            #             #         print(f"{user_document['name']} has auto-cast set")
            #             #         auto = "Auto "
            #             #         return_value = user_document['data_games']['fish']['auto']['cast'] * fish_auto_cost
            #             #         user_document['data_games']['fish']['auto'].update(cast=0, cost=0, gain=0, lost=0, rewards=[])
            #             #         # user_document['data_games']['fish']['auto']['cast'] = 0
            #             #         # user_document['data_games']['fish']['auto']['cost'] = 0
            #             #         # user_document['data_games']['fish']['auto']['gain'] = 0.0
            #             #         # user_document['data_games']['fish']['auto']['lost'] = 0.0
            #             #         # user_document['data_games']['fish']['auto']['rewards'] = []
            #             #         user_document['data_user']['points'] += return_value
            #             #         print(f"{user_document['name']} fishing stats & points updated")
            #             #     user_document.save()
            #             #     print(f"{user_document['name']} document saved")
            #             #     user_document = Users.objects.get(_id=user_document['_id'])
            #             #     print(f"{user_document['name']} document reloaded")
            #             #     await bot.send_chat_message(id_streamer, id_streamer, f"{user_document['name']} your {auto}Cast has been returned.")
            #             #     await asyncio.sleep(0.25)
            #     except Exception as f:
            #         logger.error(f"{fortime()}: Error in stop fishing command -- {user_document if user_document is not None else 'USER DOCUMENT IS NONE!!!!!!'} -- {f}")
            #         end_timer("stopfishing command error")
            #         return
            elif command_check.startswith("changerate") and chatter_id in (id_streamer, id_streamloots):
                """$changerate accel/slow-new_rate by {{username}} for time_here via StreamLoots Card"""
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
                    if phase not in ("accel", "slow"):
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- phase couldn't be identified -- '{phase}' {type(phase)}")
                        return
                    if not new_rate.isdigit:
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- new_rate couldn't be identified -- '{new_rate}' {type(new_rate)}")
                        return
                    if not last_time.isdigit():
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- last_time couldn't be identified -- '{last_time}' {type(last_time)}")
                        return
                    if phase == "accel":
                        write_clock_phase(phase)
                        new_time = write_clock_accel_time(float(last_time))
                        # write_clock_slow_state(False)
                        # write_clock_accel_state(True)
                        # write_clock_rate(float(new_rate))
                    elif phase == "slow":
                        write_clock_phase(phase)
                        new_time = write_clock_slow_time(float(last_time))
                        # write_clock_accel_state(False)
                        # write_clock_slow_state(True)
                        # write_clock_rate(float(new_rate))
                        # write_clock_slow_strict(float(new_rate))
                    else:
                        logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- phase isn't accel or slow....")
                        return
                    set_timer_rate(obs, new_time)
                    obs.set_source_visibility("NS-Marathon", "TimerSpeed", True)
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, float(last_time) * float(new_rate))
                    special_logger.info(f"{fortime()}: Timer Rate Change; {phase} for {last_time} by {name} -- new_total; {float(read_clock_accel_time()) + float(read_clock_slow_time())}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} has {f'Accelerated' if phase == 'accel' else 'Slowed Down'} Thee Timer Rate to {new_rate} for {str(datetime.timedelta(seconds=float(last_time))).title()}.{f' {str(datetime.timedelta(seconds=new_time)).title()} now remaining.' if new_time != float(last_time) else ''}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                    while True:
                        await asyncio.sleep(float(read_clock_accel_time()) + float(read_clock_slow_time()))
                        if float(read_clock_accel_time()) + float(read_clock_slow_time()) == 0:
                            obs.set_source_visibility("NS-Marathon", "TimerSpeed", False)
                            break
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- changerate command -- {f}")
                    end_timer("changerate command")
                    return
            elif command_check.startswith("pausetime") and chatter_id in (id_streamer, id_streamloots):
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
                    total_pause = write_clock_pause(time_pause)
                    set_timer_pause(obs, True)
                    special_logger.info(f"{name} paused thee timer for {time_pause}")
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, time_pause)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} paused thee timer for {str(datetime.timedelta(seconds=time_pause)).title()}.{f' Timer paused for a total of {str(datetime.timedelta(seconds=int(total_pause))).title()}.' if time_pause != total_pause else ''}{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                    while True:  # ToDo: MONITOR THIS!!!!!!!!!!!!!!!!!!!
                        if read_clock_accel_state():
                            await asyncio.sleep((total_pause / float(read_clock_rate())) + 1)
                        elif read_clock_slow_state():
                            await asyncio.sleep((total_pause * float(read_clock_slow_strict())) + 1)
                        else:
                            await asyncio.sleep(total_pause + 1)
                        if float(read_clock_pause()) == 0:
                            obs.set_source_visibility("NS-Marathon", "TwitchTimerPause", False)
                            break
                        else:
                            total_pause = float(read_clock_pause())
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
                    old_value = float(read_clock_up_time())
                    total_direct_time = write_clock_up_time(time_value)
                    chatter_document, response_level, success = await chatter_doc_swap(name, channel_document, time_value)
                    special_logger.info(f"{fortime()}: Count Up -- Old Value; {old_value} -- New Value; {total_direct_time} -- By; {name} -- Via; {origin}")
                    set_timer_count_up(obs, total_direct_time)
                    obs.set_source_visibility("NS-Marathon", "TimerCountUp", True)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{name} {f'made thee timer count UP for {datetime.timedelta(seconds=time_value)}' if time_value == total_direct_time else f'added {datetime.timedelta(seconds=time_value)} to thee timer counting UP. Total time left {datetime.timedelta(seconds=total_direct_time)}'}.{f' {response_level}' if response_level is not None else ''}{f' {success}' if success is not None else ''}")
                    while True:
                        await asyncio.sleep(float(read_clock_up_time()))
                        if float(read_clock_up_time()) == 0:
                            obs.set_source_visibility("NS-Marathon", "TimerCountUp", False)
                            break
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- directtime command -- {f}")
                    end_timer("directtime command")
                    return
            elif command_check.startswith("startehvent") and chatter_id in (id_streamer, id_streamloots):
                await bot.send_chat_message(id_streamer, id_streamer, f"This command is temporarily unavailable")
                # try:
                #     time_value, name = command.replace(" ", "").replace("startehvent", "").split("by")
                #     level, time_value = time_value.split("-")
                #     name, _ = name.split("via")
                #     channel_document['data_channel']['hype_train'].update(current=True, current_level=int(level))
                #     channel_document.save()
                #     channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
                #     if channel_document['data_channel']['hype_train']['current_level'] > 1:
                #         mult = (channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult
                #     else:
                #         mult = standard_ehvent_mult
                #     obs.set_text("HypeEhVent", f"Hype EhVent Enabled -- {mult:.1f}X")
                #     obs.set_source_visibility("NS-Marathon", "HypeEhVent", True)
                #     await bot.send_chat_message(id_streamer, id_streamer, f"Hype EhVent Forced by {name}!! Multiplier set to: {mult:.1f}X and will last {datetime.timedelta(seconds=int(time_value))}")
                #     await asyncio.sleep(int(time_value))
                #     await bot.send_chat_message(id_streamer, id_streamer, f"Hype EhVent has concluded, multiplier returned to 1X")
                #     obs.set_source_visibility("NS-Marathon", "HypeEhVent", False)
                #     obs.set_text("HypeEhVent", f"Hype EhVent Disabled -- 1X")
                #     channel_document['data_channel']['hype_train'].update(current=False, current_level=1)
                #     channel_document.save()
                # except Exception as f:
                #     logger.error(f"{fortime()}: Error in on_stream_chat_message - startehvent command -- {f}")
                #     end_timer("startehvent command")
                #     return
            elif command_check.startswith("addlurk") and chatter_id == id_streamer:
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    target_username = command.replace(" ", "").replace("addlurk@", "")
                    print(target_username)
                    target_id = None
                    users = users_collection.find({})
                    for user in users:
                        if user['name'].lower() == target_username:
                            target_id = user['_id']
                            break
                    if str(target_id) not in channel_document['data_lists']['lurk'] and target_id is not None:
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
            elif command_check.startswith("testtime") and chatter_id == id_streamer:
                try:
                    seconds, lost = write_clock(720, True, obs)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{float(seconds):.2f} added, {lost} not added")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- testtime command -- {f}")
                    end_timer("testtime")
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
            elif command_check.startswith("updateudocs") and chatter_id == id_streamer:
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    new_field, new_value = command.replace(" ", "").replace("updateudocs", "").split("/", maxsplit=1)
                    users_collection.update_many(
                        {},
                        {"$set": {new_field: new_value}}
                    )
                    await bot.send_chat_message(id_streamer, id_streamer, f"Documents updated with {new_field} and {new_value}")
                except Exception as f:
                    logger.error(f"{fortime()}: Error in on_stream_chat_message -- updateudocs command -- {f}")
                    end_timer("updateudocs command")
                    return
            end_timer(f"{command} command")
            # await flash_window("twitch")
        # ToDo: Add # command recognition. #RIP @TARGET_NAME, pops up a 'moment of silent for target_name' or alike
        #  #oof
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
                    chatter_document, response_level = await twitch_points_transfer(chatter_document, channel_document, 100000)
                    response_ranword = f"You used thee random word!! It was {channel_document['data_games']['ranword']}. You gained 1,000 points!"
                    ran_word(channel_document)
            except Exception as f:
                logger.error(f"{fortime()}: Error in on_stream_chat_message -- ranword_bit -- {f}")
                pass
            # try:
            #     for keyword, properties in keywords.items():
            #         if re.search(keyword, messagecont):
            #             await bot.send_chat_message(id_streamer, id_streamer, properties['response'], reply_parent_message_id=data.event.message_id)
            # except Exception as f:
            #     logger.error(f"{fortime()}: Error in on_stream_chat_message -- keywords_loop -- {f}")
            #     pass
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
        response_udocs = None
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
                seconds, not_added = write_clock(seconds, True, obs)
                response_udocs = f"{chatter_username} added {datetime.timedelta(seconds=int(seconds))} to thee clock{f' -- MAX TIME HIT {not_added} to thee clock' if not_added is not None else ''} {response_thanks}"
                special_logger.info(response_udocs)
            except Exception as f:
                logger.error(f"{fortime()}: Error in on_stream_chat_message -- power_ups -- {f}")
                end_timer("power_ups")
                return
        if response_udocs is not None or response_ranword is not None or response_level is not None:
            if response_level is not None and command is not None and response_udocs is None and response_ranword is None:
                end_timer("level up during command")
                return
            await bot.send_chat_message(id_streamer, id_streamer, f"{f'{response_ranword}.' if response_ranword is not None else ''} {f'{response_udocs}.' if response_udocs is not None else ''} {f'{response}.' if response is not None else ''} {f' {response_level}.' if response_level is not None else ''}", reply_parent_message_id=data.event.message_id)

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
            seconds, time_not_added = write_clock(seconds, True, obs)
            response = f", adding {str(datetime.timedelta(seconds=int(seconds))).title()} to thee clock!!{f' Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}{f' {response_level}.' if response_level is not None else ''}"
        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} has cheered {data.event.bits}{response}")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_cheer' -- {e}")
        return


async def on_stream_follow(data: ChannelFollowEvent):
    try:
        if read_bot_raid() == "False":
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
        # await bot.send_chat_message(id_streamer, id_streamer, f"Choo Choooooooo!! Hype train started by {data.event.last_contribution.user_name}{f', also triggering a Hype EhVent, doubling all twitch contributions to thee clock!!' if channel_document['data_channel']['writing_clock'] else '!'}{response}")
        await bot.send_chat_message(id_streamer, id_streamer, f"Choo Choooooooo!! Hype train started by {data.event.last_contribution.user_name}.{response}")
        channel_document['data_channel']['hype_train'].update(current=True, current_level=data.event.level)
        channel_document.save()
        # if channel_document['data_channel']['writing_clock']:
        #     # obs.set_text("HypeEhVent", f"Hype EhVent Enabled -- {standard_ehvent_mult}X")
        #     # obs.set_source_visibility("NS-Marathon", "HypeEhVent", True)
        #     if data.event.level > 1:
        #         mult = (data.event.level - 1) / 10 + standard_ehvent_mult
        #     else:
        #         mult = standard_ehvent_mult
        #     obs.set_text("HypeEhVent", f"HypeEhVent Enabled -- {mult:.1f}X")
        #     obs.set_source_visibility("NS-Marathon", "HypeEhVent", True)
        #     response_writing_to_log = f"New Hype EhVent Level -- {mult:.1f}X -- {data.event.level} -- {response}"
        # else:
        response_writing_to_log = f"Thee Hype Train ENABLED -- {data.event.level} level"
        special_logger.info(response_writing_to_log)
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
        # await bot.send_chat_message(id_streamer, id_streamer, f"Hype Train Completed @ {data.event.level}!!{f' New local record reached at {new_hype_train_record_level}!!' if record_beat else ''{}{f' Thee Hype EhVent is now over, all contributions to thee clock have returned to normal.' if channel_document['data_channel']['writing_clock'] else ''} {response_thanks}")
        await bot.send_chat_message(id_streamer, id_streamer, f"Hype Train Completed @ {data.event.level}!!{f' New local record reached at {new_hype_train_record_level}!!' if record_beat else ''} {response_thanks}")
        channel_document['data_channel']['hype_train'].update(current=False, current_level=1, last=fortime(),
                                                              last_level=data.event.level, record_level=new_hype_train_record_level)
        channel_document.save()
        # special_logger.info(f"Thee Hype EhVent DISABLED" if channel_document['data_channel']['writing_clock'] else f"Hype Train Ended")
        special_logger.info(f"Hype Train Ended")
        # if channel_document['data_channel']['writing_clock']:
        #     obs.set_source_visibility("NS-Marathon", "HypeEhVent", False)
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
            await bot.send_chat_message(id_streamer, id_streamer, f"New Hype Train Level!! Currently @ {data.event.level}.{response}")
            special_logger.info(f"New Hype Train Level!! Currently @ {data.event.level}.{response}")
        else:
            new_hype_train_current_level = channel_document['data_channel']['hype_train']['current_level']
        channel_document['data_channel']['hype_train'].update(current_level=new_hype_train_current_level)
        channel_document.save()
        # if channel_document['data_channel']['writing_clock']:
        #     if new_hype_train_current_level > 1:
        #         mult = (new_hype_train_current_level - 1) / 10 + standard_ehvent_mult
        #     else:
        #         mult = standard_ehvent_mult
        #     obs.set_text("HypeEhVent", f"HypeEhVent Enabled -- {mult:.1f}X")
        #     response_writing_to_log = f"New Hype EhVent Level -- {mult:.1f}X -- {data.event.level} -- {response}"
        # else:
        response_writing_to_log = f"New Hype Train Level!! Currently @ {data.event.level} -- {response}"
        special_logger.info(response_writing_to_log)
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
        await bot.send_chat_message(id_streamer, id_streamer, f"Poll '{data.event.title}' has started. Choices are: {' - '.join(choices)}. Poll will end in {datetime.timedelta(seconds=abs(time_till_end - seconds_now))}. Voting with extra channel points is {'enabled' if data.event.channel_points_voting.is_enabled else 'disabled'}")
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
        await bot.send_chat_message(id_streamer, id_streamer, f"Poll '{data.event.title}' has ended. Thee winner is: {winner[1].title()} with {winner[0]} votes!")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_poll_end' -- {e}")
        return


async def on_stream_point_redemption(data: ChannelPointsCustomRewardRedemptionAddEvent):
    try:
        # print(f"ChannelPointsRedemption\nTitle: {data.event.reward.title}\nCost: {data.event.reward.cost}\nPrompt: {data.event.reward.prompt}")  # For debugging TEMP LEAVE HERE COMMENTED
        check_in, multiple_spin, timeout = True, False, False
        response_redemption, response_check_in, times_spun = None, None, None
        channel_document = await get_channel_document(data.event.broadcaster_user_id, data.event.broadcaster_user_name, data.event.broadcaster_user_login)
        special_logger.info(f"fin--RewardID: {data.event.reward.id} -- {data.event.reward.title}")
        if data.event.reward.title == "Text-to-Speech":
            return
        elif data.event.reward.title == "Stream Check-In":
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
            seconds, time_not_added = write_clock(seconds, True, obs)
            response_redemption = f"added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {data.event.reward.cost:,} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        elif data.event.reward.title == "Add 20 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 1200
            seconds, time_not_added = write_clock(seconds, True, obs)
            response_redemption = f"{data.event.user_name} added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {data.event.reward.cost:,} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        elif data.event.reward.title == "Add 30 Mins" and channel_document['data_channel']['writing_clock']:
            seconds = 1800
            seconds, time_not_added = write_clock(seconds, True, obs)
            response_redemption = f"added {str(datetime.timedelta(seconds=int(seconds))).title()} to thee timer with {data.event.reward.cost:,} {channel_point_name}. {f'Max Time Reached! {time_not_added} not added to thee clock.' if time_not_added is not None else ''}"
        elif data.event.reward.title == "Timeout Somebody Else":
            if data.event.user_input.removeprefix("@").lower().startswith(name_streamer):
                await bot.send_chat_message(id_streamer, id_streamer, f"You cannot timeout thee Streamer bud, Mods please give back {data.event.user_name}'s {data.event.reward.cost:,} {channel_point_name} back.")
                return
            timeout = True
            timeout_error_msg = f"{data.event.user_name} tried timing out {data.event.user_input} and it didn't work automagically"
            try:
                time_sleep = 300
                moderator = False
                user_t = None
                target = data.event.user_input.lower()
                if " " in target:
                    target, _ = target.split(" ", maxsplit=1)
                if target.startswith("@"):
                    target = target.removeprefix("@")
                chatters = await bot.get_chatters(id_streamer, id_streamer)
                for chatter in chatters.data:
                    if chatter.user_name.lower() == target:
                        user_t = chatter
                        if user_t.user_id in channel_document['data_lists']['mods']:
                            moderator = True
                if user_t is None:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} attempted to time out {data.event.user_input}. {target} not found in users currently connected to chat. Automagic operation failed.")
                    return
            except Exception as g:
                logger.error(f"{fortime()}: Error in channel_point_redemption - timeout - timing out user\n{data.event}\n\n{g}")
                await bot.send_chat_message(id_streamer, id_streamer, f"{timeout_error_msg} -- {g}")
                return
            try:
                if user_t is not None:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} timed out {user_t.user_name} for {str(datetime.timedelta(seconds=time_sleep)).title()}.")
                    await bot.ban_user(id_streamer, id_streamer, user_t.user_id, f"Channel Point Redemption via {data.event.user_name}", time_sleep)
                    if moderator:
                        await asyncio.sleep(time_sleep + 1)
                        await bot.add_channel_moderator(id_streamer, user_t.user_id)
                else:
                    logger.error(f"{fortime()}: Error in channel_point_redemption - timeout (user_t IS NONE) - timing out user\n{data.event}")
                    await bot.send_chat_message(id_streamer, id_streamer, timeout_error_msg)
            except Exception as g:
                logger.error(f"{fortime()}: Error in channel_point_redemption - timeout - granting mod priv's to {user_t} -- {g}")
                await bot.send_chat_message(id_streamer, id_streamer, f"{user_t.user_name} is a moderator, but restoring privileges failed!! -- {g}")
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
        if not timeout:
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} {response_check_in if response_check_in is not None else response_redemption if response_redemption is not None else f'used {data.event.reward.cost:,} {channel_point_name} to redeem {data.event.reward.title}'}{f' {times_spun} times spun.' if multiple_spin else ''}")
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


async def on_stream_prediction_end(data: ChannelPredictionEndEvent):
    try:
        print(data.event.winning_outcome_id)
        if data.event.status == "archived":
            print('arch')
            pass
        else:
            await bot.send_chat_message(id_streamer, id_streamer, f"Prediction '{data.event.title}' has ended with status: {data.event.status}.")
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_prediction_end' -- {e}")
        return


async def on_stream_prediction_lock(data: ChannelPredictionEvent):
    try:
        print(data.event.title)
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'on_stream_prediction_lock' -- {e}")
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
        await bot.send_chat_message(id_streamer, id_streamer, f"Hola. I is here :D Big Chody Hugs.")
        if channel_document['data_channel']['writing_clock']:
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
        # await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name} has faded into thee shadows. {response_thanks}")
        await bot.send_chat_message(id_streamer, id_streamer, f"I have faded into thee shadows. {response_thanks}")
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
                    position_x = 766
                    position_y = 1666.0
                    rotation = 0.0
                    reset_position_x = 767
                    reset_position_y = 494
                    reset_rotation = 180.0
                else:
                    position_x = 767
                    position_y = 494
                    rotation = 180.0
                    reset_position_x = 766
                    reset_position_y = 1666.0
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
                if old_rotation == 180:
                    check_position = obs.get_source_transform("NS-Cam", "nvcam")
                    if check_position["positionY"] == 466:
                        new_rotation = 181
                        old_rotation = 0.0
                        while new_rotation != old_rotation:
                            if new_rotation == 361.0:
                                new_rotation = 0.0
                                if new_rotation == old_rotation:
                                    break
                            obs.set_source_transform("NS-Cam", "nvcam", {"rotation": new_rotation})
                            new_rotation += 1
                            await asyncio.sleep(0.00005)
        elif webcam_manipulation == "reset":
            obs.set_source_transform("NS-Cam", "nvcam", {"positionX": 766, "positionY": 1666.0, "rotation": 0.0})
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
        logger.info(f"{long_dashes}\nDisconnected from MongoDB\n{long_dashes}")
    except Exception as e:
        logger.error(f"{fortime()}: Error Disconnection MongoDB -- {e}")
        return


async def document_points_transfer(direction, transfer_value, chatter_document, chatter_document_discord):
    try:
        if None in (chatter_document, chatter_document_discord):
            return
        transfer_value = int(transfer_value)
        if direction == "twitch":
            if transfer_value > chatter_document_discord['points_value']:
                await bot.send_chat_message(id_streamer, id_streamer, f"You do not have enough discord points to transfer. You have {chatter_document_discord['points_value']} points")
                return
            new_discord_points = chatter_document_discord['points_value'] - transfer_value
            chatter_document_discord.update(points_value=new_discord_points)
            chatter_document_discord.save()
            new_twitch_points = chatter_document['data_user']['points'] + transfer_value
            chatter_document['data_user'].update(points=new_twitch_points)
            chatter_document.save()
        elif direction == "discord":
            if transfer_value > chatter_document['data_user']['points']:
                await bot.send_chat_message(id_streamer, id_streamer, f"You do not have enough twitch points to transfer. You have {chatter_document['data_user']['points']:,.2f} points")
                return
            new_discord_points = chatter_document_discord['points_value'] + transfer_value
            chatter_document_discord.update(points_value=new_discord_points)
            chatter_document_discord.save()
            new_twitch_points = chatter_document['data_user']['points'] - transfer_value
            chatter_document['data_user'].update(points=new_twitch_points)
            chatter_document.save()
        else:
            await bot.send_chat_message(id_streamer, id_streamer, f"Backend Mess up.... {direction} is thee direction")
            return
        await bot.send_chat_message(id_streamer, id_streamer, f"Transferred {transfer_value} to your {direction} profile.")
    except Exception as e:
        logger.error(f"{fortime()}: Error in points_transfer -- {chatter_document['_id'][:5]}/{chatter_document['name']}/{chatter_document['data_user']['login']}/{chatter_document['data_user']['discord_id']} -- {chatter_document_discord['author_id']}/{chatter_document_discord['author_name']}/{chatter_document_discord['guild_name']}/{chatter_document_discord['twitch_id']} -- {e}")
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
            if type(data) is not None:
                chatter_document = Users.objects.get(_id=chatter_id)
            else:
                chatter_document = Users.objects.get(name=chatter_name.lower())
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
            # if channel_document['data_channel']['hype_train']['current'] and add:
            #     value *= ((channel_document['data_channel']['hype_train']['current_level'] - 1) / 10 + standard_ehvent_mult)
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
            new_user_xp_points = float(chatter_document['data_rank']['xp'] + value)
            x = 0
            while True:
                level_mult = 1.0
                if new_user_level > 1:
                    level_mult += float((new_user_level / 2) * new_user_level)
                xp_needed = (level_const * level_mult) * new_user_level
                special_logger.info(f"XP-INCREASE: {user_name} Level(XP): {new_user_level}({new_user_xp_points}) -- XP Needed: {xp_needed}")
                if new_user_xp_points >= xp_needed:
                    new_user_level += 1
                else:  #if new_user_xp_points < xp_needed:  # and chatter_document['_id'] == id_streamer:
                    break
                    # new_user_level_test = new_user_level - 1
                    # if new_user_level_test > 1:
                    #     level_mult += float((new_user_level_test / 2) * new_user_level_test)
                    # xp_needed = (level_const * level_mult) * new_user_level_test
                    # if new_user_xp_points < xp_needed and new_user_level > 1:
                    #     new_user_level -= 1
                    #     special_logger.info(f"XP-DECREASE: {user_name} Level(XP): {new_user_level}({new_user_xp_points}) -- XP Needed: {xp_needed}")
                    # else:
                    #     break
                # else:
                #     break
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
            print("Attempting to stop auto-casting. Stand By")
            try:
                users_collection = twitch_database.twitch.get_collection('users')
                users_docs = users_collection.find({})
                for user in users_docs:
                    user_document = await get_chatter_document(None, channel_document, user['_id'], user['name'], user['data_user']['login'], id_streamer, name_streamer)
                    if user_document is not None:
                        if user_document['data_games']['fish'] == "" or not user_document['data_games']['fish']:
                            user_document['data_games']['fish'] = {"auto": {"cast": 0, "cost": 0, "gain": 0.0, "lost": 0.0, "rewards": []}, "line": {"cast": False, "cut": False, "cut_by": "", "cut_last": None}}
                            user_document.save()
                        elif user_document['data_games']['fish']['line']['cast']:  #if type(user_document['data_games']['fish']) == object:
                            user_document['data_games']['fish']['line']['cast'] = False
                            user_document.save()
                            await bot.send_chat_message(id_streamer, id_streamer, f"{user_document['name']} your cast was interrupted by a bot restart. Wait a few mins and then try again")
                        if user_document['data_games']['fish']['auto']['cast'] > 0:
                            channel_document['data_games']['fish_recast'].append(user_document['name'])
                channel_document.save()
            except Exception as f:
                print(f"{fortime()}: Error in attempt to stop auto_casting;;;; {f}")
                pass
            print("Shutting down twitch bot processes. Stand By")
            if obs_loaded:
                if channel_document is not None:
                    if channel_document['data_channel']['writing_clock']:
                        obs.set_source_visibility("NS-Marathon", "TwitchTimer", False)
                        obs.set_source_visibility("NS-Marathon", "TwitchTimerSoFar", False)
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
            print("Twitch bot processes shut down successfully")
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

    # await event_sub.listen_extension_bits_transaction_create(id_streamer, on_stream_bits_ext_transfer)  # WebHooks Needed For This
    await event_sub.listen_channel_ad_break_begin(user.id, on_stream_ad_start)
    await event_sub.listen_channel_chat_message(user.id, user.id, on_stream_chat_message)
    await event_sub.listen_channel_chat_notification(user.id, user.id, on_stream_chat_notification)
    await event_sub.listen_channel_cheer(user.id, on_stream_cheer)
    await event_sub.listen_channel_follow_v2(user.id, user.id, on_stream_follow)
    # await event_sub.listen_goal_begin(user.id, on_stream_goal_begin)  # Don't think I'll use this or thee next two lines, I don't use goals
    # await event_sub.listen_goal_progress(user.id, on_stream_goal_progress)
    # await event_sub.listen_goal_end(user.id, on_stream_goal_end)
    await event_sub.listen_hype_train_begin(user.id, on_stream_hype_begin)
    await event_sub.listen_hype_train_end(user.id, on_stream_hype_end)
    await event_sub.listen_hype_train_progress(user.id, on_stream_hype_progress)
    await event_sub.listen_channel_poll_begin(user.id, on_stream_poll_begin)
    await event_sub.listen_channel_poll_end(user.id, on_stream_poll_end)
    await event_sub.listen_channel_points_custom_reward_redemption_add(user.id, on_stream_point_redemption)
    await event_sub.listen_channel_prediction_begin(user.id, on_stream_prediction_begin)
    # await event_sub.listen_channel_prediction_end(user.id, on_stream_prediction_end)  # ToDo: Find out why this is broke!!!! -- TypeError: twitchAPI.object.eventsub.TopPredictors() argument after ** must be a mapping, not list
    # await event_sub.listen_channel_prediction_lock(user.id, on_stream_prediction_lock)  # This one is fucking broke too... Same error ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
        value = False
        if channel_document['data_channel']['writing_clock']:
            value = True
        obs.set_source_visibility("NS-Marathon", "TwitchTimer", value)
        obs.set_source_visibility("NS-Marathon", "TwitchTimerSoFar", value)
        # obs.set_source_visibility("NS-Marathon", "HypeEhVent", False)
        # obs.set_source_visibility("NS-Overlay", "InAd", False)
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
                            elif user_input == 9:
                                reset_night_mode()
                                await asyncio.sleep(2)
                            elif user_input == 10:
                                reset_flash_settings()
                                await asyncio.sleep(2)
                            else:
                                print("Not valid, try again..")
                                await asyncio.sleep(2)
                elif user_input == 2:
                    print(str(datetime.timedelta(seconds=int(float(read_clock())))).title())
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
                   "Enter 2 to get current time left",
                   "Enter 3 to +/- time",
                   "Enter 4 for Bot Protection",
                   "Enter 0 to Halt Bot"]
    bot_options_one = ["Enter 1 to Enable/Disable Writing to Clock",
                       # "Enter 2 to Enable/Disable Thee Hype EhVent",
                       "Enter 3 to Change Current time left",
                       "Enter 4 to Change Max Time",
                       "Enter 5 to Change Total Time",
                       "Enter 6 to Change Countdown ACCEL Rate",
                       "Enter 7 to Change Countdown SLOW Rate",
                       "Enter 8 to Change Countdown Pause",
                       "Enter 9 to Enable/Disable Night Time Mode",  # ToDo: ADD THIS
                       # f"Enter 9 to Reset Paused OBS Source" if float(read_clock_pause()) != 0.0 else '',
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
    asyncio.run(disconnect_mongo())
    asyncio.run(full_shutdown(logger_list))
