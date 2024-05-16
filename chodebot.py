import os
import sys
import time
import asyncio
import logging
import datetime
from pathlib import Path
from mondocs import Users, EconomyData
from dotenv import load_dotenv
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from pyprobs import Probability as pr
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.oauth import UserAuthenticationStorageHelper
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME
from twitchAPI.object.eventsub import ChannelChatMessageEvent, ChannelFollowEvent, StreamOnlineEvent, \
    StreamOfflineEvent, ChannelAdBreakBeginEvent, ChannelCheerEvent, ChannelPointsCustomRewardRedemptionAddEvent, \
    ChannelPollBeginEvent, ChannelPollEndEvent, ChannelRaidEvent, ChannelSubscribeEvent, ChannelSubscriptionGiftEvent

load_dotenv()
id_twitch_client = os.getenv("client")
id_twitch_secret = os.getenv("secret")
id_theechody_account = os.getenv("theechody")
id_theechodebot_account = os.getenv("theechodebot")
mongo_login_string = os.getenv("monlog_string")
mongo_twitch_collection = os.getenv("montwi_string")
mongo_discord_collection = os.getenv("mondis_string")
long_dashes = "-------------------------------------------------"
target_scopes = [AuthScope.BITS_READ,
                 AuthScope.USER_READ_CHAT,
                 AuthScope.USER_WRITE_CHAT,
                 AuthScope.CHANNEL_MODERATE,
                 AuthScope.CHANNEL_READ_ADS,
                 AuthScope.CHANNEL_MANAGE_POLLS,
                 AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
                 AuthScope.MODERATOR_READ_FOLLOWERS,
                 AuthScope.MODERATOR_MANAGE_SHOUTOUTS,
                 AuthScope.CHANNEL_SUBSCRIPTIONS,
                 AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
                 AuthScope.MODERATOR_READ_CHATTERS]
twitch_bot = Twitch(id_twitch_client, id_twitch_secret)

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

data_directory = f"{application_path}\\data\\"
logs_directory = f"{application_path}\\logs\\"
chat_log = f"{logs_directory}chat_log.log"
Path(data_directory).mkdir(parents=True, exist_ok=True)
Path(logs_directory).mkdir(parents=True, exist_ok=True)


async def points_transfer(direction, transfer_value, chatter_document, chatter_document_discord):
    transfer_value = int(transfer_value)
    if direction == "twitch":
        if transfer_value > chatter_document_discord['points_value']:
            await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"You do not have enough discord points to transfer. You have {chatter_document_discord['points_value']} points")
            return
        new_discord_points = chatter_document_discord['points_value'] - transfer_value
        chatter_document_discord.update(points_value=new_discord_points)
        chatter_document_discord.save()
        new_twitch_points = chatter_document['user_points'] + transfer_value
        chatter_document.update(user_points=new_twitch_points)
        chatter_document.save()
        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Transferred {transfer_value} to your twitch profile.")
    elif direction == "discord":
        if transfer_value > chatter_document['user_points']:
            await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"You do not have enough discord points to transfer. You have {chatter_document['user_points']} points")
            return
        new_discord_points = chatter_document_discord['points_value'] + transfer_value
        chatter_document_discord.update(points_value=new_discord_points)
        chatter_document_discord.save()
        new_twitch_points = chatter_document['user_points'] - transfer_value
        chatter_document.update(user_points=new_twitch_points)
        chatter_document.save()
        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Transferred {transfer_value} to your discord profile.")
    else:
        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Backend Mess up.... {direction} is thee direction")
        return


def twitch_points_transfer(chatter_document, value: int, add: bool = True):
    if add:
        new_user_points = chatter_document['user_points'] + value
    else:
        new_user_points = chatter_document['user_points'] - value
    chatter_document.update(user_points=new_user_points)
    chatter_document.save()


async def on_stream_start(data: StreamOnlineEvent):
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{data.event.broadcaster_user_name} is now online! Gather one, gather all.")


async def on_stream_ad_start(data: ChannelAdBreakBeginEvent):
    if data.event.is_automatic:
        auto_response = f"This is a automatically scheduled ad break"
    else:
        auto_response = f"This is a manually ran ad to attempt to time things better"
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Incoming ad break\n{auto_response} and should only last {data.event.duration_seconds} seconds.")


async def on_stream_message(data: ChannelChatMessageEvent):  # ToDo: Add .startswith for cheer, to multiply points added later on
    try:
        if data.event.chatter_user_id == id_theechody_account:
            return
        message_add_points = 10
        chatter_username = data.event.chatter_user_name
        chatter_document = await get_chatter_document(data)
        if chatter_document is None:
            logger.error(f"Chatter Document is None!! -- {data.event.chatter_user_id}/{data.event.chatter_user_name}/{data.event.chatter_user_login}")
            pass
        if data.event.message.text in ("!lastcomment", "!last comment", "!lastmessage", "!last message"):
            last_message = None
            try:
                with open(chat_log, "r") as file:
                    chat_logs = file.read()
                chat_logs = list(map(str, chat_logs.splitlines()))
                for last in reversed(chat_logs):
                    if last.startswith(data.event.chatter_user_id):
                        last_message = last.lstrip(f"{data.event.chatter_user_id}: ")
                        break
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error fetching last message -- {f}")
                return
            await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"@TheeChody!!!! {chatter_username}'s last message was:\n{last_message if not None else 'Not Found!!!'}")
            return
        elif data.event.message.text.startswith("!pt"):
            try:
                if chatter_document['user_discord_id'] == 0:
                    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{chatter_username} you do not have your discord ID linked to your twitch yet")
                    return
                chatter_document_discord = await get_discord_document(chatter_document)
                if chatter_document_discord is None:
                    return
                if data.event.message.text.lstrip("!pt ").startswith("witch"):
                    transfer_value = data.event.message.text.lstrip("!pt twitch ")
                    if transfer_value.isdigit():
                        await points_transfer("twitch", transfer_value, chatter_document, chatter_document_discord)
                    else:
                        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"I couldn't ID thee number you're betting with")
                        print(f"--{transfer_value}--{type(transfer_value)}")
                        return
                elif data.event.message.text.lstrip("!pt ").startswith("discord"):
                    transfer_value = data.event.message.text.lstrip("!pt discord ")
                    if transfer_value.isdigit():
                        await points_transfer("discord", transfer_value, chatter_document, chatter_document_discord)
                    else:
                        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"I couldn't ID thee number you're betting with")
                        print(f"--{transfer_value}--{type(transfer_value)}")
                        return
            except Exception as f:
                print(f"ERROR IN !pt -- {f}")
        elif data.event.message.text.startswith("!gamble"):
            try:
                bet_value = data.event.message.text.lstrip("!gamble ")
                if bet_value.isdigit():
                    bet_value = int(bet_value)
                else:
                    print(f"--{bet_value}")
                    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{chatter_username} your command should resemble '!gamble 100' where 100, put your bet value. Try again")
                    return
                print(f"{bet_value} vs {chatter_document['user_points']}")
                if bet_value > chatter_document['user_points']:
                    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{chatter_username} you do not have enough points to bet that. You currently have {chatter_document['user_points']}")
                    return
                elif bet_value <= chatter_document['user_points']:
                    if pr.prob(97.5/100):
                        response = f"lost {bet_value}"
                        new_points_value = chatter_document['user_points'] - bet_value
                        twitch_points_transfer(chatter_document, bet_value, False)
                        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{chatter_username} you lost thee gamble, I ate your points. They tasted yummy! You now have {new_points_value} points.")
                    else:
                        won_amount = bet_value * 10000
                        response = f"won {won_amount} with a bet of {bet_value}"
                        new_points_value = chatter_document['user_points'] + won_amount
                        twitch_points_transfer(chatter_document, won_amount)
                        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{chatter_username} you won {won_amount} making your new total {new_points_value}!! Congratz!!!")
                    formatted_time = fortime()
                    gamble_logger.info(f"{formatted_time}: {chatter_username}/{data.event.chatter_user_id} gambled and {response}.")
            except Exception as f:
                formatted_time = fortime()
                gamble_logger.error(f"{formatted_time}: Error in gamble command -- {f}")
                await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{chatter_username} something wen't wrong, TheeChody will fix it sooner than later. Error logged in thee background")
                return
        else:
            twitch_points_transfer(chatter_document, message_add_points)
            chat_logger.info(f"{data.event.chatter_user_id}: {data.event.message.text if data.event.message_type == 'text' else 'not a text message'}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in on_stream_message -- {e}")
        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Something went wrong in thee backend, error logged. Try again later")
        return


async def on_stream_follow(data: ChannelFollowEvent):
    print(f"raw data:\n{data.event.user_id}\n{data.event.user_name}\n{data.event.broadcaster_user_id}\n{data.event.broadcaster_user_name}")
    print(f"data types:\n{type(data.event.user_id)}\n{type(data.event.user_name)}\n{type(data.event.broadcaster_user_id)}\n{type(data.event.broadcaster_user_name)}")
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Welcome in {data.event.user_name} to Thee Chodeling's Nest!")


async def on_stream_channel_point_redemption(data: ChannelPointsCustomRewardRedemptionAddEvent):
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{data.event.user_name} used {data.event.reward.cost} Theebucks to redeem {data.event.reward.title}")


async def on_stream_poll_start(data: ChannelPollBeginEvent):
    choices = ""
    for n, choice in enumerate(data.event.choices):
        choices += f"{n+1}: {choice.title} - "
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Poll '{data.event.title}' has started. Choices are: {choices[:-3]}. Poll will end at {data.event.ends_at.astimezone().strftime('%H:%M:%S')} MST. Voting with extra channel points is {'enabled' if data.event.channel_points_voting.is_enabled else 'disabled'}")


async def on_stream_poll_end(data: ChannelPollEndEvent):
    if data.event.status == "archived":
        pass
    else:
        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"Poll '{data.event.title}' has ended with status: {data.event.status}.")


async def on_stream_subbie(data: ChannelSubscribeEvent):
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{data.event.user_name} subscribed to Thee Nest.\nMuch Love, Thank You :)")


async def on_stream_subbie_gift(data: ChannelSubscriptionGiftEvent):
    if data.event.is_anonymous:
        user = "Anonymous"
        response = f"Thank You :) Much Love <3"
    else:
        user = data.event.user_name
        response = f"Giving them a total of {data.event.cumulative_total} gifted subbies. Thank You :) Much Love <3"
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{user} gifted out {data.event.total} to Thee Chodelings. {response}")


async def on_stream_cheer(data: ChannelCheerEvent):
    if data.event.is_anonymous:
        user = "Anonymous"
    else:
        user = data.event.user_name
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{user} has cheered {data.event.bits}")


async def on_stream_raid_in(data: ChannelRaidEvent):
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{data.event.from_broadcaster_user_name} raid with {data.event.viewers} incoming!!!\nGo show them some love back y'all")
    # if data.event.viewers > 1:
    await twitch_bot.send_a_shoutout(id_theechody_account, data.event.from_broadcaster_user_id, id_theechody_account)


async def on_stream_raid_out(data: ChannelRaidEvent):
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{data.event.from_broadcaster_user_name} has sent thee raid with {data.event.viewers} to https://twitch.tv/{data.event.to_broadcaster_user_name}")


async def on_stream_end(data: StreamOfflineEvent):
    await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"{data.event.broadcaster_user_name} has faded into thee shadows. Much Love All")


async def run():
    twitch_helper = UserAuthenticationStorageHelper(twitch_bot, target_scopes)
    await twitch_helper.bind()

    user = await first(twitch_bot.get_users())

    event_sub = EventSubWebsocket(twitch_bot)
    event_sub.start()

    # await event_sub.listen_extension_bits_transaction_create()
    await event_sub.listen_stream_online(id_theechody_account, on_stream_start)
    await event_sub.listen_channel_ad_break_begin(id_theechody_account, on_stream_ad_start)
    await event_sub.listen_channel_follow_v2(id_theechody_account, user.id, on_stream_follow)
    await event_sub.listen_channel_chat_message(id_theechody_account, user.id, on_stream_message)
    await event_sub.listen_channel_points_custom_reward_redemption_add(id_theechody_account, on_stream_channel_point_redemption)
    await event_sub.listen_channel_poll_begin(id_theechody_account, on_stream_poll_start)
    await event_sub.listen_channel_poll_end(id_theechody_account, on_stream_poll_end)
    await event_sub.listen_channel_subscribe(id_theechody_account, on_stream_subbie)
    await event_sub.listen_channel_subscription_gift(id_theechody_account, on_stream_subbie_gift)
    await event_sub.listen_channel_cheer(id_theechody_account, on_stream_cheer)
    await event_sub.listen_channel_raid(on_stream_raid_in, to_broadcaster_user_id=id_theechody_account)
    await event_sub.listen_channel_raid(on_stream_raid_out, from_broadcaster_user_id=id_theechody_account)
    await event_sub.listen_stream_offline(id_theechody_account, on_stream_end)

    while True:
        async def shutdown():
            try:
                print("Shutting down processes. Stand By")
                await event_sub.stop()
                await twitch_bot.close()
                await disconnect_mongo()
                print("Processes shut down successfully")
            except Exception as e:
                print(f"Error in shutdown() -- {e}")
                pass

        try:
            user_input = input("Enter 1 to Start Timer\nEnter 2 to Stop Timer\nEnter 0 to Exit Program\n")
            if user_input.isdigit():
                user_input = int(user_input)
            if user_input in (1, 2):
                print("Values 1 & 2 Not Programmed Yet")
            elif user_input == 0:
                await shutdown()
                break
            else:
                print(f"{user_input} is not valid")
        except Exception as e:
            if KeyboardInterrupt:
                await shutdown()
                break
            else:
                print(f"Error in while loop -- {e}")
                pass


def fortime():
    try:
        nowtime = datetime.datetime.now()
        formatted_time = nowtime.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_time
    except Exception as e:
        logger.error(f"Error creating formatted_time -- {e}")
        return None


def connect_mongo(db, alias):
    try:
        client = connect(db=db, host=mongo_login_string, alias=alias)
        formatted_time = fortime()
        logger.info(f"{long_dashes}\n{formatted_time}: MongoDB Connected")
        time.sleep(1)
        client.get_default_database(db)
        formatted_time = fortime()
        logger.info(f"{long_dashes}\n{formatted_time}: Database Loaded")
        return client
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error Connecting MongoDB -- {e}")
        return None


async def disconnect_mongo():
    try:
        disconnect_all()
        logger.info(f"{long_dashes}\nDisconnected from MongoDB")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error Disconnection MongoDB -- {e}")
        return


def connect_database(client, database):
    client.get_database(database)
    formatted_time = fortime()
    logger.info(f"{long_dashes}\n{formatted_time}: Database {database} loaded")
    return client


async def get_chatter_document(data):
    users_collection = twitch_database.twitch.get_collection('users')
    try:
        chatter_document = Users.objects.get(user_id=data.event.chatter_user_id)
    except Exception as e:
        if FileNotFoundError:
            try:
                formatted_time = fortime()
                new_chatter_document = Users(user_id=data.event.chatter_user_id, user_name=data.event.chatter_user_name,
                                             user_login=data.event.chatter_user_login, first_chat_date=formatted_time)
                new_chatter_document_dict = new_chatter_document.to_mongo()
                users_collection.insert_one(new_chatter_document_dict)
                chatter_document = Users.objects.get(user_id=data.event.chatter_user_id)
                pass
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error creating new document for user -- {data.event.chatter_user_name} - {data.event.chatter_user_id}\n{f}")
                return None
        else:
            formatted_time = fortime()
            logger.error(f"{formatted_time}: Error reading/creating new document for user -- {data.event.chatter_user_name} - {data.event.chatter_user_id}\n{e}")
            return None
    return chatter_document


async def get_discord_document(chatter_document):
    discord_economy_collection = discord_database.channel_ids.get_collection('economy_data')
    if discord_economy_collection.find_one({"_id": chatter_document['user_discord_id']}):
        chatter_document_discord = EconomyData.objects.get(author_id=chatter_document['user_discord_id'])
        return chatter_document_discord
    else:
        await twitch_bot.send_chat_message(id_theechody_account, id_theechody_account, f"You do not have a document in a server TheeChodebot is in as well.")
        return None


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(f"{logs_directory}{log_file}")
    console_handler = logging.StreamHandler()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)
    return logger


logger = setup_logger('logger', 'log.log')
chat_logger = setup_logger('chat_logger', 'chat_log.log')
gamble_logger = setup_logger('gamble_logger', 'gamble_log.log')

try:
    twitch_database = connect_mongo(mongo_twitch_collection, DEFAULT_CONNECTION_NAME)
    time.sleep(1)
    discord_database = connect_mongo(mongo_discord_collection, "Discord_Database")
    time.sleep(1)
except Exception as e:
    formatted_time = fortime()
    logger.error(f"{formatted_time}: Error Loading Twitch Database -- {e}")
    pass

asyncio.run(run())
