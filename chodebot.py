"""
All currency in USD
"""
import os
import time
import random
import asyncio
import logging
import datetime
# from timeit import default_timer as timer  #start = timer()  #end = timer()  #print(start - end)
from dotenv import load_dotenv
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope  #, ChatEvent  # Maybe attempt this again?? IDK
from pyprobs import Probability as pr
from mondocs import Channels, Users, EconomyData
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.oauth import UserAuthenticationStorageHelper
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME
from functions import logs_directory, chat_log, read_clock, write_clock, long_dashes, reset_max_time, reset_total_time, reset_current_time, reset_level_const  #, get_sec
# from twitchAPI.chat import Chat, ChatCommand, EventData, ChatMessage, ChatUser, ChatSub  # Maybe attempt this again? IDK
from twitchAPI.object.eventsub import ChannelAdBreakBeginEvent, ChannelChatMessageEvent, ChannelChatNotificationEvent, \
    ChannelCheerEvent, ChannelFollowEvent, ChannelPollBeginEvent, ChannelPollEndEvent, ChannelPointsCustomRewardRedemptionAddEvent, \
    ChannelPredictionEvent, ChannelPredictionEndEvent, ChannelRaidEvent, ChannelSubscribeEvent, ChannelSubscriptionGiftEvent, \
    ChannelUpdateEvent, ExtensionBitsTransactionCreateEvent, HypeTrainEvent, HypeTrainEndEvent, StreamOnlineEvent, StreamOfflineEvent  #, GoalEvent


# ToDo List ------------------------------------------------------------------------------------------------------------
#  FollowAge
#  --- Hype system that works up to a power hour ei;                      --- TRYING HYPE TRAIN system -- IS IMPLEMENTED           |
#  user1 throws 1000 bitties, user2 throws 500, in quick order, third user that throws bitties or subbies starts a                 |
#  'Power Hype Hour' were a certain threshold must be reached in order for all monetary stuffz to count as power hour stuff, or    |
#  gets added as normal after time limit is exceeded if unsuccessful ---                                                           |
#  Add a return for in over-write protections kick in aka, if time isn't written due to MAX_TIME being topped out by TOTAL_TIME
#  ---------------------------------------------------- End of List ----------------------------------------------------

load_dotenv()
id_twitch_client = os.getenv("client")
id_twitch_secret = os.getenv("secret")
id_streamer = os.getenv("broadcaster")
mongo_login_string = os.getenv("monlog_string")
mongo_twitch_collection = os.getenv("montwi_string")
mongo_discord_collection = os.getenv("mondis_string")

lurk_ignore_list = []
ignore_list = ["431026547",  # Stickersbot
               "52268235",  # Wizebot
               "253326823",  # Blerps
               "100135110",  # StreamElements
               "431199284",  # KofiBot
               "261104033"]
fish_rewards = [['TestOBJ1', 5],
                ['TestOBJ2', 10],
                ['TestOBJ3', 15],
                ['TestOBJ4', 20]]
pants_choices = ["Commando",
                 "Wearing Boxers"]
target_scopes = [AuthScope.BITS_READ,
                 AuthScope.CLIPS_EDIT,
                 AuthScope.CHANNEL_BOT,
                 AuthScope.USER_READ_CHAT,
                 AuthScope.USER_WRITE_CHAT,
                 AuthScope.CHANNEL_MODERATE,
                 AuthScope.CHANNEL_READ_ADS,
                 AuthScope.CHANNEL_READ_GOALS,
                 AuthScope.USER_READ_BROADCAST,
                 AuthScope.CHANNEL_MANAGE_POLLS,
                 AuthScope.USER_MANAGE_WHISPERS,
                 AuthScope.CHANNEL_SUBSCRIPTIONS,
                 AuthScope.CHANNEL_READ_HYPE_TRAIN,
                 AuthScope.MODERATOR_READ_CHATTERS,
                 AuthScope.MODERATOR_READ_FOLLOWERS,
                 AuthScope.CHANNEL_READ_PREDICTIONS,
                 AuthScope.MODERATOR_MANAGE_SHOUTOUTS,
                 AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
                 AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
                 AuthScope.CHANNEL_MANAGE_PREDICTIONS]  # ToDo: FIGURE OUT WHY THEE PREDICTION SHIT FLIPS OUT ON END/LOCK CALL!!!!!!!!!!!
marathon_rewards = ["8099f524-c2e8-41de-b31f-35de4ff7f084",  # 10
                    "55ec31e9-98f8-46ef-939e-c7835514fd1b",  # 20
                    "dc306b71-9fd2-422e-968b-61690c1b7387"]  # 30  # ToDo: FIGURE OUT WHY THIS SHIT SAYS IT'S NOT MINE

level_const = 100
cmd = ("$", "!")  # What thee commands can start with
raid_seconds = 30  # How many Seconds PER Raid Viewer to add to thee clock
follow_seconds = 30  # How many Seconds PER Follower to add to thee clock
standard_points = 5  # Base value -- points for chatting, bitties, subbing/resubbing, gifting subbies etc.
standard_seconds = 1  # Base value -- Seconds per Cents  AKA: 1Second = 1cent per 1Sec = $36/Hour //// 2Second = 1cent per 2Sec = $18/Hour
thee_hype_ehvent_mult = 2  # Base value for hype ehvent multiplier  # ToDo: Add bit in write_clock via functions file, to write custom hype_ehvent multipliers!!!
writing_to_clock = True  # Marathon started? Either configure this or in bot loop, option to set it there
thee_hype_ehvent_enabled = False  # In a marathon? New System Uses HypeTrains to trigger, however can still be manually turned on/off via bot loop
discord_link = "http://discord.theechody.ca"  # Your discord link here
response_thanks = f" Much Love <3"  # A response message one wants to be repeated at thee end of monetary things, START with a SPACE
channel_point_name = "Theebucks"  # Channel point name

bot = Twitch(id_twitch_client, id_twitch_secret)


async def get_ad_time(ad_schedule):  #, attempt_snooze: bool = False):
    # if attempt_snooze:
    #     ad_next_seconds = await get_ad_seconds(ad_schedule.next_ad_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:])
    #     now_time_seconds = await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
    # else:
    ad_next_seconds = await get_ad_seconds(ad_schedule.next_ad_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:])
    now_time_seconds = await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
    return ad_next_seconds, now_time_seconds


async def get_ad_seconds(time):
    y, mo, d, h, mi, s = time.split(":")
    return int(y) * 1 + int(mo) * 1 + int(d) * 1 + int(h) * 3600 + int(mi) * 60 + int(s)
    # return int(y) * 31536000 + int(mo) * 2628288 + int(d) * 86400 + int(h) * 3600 + int(mi) * 60 + int(s)


async def on_stream_ad_start(data: ChannelAdBreakBeginEvent):
    try:
        if data.event.is_automatic:
            auto_response = f"This is a automatically scheduled ad break"
        else:
            auto_response = f"This is a manually ran ad to attempt to time things better"
        ad_schedule = await bot.get_ad_schedule(id_streamer)
        ad_next_seconds, now_time_seconds = await get_ad_time(ad_schedule)
        # ad_next_seconds = await get_ad_seconds(ad_schedule.next_ad_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:])
        # now_time_seconds = await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
        await bot.send_chat_message(id_streamer, id_streamer, f"Incoming ad break\n{auto_response} and should only last {data.event.duration_seconds} seconds. Next ad inbound in {datetime.timedelta(seconds=abs(ad_next_seconds - now_time_seconds))}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_ad_start' -- {e}")
        return


async def on_stream_bits_ext_transfer(data: ExtensionBitsTransactionCreateEvent):  # WebHooks Needed For This
    try:
        response = "!"
        chatter_document = await get_chatter_document(data)
        if chatter_document is not None:
            points_to_add = round(standard_points * data.event.product.bits)
            await twitch_points_transfer(chatter_document, points_to_add)
        if writing_to_clock:
            seconds = round(standard_seconds * data.event.product.bits)
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            formatted_time_added = datetime.timedelta(seconds=seconds)
            response = f", adding {formatted_time_added} to thee clock!!"
        await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} used {data.event.product.bits} on {data.event.product.name}{response}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_bits_ext_transfer' -- {e}")
        return

registered_commands = ["bitsleader",
                       "commands",
                       "discord",
                       "fish",
                       "gamble 'NUMBER_HERE'",
                       "hug",
                       "joe",
                       "lastcomment",
                       "levelcheck",
                       "levelleader",
                       "lore",
                       "lurk",
                       "pants",
                       "pointscheck",
                       "pointsleader",
                       "pt 'discord/twitch' 'NUMBER_HERE'",
                       "pp",
                       "tag"]  # ToDo: MONITOR NEW COMMAND SYSTEM


async def on_stream_chat_message(data: ChannelChatMessageEvent):
    # ToDo: ------------------------------------------------------------------------------------------------------------
    #  LEVELING SYSTEM
    #  Little 'mini-games' --pants, fight, fish, bet, etc
    #  Figure out music queueing system, gonna need ability to manipulate VLC player.. or make my own? haha yeah right
    #  -------------------------------------- End of on_stream_chat_message List ---------------------------------------
    try:
        chatter_id = data.event.chatter_user_id
        if chatter_id in ignore_list:
            return
        if chatter_id == id_streamer and not data.event.message.text.startswith(cmd):
            return
        chatter_username = data.event.chatter_user_name
        chatter_document = await get_chatter_document(data)
        channel_document = await get_channel_document(data)
        if None in (chatter_document, channel_document):
            logger.error(f"Chatter/Channel Document is None!! -- chatter-{chatter_document} -- channel-{channel_document}")
            pass
        if chatter_id in lurk_ignore_list:
            try:
                lurk_ignore_list.remove(chatter_id)
                await bot.send_chat_message(id_streamer, id_streamer, f"Well, lookie who came back from thee shadows, {chatter_username}.")
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message -- welcome back from lurk bit -- {f}")
                pass
        if data.event.message.text.startswith(cmd):
            command = data.event.message.text
            for letter in cmd:
                command = command.lstrip(letter)
            command = command.lower()
            if command.replace(" ", "").startswith(("bittiesleader", "bitsleader")):
                try:
                    bits_lb = await bot.get_bits_leaderboard()
                    print(bits_lb.total)
                    users_board = ""
                    for user in bits_lb:
                        users_board += f"#{user.rank:02d}: {user.user_name}: {user.score} - "
                    await bot.send_chat_message(id_streamer, id_streamer, f"Bitties 4 Titties Leaderboard: {users_board[:-3]}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - bittiesleader command -- {f}")
                    return
            elif command.replace(" ", "").startswith(("commands", "cmd", "cmds", "commandlist", "cmdlist")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Registered commands are: {' - '.join(registered_commands)}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - commands command -- {f}")
                    return
            elif command.replace(" ", "").startswith(("discord", "discordlink")):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Thee discord link is: {discord_link}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- discord command -- {f}")
                    return
            elif command.replace(" ", "").startswith("fish"):
                try:
                    fish = random.choice(fish_rewards)
                    new_points = fish[1] + chatter_document['user_points']
                    chatter_document.update(user_points=new_points)
                    chatter_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"You caught a {fish[0]} worth {fish[1]} points! Your new points are: {new_points}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- fish command -- {f}")
                    return
            elif command.replace(" ", "").startswith("gamble"):
                try:
                    bet_value = command.lstrip("gamble ")
                    if bet_value.isdigit():
                        bet_value = int(bet_value)
                    else:
                        print(f"--{bet_value}")
                        await bot.send_chat_message(id_streamer, id_streamer, f"Your command should resemble '{f' or '.join(cmd)}' gamble X where X, put your bet value. Try again", reply_parent_message_id=data.event.message_id)
                        return
                    print(f"{bet_value} vs {chatter_document['user_points']}")
                    if bet_value > chatter_document['user_points']:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You do not have enough points to bet that. You currently have {chatter_document['user_points']}", reply_parent_message_id=data.event.message_id)
                        return
                    elif bet_value <= chatter_document['user_points']:
                        if pr.prob(97.5/100):
                            response = f"lost {bet_value}"
                            new_points_value = chatter_document['user_points'] - bet_value
                            await twitch_points_transfer(chatter_document, bet_value, False)
                            await bot.send_chat_message(id_streamer, id_streamer, f"You lost thee gamble, I ate your points. They tasted yummy! You now have {new_points_value} points.", reply_parent_message_id=data.event.message_id)
                        else:
                            won_amount = bet_value * 100000
                            response = f"won {won_amount} with a bet of {bet_value}"
                            new_points_value = chatter_document['user_points'] + won_amount
                            await twitch_points_transfer(chatter_document, won_amount)
                            await bot.send_chat_message(id_streamer, id_streamer, f"You won thee gamble, winning {won_amount} making your new total {new_points_value}!! Congratz!!!", reply_parent_message_id=data.event.message_id)
                        formatted_time = fortime()
                        gamble_logger.info(f"{formatted_time}: {chatter_username}/{chatter_id} gambled and {response}.")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - gamble command -- {f}")
                    gamble_logger.error(f"{formatted_time}: Error in on_stream_chat_message - gamble command -- {f}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Something wen't wrong, TheeChody will fix it sooner than later. Error logged in thee background", reply_parent_message_id=data.event.message_id)
                    return
            elif command.replace(" ", "").startswith("hug"):
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"Big Chody Hugs!!!", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- hug command -- {f}")
                    return
            elif command.replace(" ", "").startswith("joe"):  # and chatter_id == "806552159":
                try:
                    if chatter_id == "806552159":  # Joe's id
                        response = f"Dammit Me!!!.. Wait I mean Dammit Joe!!!"
                    else:
                        response = f"Dammit Joe!!!"
                    await bot.send_chat_message(id_streamer, id_streamer, response)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - joe command -- {f}")
                    return
            elif command.replace(" ", "").startswith(("lastcomment", "lastmessage")):
                if chatter_id == id_streamer:
                    return
                try:
                    last_message = None
                    with open(chat_log, "r") as file:
                        chat_logs = file.read()
                    chat_logs = list(map(str, chat_logs.splitlines()))
                    for last in reversed(chat_logs):
                        if last.startswith(chatter_id):
                            user_name, last_message = last.split(": ", maxsplit=1)
                            break
                    await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name}!! {chatter_username}'s last message was: {last_message if not None else 'Not Found!!!'}")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - lastcomment command -- {f}")
                    return
            elif command.replace(" ", "").startswith("levelcheck"):
                try:
                    if chatter_document is not None:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are {chatter_document['user_level']} level", reply_parent_message_id=data.event.message_id)
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong getting your chatter_document", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- levelcheck command -- {f}")
                    return
            elif command.replace(" ", "").startswith("levelleader"):
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    users = users_collection.find({})
                    users_sorted = sorted(users, key=lambda user: user['user_xp_points'], reverse=True)
                    response = []
                    for n, user in enumerate(users_sorted[:5]):
                        response.append(f"{n+1}: {user['user_name']}/{user['user_level']}/{user['user_xp_points']}")
                    await bot.send_chat_message(id_streamer, id_streamer, f"Leaderboard: {' - '.join(response)}")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- leaderboard command -- {f}")
                    return
            elif command.replace(" ", "").startswith("lore"):  # and chatter_id == "170147951":
                try:
                    if chatter_id == "170147951":  # Maylore's id
                        response = f"Fucking run Chody!! Run! It's Maylore himself here to taunt you"
                    else:
                        response = f"{chatter_username} is taunting you with Maylore's command"
                    await bot.send_chat_message(id_streamer, id_streamer, response)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - lore command -- {f}")
                    return
            elif command.replace(" ", "").startswith("lurk"):
                try:
                    if chatter_id not in lurk_ignore_list and chatter_id != id_streamer:
                        lurk_ignore_list.append(chatter_id)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} fades off into thee shadows. Much love")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - lurk command -- {f}")
                    return
            elif command.replace(" ", "").startswith("pants"):
                try:
                    target = await select_target(chatter_id)
                    pants_response = random.choice(pants_choices)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} pulls down thee pants of {target.user_name} whom is {pants_response}")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- pants command -- {f}")
                    return
            elif command.replace(" ", "").startswith("pointscheck"):
                try:
                    if chatter_document is not None:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You have {chatter_document['user_points']} points", reply_parent_message_id=data.event.message_id)
                    else:
                        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong getting your chatter_document", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - points check command -- {f}")
                    return
            elif command.replace(" ", "").startswith("pointsleader"):
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    users = users_collection.find({})
                    users_sorted = sorted(users, key=lambda user: user['user_points'], reverse=True)
                    response = ""
                    for n, user in enumerate(users_sorted[:5]):
                        response += f"{n+1}: {user['user_name']}/{user['user_points']:,} - "
                    await bot.send_chat_message(id_streamer, id_streamer, response[:-3], reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- command pointsleader -- {f}")
                    return
            elif command.replace(" ", "").startswith("pt"):
                try:
                    if chatter_document['user_discord_id'] == 0:
                        user_discord_id_temp = str(chatter_document['user_id'])[:5] + str(random.randint(10000, 99999))
                        chatter_document.update(user_discord_id=int(user_discord_id_temp))
                        chatter_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"You do not have your discord ID linked to your twitch yet. Will attempt to DM you a special code with instructions to link account", reply_parent_message_id=data.event.message_id)
                        await bot.send_whisper(id_streamer, chatter_id, f"Hola, your special discord link code is: {user_discord_id_temp} . Head to any discord server TheeChodebot runs in and use this command: $link_twitch {user_discord_id_temp} . Thee code will automatically expire and your message will be deleted in discord and a response confirming will appear")
                        return
                    elif str(chatter_document['user_discord_id']).startswith(chatter_id[:5]):
                        await bot.send_chat_message(id_streamer, id_streamer, f"Check your DM's. If not reach out to {data.event.broadcaster_user_name} to figure it out", reply_parent_message_id=data.event.message_id)
                        return
                    chatter_document_discord = await get_discord_document(chatter_document)
                    if chatter_document_discord is None:
                        print(f"{chatter_username}'s discord document is NONE. Something went wrong. ")
                        return
                    if command.lstrip("pt ").startswith("witch"):
                        transfer_value = command.lstrip("pt twitch ")
                        if transfer_value.isdigit():
                            await document_points_transfer("twitch", transfer_value, chatter_document, chatter_document_discord)
                        else:
                            await bot.send_chat_message(id_streamer, id_streamer, f"I couldn't ID thee number you're trying to transfer", reply_parent_message_id=data.event.message_id)
                            print(f"--{transfer_value}--{type(transfer_value)}")
                            return
                    elif command.lstrip("pt ").startswith("discord"):
                        transfer_value = command.lstrip("pt discord ")
                        if transfer_value.isdigit():
                            await document_points_transfer("discord", transfer_value, chatter_document, chatter_document_discord)
                        else:
                            await bot.send_chat_message(id_streamer, id_streamer, f"I couldn't ID thee number you're trying to transfer", reply_parent_message_id=data.event.message_id)
                            print(f"--{transfer_value}--{type(transfer_value)}")
                            return
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message - pt command -- {f}")
                    return
            elif command.replace(" ", "").startswith("pp"):
                try:
                    size = random.randint(-4, 18)
                    await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username}'s packin' a  {f'{size} inch pecker' if size > 0 else f'{size} inch innie'}")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- pp command -- {f}")
                    return
            elif command.replace(" ", "").startswith("tag"):
                try:
                    last_tag_id, last_tag_name = channel_document['cmd_tag_last_it'].split("/")
                    time_since_tagged = datetime.datetime.now() - channel_document['cmd_tag_last_it_time']
                    if chatter_id != last_tag_id and time_since_tagged.seconds < 120:
                        await bot.send_chat_message(id_streamer, id_streamer, f"You are not last tagged, {last_tag_name} is last to be tagged. {abs(time_since_tagged.seconds - 120)} seconds till able to tag.", reply_parent_message_id=data.event.message_id)
                    else:
                        if chatter_id != last_tag_id:
                            try:
                                prior_target_chatter_doc = Users.objects.get(user_id=int(last_tag_id))
                                await twitch_points_transfer(prior_target_chatter_doc, 25, False)
                            except Exception as g:
                                formatted_time = fortime()
                                logger.error(f"{formatted_time}: Error in on_stream_chat_notification -- tag command -- chatter_id != last_tag_id -- {g}")
                                pass
                        target = await select_target(chatter_id)
                        channel_document.update(cmd_tag_last_it=f'{target.user_id}/{target.user_name}', cmd_tag_last_it_time=datetime.datetime.now())
                        channel_document.save()
                        await bot.send_chat_message(id_streamer, id_streamer, f"{chatter_username} tags {target.user_name}.")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- tag command -- {f}")
                    return
            elif command.replace(" ", "").startswith("levelcorrection") and chatter_id == id_streamer:
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    users = users_collection.find({})
                    for user in users:
                        print(f"User: {user['user_id']}/{user['user_name']} - Old: {user['user_xp_points']}/{user['user_level']}")
                        new_user_level = user['user_level']
                        old_user_level = user['user_level']
                        x = 0
                        while True:
                            if user['user_xp_points'] >= level_const * old_user_level:
                                old_user_level = new_user_level
                                new_user_level += 1
                            elif user['user_xp_points'] < level_const * old_user_level:  # > level_const * (old_user_level - 1):  # want to try this later to clean up below
                                if user['user_xp_points'] < level_const * (old_user_level - 1):
                                    new_user_level -= 1
                                    old_user_level = new_user_level
                                else:
                                    break
                            x += 1
                            if x >= 20:
                                print(f"X has reached 20, breaking...\nold-{old_user_level}-new-{new_user_level}-xp-{user['user_xp_points']}")
                                break
                        if x < 20:
                            user.update(user_level=new_user_level)
                            user.save()
                        print(f"User: {user['user_id']}/{user['user_name']} - New: {user['user_xp_points']}/{new_user_level}")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- levelcorrection command -- {f}")
                    return
            elif command.replace(" ", "").startswith("rtag") and chatter_id == id_streamer:
                try:
                    channel_document.update(cmd_tag_last_it=f"{data.event.broadcaster_user_id}/{data.event.broadcaster_user_name}")
                    channel_document.save()
                    await bot.send_chat_message(id_streamer, id_streamer, f"Tag game reset")
                except Exception as f:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error in on_stream_chat_message -- tagreset command -- {f}")
                    return
            elif command.replace(" ", "").startswith("test") and chatter_id == id_streamer:
                try:
                    await bot.send_chat_message(id_streamer, id_streamer, f"{channel_document['user_name']}--{channel_document['channel_online']}--{channel_document['hype_train_current']}", reply_parent_message_id=data.event.message_id)
                except Exception as f:
                    print(f)
        else:
            try:
                await twitch_points_transfer(chatter_document, standard_points if not thee_hype_ehvent_enabled else standard_points * thee_hype_ehvent_mult)
                chat_logger.info(f"{chatter_id}/{chatter_username}: {data.event.message.text if data.event.message_type == 'text' else f'Last message was a type({data.event.message_type}) not a text type.'}")
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message - else - twitch_points? -- {f}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in on_stream_chat_message -- {e}")
        await bot.send_chat_message(id_streamer, id_streamer, f"Something went wrong in thee backend, error logged. Try again later", reply_parent_message_id=data.event.message_id)
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
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.chatter_user_name}{f' is on a {streak} streak, and has been subscribed for a total of' if streak is not None or streak == 0 else 'has been subscribed for a total of'} {data.event.resub.cumulative_months} months.{response_thanks}")
        elif data.event.notice_type == "pay_it_forward":
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.chatter_user_name} is paying forward thee subbie gifted by {data.event.pay_it_forward.gifter_user_name} to {data.event.sub_gift.recipient_user_name}.{response_thanks}")
        elif data.event.notice_type == "bits_badge_tier":
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.chatter_user_name} just unlocked thee {data.event.bits_badge_tier.tier} bitties badge!!{response_thanks}")
        else:
            special_logger.info(f"on_stream_chat_notification -- {data.event.notice_type}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in on_stream_chat_notification -- {e}")
        return


async def on_stream_cheer(data: ChannelCheerEvent):
    try:
        response = "!"
        if data.event.is_anonymous:
            user = "Anonymous"
        else:
            user = data.event.user_name
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = round(standard_points * data.event.bits)
                await twitch_points_transfer(chatter_document, points_to_add)
        if writing_to_clock:
            seconds = round(standard_seconds * data.event.bits)
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            formatted_time_added = datetime.timedelta(seconds=seconds)
            response = f', adding {formatted_time_added} to thee clock!!'
        await bot.send_chat_message(id_streamer, id_streamer, f"{user} has cheered {data.event.bits}{response}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_cheer' -- {e}")
        return


async def on_stream_follow(data: ChannelFollowEvent):
    try:
        # channel_document = await get_channel_document(data)
        # if data.event.user_id not in channel_document['followers_list']:
        chatter_document = await get_chatter_document(data)
        if chatter_document is not None:
            points_to_add = round(standard_seconds * follow_seconds)
            await twitch_points_transfer(chatter_document, points_to_add)
        response = "!"
        if writing_to_clock:
            seconds = round(standard_seconds * follow_seconds)
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            formatted_time_added = datetime.timedelta(seconds=seconds)
            response = f"! {formatted_time_added} to thee clock!!"
        await bot.send_chat_message(id_streamer, id_streamer, f"Welcome {data.event.user_name} to Thee Chodeling's Nest{response}{response_thanks}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_follow' -- {e}")
        return


async def on_stream_hype_begin(data: HypeTrainEvent):
    try:
        global thee_hype_ehvent_enabled
        thee_hype_ehvent_enabled = True
        special_logger.info(f"Thee Hype EhVent {'EN' if thee_hype_ehvent_enabled else 'DIS'}ABLED")
        # ToDo: ADD OBS LOGIC HERE TO ENABLE THEE HYPE EH-VENT (NEW NAME FOR THEE Hype EhVent)
        try:
            ad_schedule = await bot.get_ad_schedule(id_streamer)
            # ad_next = datetime.datetime.now() - ad_schedule.next_ad_at.astimezone()
            ad_next_seconds, now_time_seconds = await get_ad_time(ad_schedule)
            # ad_next = await get_ad_seconds(ad_schedule.next_ad_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:]) - await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
            ad_next = ad_next_seconds - now_time_seconds
            if ad_next <= 300:
                ad_attempt_snooze = await bot.snooze_next_ad(id_streamer)
                # snoozed_ad_next = await get_ad_seconds(ad_attempt_snooze.next_ad_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:]) - await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
                ad_next_seconds, now_time_seconds = await get_ad_time(ad_attempt_snooze)
                await bot.send_chat_message(id_streamer, id_streamer, f"Attempting to snooze ad, hype train start - {ad_attempt_snooze.snooze_count} snooze's remaining. Next ad in: {datetime.timedelta(seconds=abs(ad_next_seconds - now_time_seconds))}")
        except Exception as f:
            formatted_time = fortime()
            logger.error(f"{formatted_time}: ERROR in on_stream_hype_begin -- ad_schedule shit -- {f}")
            pass
        channel_document = await get_channel_document(data)
        if channel_document is None:
            await bot.send_chat_message(id_streamer, id_streamer, f"Error grabbing/creating channel document. Try again later")
            return
        channel_document.update(hype_train_current=True, hype_train_current_level=data.event.level)
        channel_document.save()
        await bot.send_chat_message(id_streamer, id_streamer, f"Choo Choooooooo!! Hype train started by {data.event.last_contribution.user_name}{f', also triggering a Hype EhVent, doubling all twitch contributions to thee clock!!' if writing_to_clock else '!'}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_hype_begin' -- {e}")
        return


async def on_stream_hype_end(data: HypeTrainEndEvent):
    try:
        global thee_hype_ehvent_enabled
        thee_hype_ehvent_enabled = False
        special_logger.info(f"Thee Hype EhVent {'EN' if thee_hype_ehvent_enabled else 'DIS'}ABLED")
        # ToDo: ADD OBS LOGIC HERE TO DISABLE THEE HYPE EH-VENT (NEW NAME FOR THEE Hype EhVent)
        channel_document = await get_channel_document(data)
        if channel_document is None:
            await bot.send_chat_message(id_streamer, id_streamer, f"Error grabbing/creating channel document. Try again later")
            return
        if data.event.level > channel_document['hype_train_record_level']:
            record_beat = True
            new_hype_train_record_level = data.event.level
        else:
            record_beat = False
            new_hype_train_record_level = channel_document['hype_train_record_level']
        formatted_time = fortime()
        channel_document.update(hype_train_last=formatted_time, hype_train_current=False, hype_train_current_level=0, 
                                hype_train_last_level=data.event.level, hype_train_record_level=new_hype_train_record_level)
        channel_document.save()
        await bot.send_chat_message(id_streamer, id_streamer, f"Hype Train Completed @ {data.event.level}!!{f' New local record reached at {new_hype_train_record_level}!!' if record_beat else ''}{f' Thee Hype EhVent is now over, all contributions to thee clock have returned to normal.' if writing_to_clock else ''} Much Love To All <3")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_hype_end' -- {e}")
        return


async def on_stream_hype_progress(data: HypeTrainEvent):
    try:
        try:
            ad_schedule = await bot.get_ad_schedule(id_streamer)
            # ad_next = datetime.datetime.now() - ad_schedule.next_ad_at.astimezone()
            ad_next_seconds, now_time_seconds = await get_ad_time(ad_schedule)
            # ad_next = await get_ad_seconds(ad_schedule.next_ad_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:]) - await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
            ad_next = ad_next_seconds - now_time_seconds
            if ad_next <= 300:
                ad_attempt_snooze = await bot.snooze_next_ad(id_streamer)
                # snoozed_ad_next = await get_ad_seconds(ad_attempt_snooze.next_ad_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:]) - await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
                ad_next_seconds, now_time_seconds = await get_ad_time(ad_attempt_snooze)
                await bot.send_chat_message(id_streamer, id_streamer, f"Attempting to snooze ad, hype train Progress - {ad_attempt_snooze.snooze_count} snooze's remaining. Next ad in: {datetime.timedelta(seconds=abs(ad_next_seconds - now_time_seconds))}")
        except Exception as f:
            formatted_time = fortime()
            logger.error(f"{formatted_time}: ERROR in on_stream_hype_progress -- ad_schedule shit -- {f}")
            pass
        # ToDo: ADD OBS LOGIC HERE TO DO HYPE TRAIN LEVEL INCREASE SHIT
        channel_document = await get_channel_document(data)
        if channel_document is None:
            await bot.send_chat_message(id_streamer, id_streamer, f"Error grabbing/creating channel document. Try again later")
            return
        if data.event.level > channel_document['hype_train_current_level']:
            new_hype_train_current_level = data.event.level
            await bot.send_chat_message(id_streamer, id_streamer, f"New Hype Train Level!! Currently @ {data.event.level}")
        else:
            new_hype_train_current_level = channel_document['hype_train_current_level']
        # if new_hype_train_current_level > channel_document['hype_train_record_level']:
        #     new_hype_train_record_level = data.event.level
        #     await bot.send_chat_message(id_streamer, id_streamer, f"New Hype Train local Record Level!!!!! Record Now @ {data.event.level}")
        # else:
        #     new_hype_train_record_level = channel_document['hype_train_record_level']  # PRETTY SURE I DON'T WANT ALL THIS TILL THEE END OF HYPE TRAIN
        channel_document.update(hype_train_current_level=new_hype_train_current_level)  #, hype_train_record_level=new_hype_train_record_level()
        channel_document.save()
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_hype_progress' -- {e}")
        return


async def on_stream_poll_begin(data: ChannelPollBeginEvent):
    try:
        choices = ""
        for n, choice in enumerate(data.event.choices):
            choices += f"{n+1}: {choice.title} - "
        time_till_end = await get_ad_seconds(data.event.ends_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:])
        seconds_now = await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
        await bot.send_chat_message(id_streamer, id_streamer, f"Poll '{data.event.title}' has started. Choices are: {choices[:-3]}. Poll will end in {datetime.timedelta(seconds=abs(time_till_end - seconds_now))}. Voting with extra channel points is {'enabled' if data.event.channel_points_voting.is_enabled else 'disabled'}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_poll_begin' -- {e}")
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
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_poll_end' -- {e}")
        return


async def on_stream_point_redemption(data: ChannelPointsCustomRewardRedemptionAddEvent):
    try:
        # print(f"ChannelPointsRedemption\nTitle: {data.event.reward.title}\nCost: {data.event.reward.cost}\nPrompt: {data.event.reward.prompt}")
        special_logger.info(f"RewardID: {data.event.reward.id} -- {data.event.reward.title}")
        if data.event.reward.title == "Add 10 Mins" and writing_to_clock:
            # seconds = 600
            seconds = 600 if not thee_hype_ehvent_enabled else 600 * thee_hype_ehvent_mult
            # if thee_hype_ehvent_enabled:
            #     seconds *= thee_hype_ehvent_mult
            seconds_formatted = str(datetime.timedelta(seconds=seconds)).title()
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} added {seconds_formatted} to thee timer with {data.event.reward.cost} {channel_point_name}")
        elif data.event.reward.title == "Add 20 Mins" and writing_to_clock:
            # seconds = 1200
            seconds = 1200 if not thee_hype_ehvent_enabled else 1200 * thee_hype_ehvent_mult
            # if thee_hype_ehvent_enabled:
            #     seconds *= thee_hype_ehvent_mult
            seconds_formatted = str(datetime.timedelta(seconds=seconds)).title()
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} added {seconds_formatted} to thee timer with {data.event.reward.cost} {channel_point_name}")
        elif data.event.reward.title == "Add 30 Mins" and writing_to_clock:
            # seconds = 1800
            seconds = 1800 if not thee_hype_ehvent_enabled else 1800 * thee_hype_ehvent_mult
            # if thee_hype_ehvent_enabled:
            #     seconds *= thee_hype_ehvent_mult
            seconds_formatted = str(datetime.timedelta(seconds=seconds)).title()
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} added {seconds_formatted} to thee timer with {data.event.reward.cost} {channel_point_name}")
        else:
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} used {data.event.reward.cost} {channel_point_name} to redeem {data.event.reward.title}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_point_redemption' -- {e}")
        return


async def on_stream_prediction_begin(data: ChannelPredictionEvent):
    try:
        outcomes = ""
        for n, outcome in enumerate(data.event.outcomes):
            outcomes += f"{n+1}: {outcome.title} - "
        time_till_end = await get_ad_seconds(data.event.locks_at.astimezone().strftime("%y:%m:%d:%H:%M:%S")[1:])
        seconds_now = await get_ad_seconds(datetime.datetime.now().strftime("%y:%m:%d:%H:%M:%S")[1:])
        await bot.send_chat_message(id_streamer, id_streamer, f"Prediction '{data.event.title}' has started. Choices are: {outcomes[:-3]}. Prediction will end in {datetime.timedelta(seconds=time_till_end - seconds_now)}.")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_prediction_begin' -- {e}")
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
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_prediction_end' -- {e}")
        return


async def on_stream_prediction_lock(data: ChannelPredictionEvent):
    try:
        print(data.event.title)
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_prediction_lock' -- {e}")
        return


async def on_stream_subbie(data: ChannelSubscribeEvent):
    try:
        if not data.event.is_gift:
            sub_tier = await get_subbie_tier(data)
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = round(standard_seconds * sub_tier)
                await twitch_points_transfer(chatter_document, points_to_add)
            if writing_to_clock:
                seconds = round(standard_seconds * sub_tier)  # ToDo: FIGURE OUT THIS MATHS SHIT....
                # seconds = int(standard_seconds * sub_tier)  # ToDo: Think This Maths Shit is Figured??? Now to test.... note using round, think it's more fair
                write_clock(seconds, thee_hype_ehvent_enabled, True)
                formatted_time_added = datetime.timedelta(seconds=seconds)
                response = f', adding {formatted_time_added} to thee clock!!'
            else:
                response = '.'
            await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.user_name} subscribed to Thee Nest{response} Much Love, Thank You :)")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_subbie' -- {e}")
        return


async def on_stream_subbie_gift(data: ChannelSubscriptionGiftEvent):
    try:
        response = ""
        sub_tier = await get_subbie_tier(data)
        if data.event.is_anonymous:
            user = "Anonymous"
            user_response = ""
        else:
            user = data.event.user_name
            user_response = f"Giving them a total of {data.event.cumulative_total} gifted subbies."
            chatter_document = await get_chatter_document(data)
            if chatter_document is not None:
                points_to_add = round((standard_seconds * sub_tier) * data.event.total)
                await twitch_points_transfer(chatter_document, points_to_add)
        if writing_to_clock:
            seconds = round((standard_seconds * sub_tier) * data.event.total)
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            formatted_time_added = datetime.timedelta(seconds=seconds)
            response = f" Added {formatted_time_added} to thee clock!!"
        await bot.send_chat_message(id_streamer, id_streamer, f"{user} gifted out {data.event.total} {'subbie' if data.event.total == 1 else 'subbies'} to Thee Chodelings. {user_response}  Thank You :) Much Love <3{response}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_subbie_gift' -- {e}")
        return


async def on_stream_raid_in(data: ChannelRaidEvent):
    try:
        response = "!!!"
        if writing_to_clock:
            seconds = round(raid_seconds * data.event.viewers)
            write_clock(seconds, thee_hype_ehvent_enabled, True)
            formatted_time_added = datetime.timedelta(seconds=seconds)
            response = f" adding {formatted_time_added} to thee clock!!!"
        await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.from_broadcaster_user_name} raid with {data.event.viewers} incoming{response} Go show them some love back y'all")
        await bot.send_a_shoutout(id_streamer, data.event.from_broadcaster_user_id, id_streamer)
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_raid_in' -- {e}")
        return


async def on_stream_raid_out(data: ChannelRaidEvent):
    try:
        await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.from_broadcaster_user_name} has sent thee raid with {data.event.viewers} to https://twitch.tv/{data.event.to_broadcaster_user_name}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_raid_out' -- {e}")
        return


async def on_stream_update(data: ChannelUpdateEvent):
    try:
        channel_document = await get_channel_document(data)
        if channel_document is None:
            formatted_time = fortime()
            logger.error(f"{formatted_time}: ERROR: Channel Document is NONE!!! -- in on_stream_update")
            return
        if data.event.title != channel_document['channel_title'] or data.event.category_id != channel_document['channel_game_id']:
            response = []
            title_new, game_id_new, game_name_new = channel_document['channel_title'], channel_document['channel_game_id'], channel_document['channel_game_name']
            if channel_document['channel_title'] != data.event.title:
                response.append(f"Title Change to {data.event.title}")
                title_new = data.event.title
            if channel_document['channel_game_id'] != data.event.category_id:
                response.append(f"Category Change to {data.event.category_name}")
                game_id_new = data.event.category_id
                game_name_new = data.event.category_name
            channel_document.update(channel_title=title_new, channel_game_id=game_id_new, channel_game_name=game_name_new)
            channel_document.save()
            await bot.send_chat_message(id_streamer, id_streamer, f"Channel Update: {' -- '.join(response)}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_update' -- {e}")
        return


async def on_stream_start(data: StreamOnlineEvent):
    try:
        channel_document = await get_channel_document(data)
        if channel_document is not None:
            channel_info = await bot.get_channel_information(id_streamer)
            channel_document.update(channel_online=True, channel_title=channel_info[0].title, channel_game_id=channel_info[0].game_id,
                                    channel_game_name=channel_info[0].game_name, channel_content_class=channel_info[0].content_classification_labels,
                                    channel_tags=channel_info[0].tags, channel_branded=channel_info[0].is_branded_content, hype_train_current=False, hype_train_current_level=0)
            channel_document.save()
        await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name} is now online! Gather one, gather all.")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_start' -- {e}")
        return


async def on_stream_end(data: StreamOfflineEvent):
    try:
        channel_document = await get_channel_document(data)
        if channel_document is not None:
            # channel_info = await bot.get_channel_information(id_streamer)
            channel_document.update(channel_online=False)
            channel_document.save()
        await bot.send_chat_message(id_streamer, id_streamer, f"{data.event.broadcaster_user_name} has faded into thee shadows. Much Love All")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_end' -- {e}")
        return


async def run():
    global thee_hype_ehvent_enabled, writing_to_clock, level_const
    twitch_helper = UserAuthenticationStorageHelper(bot, target_scopes)
    await twitch_helper.bind()

    user = await first(bot.get_users(user_ids=id_streamer))  # Don't think I need this, however, I feel more comfortable knowing 100% it's grabbing my account, and not some random somehow by mistake...

    event_sub = EventSubWebsocket(bot)
    event_sub.start()

    # follower_list = []
    # for x in range(99):
    #     follower_list.append(await bot.get_channel_followers(id_streamer, ))

    await event_sub.listen_channel_ad_break_begin(user.id, on_stream_ad_start)
    # await event_sub.listen_extension_bits_transaction_create(id_streamer, on_stream_bits_ext_transfer)  # WebHooks Needed For This
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

    while True:  # Bot's Loop
        async def shutdown():
            try:
                print("Shutting down twitch bot processes. Stand By")
                await asyncio.sleep(1)
                await event_sub.stop()
                await asyncio.sleep(1)
                # chat_bot.stop()
                await asyncio.sleep(1)
                await bot.close()
                await asyncio.sleep(1)
                await disconnect_mongo()
                await asyncio.sleep(1)
                print("Twitch bot processes shut down successfully")
            except Exception as e:
                print(f"Error in shutdown() -- {e}")
                pass

        try:
            options = ["Enter 1 to configure timer",
                       "Enter 2 to get current time left",
                       "Enter 3 to add/subtract time",
                       "Enter 0 to Halt Bot"]
            one_options = ["Enter 1 to Enable/Disable Writing to Clock",
                           "Enter 2 to Enable/Disable Thee Hype EhVent",
                           "Enter 3 to Change Current time left",
                           "Enter 4 to Change Max Time",
                           "Enter 5 to Change Total Time",
                           "Enter 6 to Change Level Const",
                           "Enter 0 To Go Up"]
            user_input = input(f"\n".join(options) + "\n")
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await shutdown()
                    break
                elif user_input == 1:
                    while True:
                        user_input = input(f"\n".join(one_options) + "\n")
                        if not user_input.isdigit():
                            print(f"Must enter just a number")
                        else:
                            user_input = int(user_input)
                            if user_input == 0:
                                print(f"Returning to Bot's Main Loop")
                                break
                            elif user_input == 1:
                                if writing_to_clock:
                                    writing_to_clock = False
                                else:
                                    writing_to_clock = True
                                # try:  # ToDo: FIGURE OUT WHY THIS TELLS ME REWARD ID IS FOR ANOTHER CHANNEL OR MY CHANNEL DOESN'T HAVE REWARDS ENABLED.....
                                #     for reward_id in marathon_rewards:
                                #         await bot.update_custom_reward(user.id, reward_id, is_enabled=writing_to_clock)
                                #         special_logger.info(f"{reward_id} is now {'EN' if writing_to_clock else 'DIS'}ABLED")
                                # except Exception as f:
                                #     logger.error(f"Error switching rewards on/off for writing_to_clock -- bot loop -- {f}")
                                #     pass
                                print(f"Writing to clock is now {'EN' if writing_to_clock else 'DIS'}ABLED")
                            elif user_input == 2:
                                if thee_hype_ehvent_enabled:
                                    thee_hype_ehvent_enabled = False
                                else:
                                    thee_hype_ehvent_enabled = True
                                print(f"Thee Hype EhVent is now {'EN' if thee_hype_ehvent_enabled else 'DIS'}ABLED")
                            elif user_input == 3:
                                reset_current_time()
                            elif user_input == 4:
                                reset_max_time()
                            elif user_input == 5:
                                reset_total_time()
                            elif user_input == 6:
                                level_const = reset_level_const(level_const)
                elif user_input == 2:
                    print(read_clock())
                elif user_input == 3:
                    number, add = loop_get_user_input_clock()
                    if number.isdigit():
                        write_clock(int(number), False, add)
                    else:
                        print(f"Invalid Input -- You put '{number}' - If None, see error logs - which is a {type(number)} -- USE NUMPAD +/-!!")
                else:
                    print(f"Invalid Input -- You put '{user_input}'")
            else:
                print(f"Invalid Input -- You put '{user_input}' which is a {type(user_input)}")
        except KeyboardInterrupt:
                await shutdown()
                break
        except Exception as e:
            formatted_time = fortime()
            logger.error(f"{formatted_time}: Error in BOT Loop -- {e}")
            try:
                continue
            except Exception as grrrr:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: ERROR TRYING TO CONTINUE UPON LAST ERROR -- {grrrr} -- ATTEMPTING TO HALT BOT")
                await shutdown()
                break


def fortime():
    try:
        nowtime = datetime.datetime.now()
        formatted_time = nowtime.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_time
    except Exception as e:
        logger.error(f"Error creating formatted_time -- {e}")
        return None


def setup_logger(name, log_file, level=logging.INFO):
    try:
        if name == "chat_logger":
            handler = logging.FileHandler(f"{logs_directory}{log_file}", mode="w", encoding="utf-8")
        else:
            handler = logging.FileHandler(f"{logs_directory}{log_file}")
        console_handler = logging.StreamHandler()
        local_logger = logging.getLogger(name)
        local_logger.setLevel(level)
        local_logger.addHandler(handler)
        if name == "logger":
            local_logger.addHandler(console_handler)
        return local_logger
    except Exception as e:
        formatted_time = fortime()
        print(f"{formatted_time}: ERROR in setup_logger - {name}/{log_file}/{level} -- {e}")
        return None


def loop_get_user_input_clock():
    try:
        while True:
            number = input(f"Enter +/-number to add/subtract\n")
            if number.startswith("+"):
                add = True
                break
            elif number.startswith("-"):
                add = False
                break
            else:
                print(f"Invalid Input -- You put '{number}'")
        number = number.lstrip("-").lstrip("+")
        return number, add
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in get_user_input_clock -- {e}")
        return None, None


def connect_mongo(db, alias):
    try:
        client = connect(db=db, host=mongo_login_string, alias=alias)
        formatted_time = fortime()
        logger.info(f"{formatted_time}: MongoDB Connected\n{long_dashes}")
        time.sleep(1)
        client.get_default_database(db)
        formatted_time = fortime()
        logger.info(f"{formatted_time}: Database Loaded\n{long_dashes}")
        return client
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error Connecting MongoDB -- {e}")
        return None


async def disconnect_mongo():
    try:
        disconnect_all()
        logger.info(f"{long_dashes}\nDisconnected from MongoDB\n{long_dashes}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error Disconnection MongoDB -- {e}")
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
            new_twitch_points = chatter_document['user_points'] + transfer_value
            chatter_document.update(user_points=new_twitch_points)
            chatter_document.save()
            # await bot.send_chat_message(id_streamer, id_streamer, f"Transferred {transfer_value} to your twitch profile.")
        elif direction == "discord":
            if transfer_value > chatter_document['user_points']:
                await bot.send_chat_message(id_streamer, id_streamer, f"You do not have enough twitch points to transfer. You have {chatter_document['user_points']} points")
                return
            new_discord_points = chatter_document_discord['points_value'] + transfer_value
            chatter_document_discord.update(points_value=new_discord_points)
            chatter_document_discord.save()
            new_twitch_points = chatter_document['user_points'] - transfer_value
            chatter_document.update(user_points=new_twitch_points)
            chatter_document.save()
            # await bot.send_chat_message(id_streamer, id_streamer, f"Transferred {transfer_value} to your discord profile.")
        else:
            await bot.send_chat_message(id_streamer, id_streamer, f"Backend Mess up.... {direction} is thee direction")
            return
        await bot.send_chat_message(id_streamer, id_streamer, f"Transferred {transfer_value} to your {direction} profile.")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in points_transfer -- {chatter_document['user_id']}/{chatter_document['user_name']}/{chatter_document['user_login']}/{chatter_document['user_discord_id']} -- {chatter_document_discord['author_id']}/{chatter_document_discord['author_name']}/{chatter_document_discord['guild_name']}/{chatter_document_discord['twitch_id']} -- {e}")
        return


async def get_channel_document(data):
    try:
        broadcaster_id = int(data.event.broadcaster_user_id)
        try:
            channel_document = Channels.objects.get(user_id=broadcaster_id)
        except Exception as f:
            if FileNotFoundError:
                try:
                    channel_collection = twitch_database.twitch.get_collection('channels')
                    new_channel_document = Channels(user_id=broadcaster_id, user_name=data.event.broadcaster_user_name,
                                                    user_login=data.event.broadcaster_user_login)
                    new_channel_document_dict = new_channel_document.to_mongo()
                    channel_collection.insert_one(new_channel_document_dict)
                    channel_document = Channels.objects.get(user_id=data.event.broadcaster_user_id)
                    pass
                except Exception as g:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error creating new document for channel -- {data.event.broadcaster_user_id}/{data.event.broadcaster_user_name}/{data.event.broadcaster_user_login} -- {g}")
                    return None
            else:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error fetching/creating channel document -- {data.event.broadcaster_user_id}/{data.event.broadcaster_user_name}/{data.event.broadcaster_user_login} -- {f}")
                return None
        return channel_document
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in get_channel_document -- Data Type -- {type(data)} -- {e}")
        return None


async def get_chatter_document(data):
    try:
        if type(data) in (ChannelChatMessageEvent, ChannelChatNotificationEvent):
            chatter_id = int(data.event.chatter_user_id)
            chatter_name = data.event.chatter_user_name
            chatter_login = data.event.chatter_user_login
        else:  #if type(data) in (ChannelSubscribeEvent, ChannelSubscriptionGiftEvent, ChannelCheerEvent, ChannelFollowEvent):
            chatter_id = int(data.event.user_id)
            chatter_name = data.event.user_name
            chatter_login = data.event.user_login
        try:
            chatter_document = Users.objects.get(user_id=chatter_id)
        except Exception as f:
            if FileNotFoundError:
                try:
                    users_collection = twitch_database.twitch.get_collection('users')
                    formatted_time = fortime()
                    new_chatter_document = Users(user_id=chatter_id, user_name=chatter_name, user_login=chatter_login,
                                                 first_chat_date=formatted_time)
                    new_chatter_document_dict = new_chatter_document.to_mongo()
                    users_collection.insert_one(new_chatter_document_dict)
                    chatter_document = Users.objects.get(user_id=chatter_id)
                    pass
                except Exception as g:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error creating new document for user -- {chatter_id}/{chatter_name}/{chatter_login}\n{g}")
                    return None
            else:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error reading/creating new document for user -- {chatter_id}/{chatter_name}/{chatter_login}\n{f}")
                return None
        return chatter_document
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in get_chatter_document -- Data Type -- {type(data)} -- {e}")
        return None


async def get_discord_document(chatter_document):
    try:
        discord_economy_collection = discord_database.channel_ids.get_collection('economy_data')
        if discord_economy_collection.find_one({"_id": chatter_document['user_discord_id']}):
            chatter_document_discord = EconomyData.objects.get(author_id=chatter_document['user_discord_id'])
            return chatter_document_discord
        else:
            await bot.send_chat_message(id_streamer, id_streamer, f"You do not have a document in a discord server TheeChodebot is in as well.")
            return None
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in get_discord_document -- {chatter_document['user_id']}/{chatter_document['user_name']}/{chatter_document['user_login']}/{chatter_document['user_discord_id']} -- {e}")
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
            formatted_time = fortime()
            logger.error(f"{formatted_time}: Error retrieving subbie tier -- {data.event.tier}")
            return 0
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in get_subbie_tier -- {e}")
        return 0


async def twitch_points_transfer(chatter_document, value: int, add: bool = True):
    try:
        if chatter_document is not None:
            # formatted_time = fortime()
            last_chatted = datetime.datetime.now()
            # print(last_chatted, type(last_chatted))
            new_user_level = chatter_document['user_level']
            if add:
                new_user_xp_points = chatter_document['user_xp_points'] + value / 2
                new_user_points = chatter_document['user_points'] + value
                if new_user_xp_points >= level_const * chatter_document['user_level']:
                    new_user_level = chatter_document['user_level'] + 1
            else:
                new_user_xp_points = chatter_document['user_xp_points'] - value
                new_user_points = chatter_document['user_points'] - value
                if new_user_xp_points < level_const * chatter_document['user_level'] and chatter_document['user_level'] > 1:
                    new_user_level = chatter_document['user_level'] - 1
            chatter_document.update(user_level=new_user_level, user_xp_points=new_user_xp_points, user_points=new_user_points, latest_chat_date=last_chatted)
            chatter_document.save()
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in twitch_points_transfer -- {chatter_document['user_id']}/{chatter_document['user_name']}/{chatter_document['user_login']} -- {e}")
        return


async def select_target(chatter_id):
    users = await bot.get_chatters(id_streamer, id_streamer)
    users_collection = twitch_database.twitch.get_collection('users')
    users_documents = users_collection.find({})
    valid_users = []
    for user in users_documents:
        valid_users.append(str(user['_id']))
    while True:
        target = random.choice(users.data)
        if target.user_id in valid_users and target.user_id not in lurk_ignore_list:
            if chatter_id == target.user_id and users.total - len(ignore_list) - len(lurk_ignore_list) > 1:
                pass
            else:
                break
    return target


if __name__ == "__main__":
    logger = setup_logger('logger', 'log.log')
    chat_logger = setup_logger('chat_logger', 'chat_log.log')
    gamble_logger = setup_logger('gamble_logger', 'gamble_log.log')
    special_logger = setup_logger('special_logger', 'special_log.log', logging.WARN)

    if None in (logger, chat_logger, gamble_logger, special_logger):
        print(f"One of thee loggers isn't setup right -- {logger}/{chat_logger}/{gamble_logger}/{special_logger} -- Quitting program")
        quit()

    # Main Loop
    while True:
        #  asyncio.create_task(countdown())  # Think about this?? Might allow for bot to execute countdown??
        try:
            options = ["Enter 1 to start twitch bot",
                       "Enter 3 to +/- time",
                       "Enter 0 to Exit Program"]
            user_input = input("\n".join(options) + "\n")
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
                        discord_database = connect_mongo(mongo_discord_collection, "Discord_Database")
                        time.sleep(1)
                        if None in (twitch_database, discord_database):
                            asyncio.run(disconnect_mongo())
                            formatted_time = fortime()
                            logger.error(f"{formatted_time}: Error connecting one of thee databases -- {twitch_database}/{discord_database} -- Quitting program")
                            break
                    except Exception as f:
                        formatted_time = fortime()
                        logger.error(f"{formatted_time}: Error Loading Database(s) -- {f}")
                        break
                    asyncio.run(run())
                elif user_input == 2:
                    print("Logic Not Coded")
                    # try:  # ToDo: Figure this shit out, so I can run thee .py file from within ChodeBot....  # PROBABLY WILL NEVER USE BUTT JUST IN CASE
                    #     def join_path(relative_path: str):
                    #         try:
                    #             print(os.path.join("py ", countdown_path, relative_path))
                    #             return os.path.join("py ", countdown_path, relative_path)
                    #         except Exception as wtf:
                    #             print(wtf)
                    #
                    #
                    #     # subprocess.Popen(join_path("countdown.py"), shell=True)
                    #     subprocess.run(join_path("countdown.py"), shell=True)
                    # except Exception as grr:
                    #     print(grr)
                    #     continue
                elif user_input == 3:
                    while True:
                        number, add = loop_get_user_input_clock()
                        if number.isdigit():
                            write_clock(int(number), False, add)
                            break
                        else:
                            print(f"Invalid Input -- You put '{number}' - If None, see error logs -  which is a {type(number)} -- USE NUMPAD +/-!!")
                # elif user_input == 4:  # PROBABLY NEVER USE BUTT JUST IN CASE
                #     threading.Thread(target=CountDown().start()).run()
                #     clock_thread = threading.Thread(target=CountDown().start()).run()
                # elif user_input == 5:
                #     CountDown().stop()
                #     # clock_thread.
                else:
                    print(f"Invalid Input -- You Entered '{user_input}'")
            else:
                print(f"Invalid Input -- You entered '{user_input}' and it's type is a {type(user_input)}")
        except KeyboardInterrupt:
            print(f"Exiting Program")
            break
        except Exception as e:
            formatted_time = fortime()
            logger.error(f"{formatted_time}: Error in MAIN loop -- {e} - Exiting Program")
            asyncio.run(disconnect_mongo())
            exit()
