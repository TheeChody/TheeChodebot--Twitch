import os
import time
import random
import asyncio
import logging
import datetime
from dotenv import load_dotenv
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from pyprobs import Probability as pr
from mondocs import Users, EconomyData, Channel
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.oauth import UserAuthenticationStorageHelper
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME
from functions import logs_directory, chat_log, read_clock, write_clock, long_dashes
from twitchAPI.object.eventsub import ChannelAdBreakBeginEvent, ChannelChatMessageEvent, ChannelCheerEvent, ChannelFollowEvent, \
    StreamOnlineEvent, StreamOfflineEvent, HypeTrainEvent, HypeTrainEndEvent, ChannelPollBeginEvent, ChannelPollEndEvent, \
    ChannelRaidEvent, ChannelPointsCustomRewardRedemptionAddEvent, ChannelSubscribeEvent, ChannelSubscriptionGiftEvent, \
    ChannelUpdateEvent, ChannelPredictionEvent, ChannelPredictionEndEvent, ChannelChatNotificationEvent

cmd = "$"
load_dotenv()
standard_points = 5
standard_seconds = 1
writing_to_clock = True
id_twitch_client = os.getenv("client")
id_twitch_secret = os.getenv("secret")
id_broadcaster_account = os.getenv("broadcaster")
mongo_login_string = os.getenv("monlog_string")
mongo_twitch_collection = os.getenv("montwi_string")
mongo_discord_collection = os.getenv("mondis_string")
target_scopes = [AuthScope.BITS_READ,
                 AuthScope.CLIPS_EDIT,
                 AuthScope.CHANNEL_BOT,
                 AuthScope.USER_READ_CHAT,
                 AuthScope.USER_WRITE_CHAT,
                 AuthScope.CHANNEL_MODERATE,
                 AuthScope.CHANNEL_READ_ADS,
                 AuthScope.CHANNEL_MANAGE_POLLS,
                 AuthScope.USER_MANAGE_WHISPERS,
                 AuthScope.CHANNEL_SUBSCRIPTIONS,
                 AuthScope.CHANNEL_READ_HYPE_TRAIN,
                 AuthScope.MODERATOR_READ_CHATTERS,
                 AuthScope.MODERATOR_READ_FOLLOWERS,
                 AuthScope.MODERATOR_MANAGE_SHOUTOUTS,
                 AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
                 AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
                 AuthScope.CHANNEL_MANAGE_PREDICTIONS,
                 AuthScope.CHANNEL_READ_PREDICTIONS]  # ToDo: FIGURE OUT WHY THEE PREDICTION SHIT FLIPS OUT ON END/LOCK CALL!!!!!!!!!!!
registered_commands = [f"{cmd}commands",
                       f"{cmd}gamble NUMBER_HERE",
                       f"{cmd}lastcomment",
                       f"{cmd}leaderbitties",
                       f"{cmd}pt discord/twitch NUMBER_HERE"]  # ToDo: Think about making use of this as a tuple and checking thru to see if thee bits before spaces match?
twitch_bot = Twitch(id_twitch_client, id_twitch_secret)


async def on_stream_ad_start(data: ChannelAdBreakBeginEvent):
    try:
        if data.event.is_automatic:
            auto_response = f"This is a automatically scheduled ad break"
        else:
            auto_response = f"This is a manually ran ad to attempt to time things better"
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Incoming ad break\n{auto_response} and should only last {data.event.duration_seconds} seconds.")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_ad_start' -- {e}")
        return


async def on_stream_chat_message(data: ChannelChatMessageEvent):
    # ToDo: ------------------------------------------------------------------------------------------------------------
    #  Add .startswith for cheer, to multiply points added later on--
    #  --or like maybe that should live in thee cheer area??? or would that be too smart?
    #  On that note, add identifiers for subbies, gifted subbies to add points
    #  Really there's a lot to do - Add new code for doing new things, new commands for mods--
    #  --just so much to take care of and do
    #  Think HEAVILY on moving chat_logs data to channel_document--
    #  --possibly have a new 'list' of chat entries for each stream day.
    #  -------------------------------------- End of on_stream_chat_message List ---------------------------------------
    try:
        if data.event.chatter_user_id == id_broadcaster_account:
            return
        if data.event.message.text.startswith("!"):
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.chatter_user_name} commands start with '{cmd}' in this channel.")
        chatter_username = data.event.chatter_user_name
        chatter_document = await get_chatter_document(data)
        if chatter_document is None:
            logger.error(f"Chatter Document is None!! -- {data.event.chatter_user_id}/{data.event.chatter_user_name}/{data.event.chatter_user_login}")
            pass
        if data.event.message.text.replace(" ", "") in (f"{cmd}commands", f"{cmd}cmds", f"{cmd}commandlist", f"{cmd}cmdlist"):
            try:
                await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Registered commands are: {' - '.join(registered_commands)}")
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message - commands command -- {f}")
                return
        elif data.event.message.text.replace(" ", "") in (f"{cmd}leaderbitties", f"{cmd}leaderbits"):
            try:
                bits_lb = await twitch_bot.get_bits_leaderboard()
                print(bits_lb.total)
                users_board = ""
                for user in bits_lb:
                    users_board += f"#{user.rank:02d}: {user.user_name}: {user.score} - "
                await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Bitties 4 Titties Leaderboard: {users_board[:-3]}")
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message - leaderbitties command -- {f}")
                return
        elif data.event.message.text.replace(" ", "") in (f"{cmd}lastcomment", f"{cmd}lastmessage", "!lastcomment", "!lastmessage"):
            try:
                last_message = None
                last_message_time = None
                with open(chat_log, "r") as file:
                    chat_logs = file.read()
                chat_logs = list(map(str, chat_logs.splitlines()))
                for last in reversed(chat_logs):
                    if last.startswith(data.event.chatter_user_id):
                        user_name, last_message = last.split(": ", maxsplit=1)
                        break
                if chatter_document is not None:
                    last_message_time = chatter_document['latest_chat_date'].strftime('%H:%M:%S')
                await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.broadcaster_user_name}!!!! {chatter_username}'s last message was: {last_message if not None else 'Not Found!!!'}{f' - Sent @ {last_message_time} MST' if last_message is not None and last_message_time is not None else ''}")
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message - lastcomment command -- {f}")
                return
        elif data.event.message.text.startswith(f"{cmd}gamble"):
            try:
                bet_value = data.event.message.text.lstrip(f"{cmd}gamble ")
                if bet_value.isdigit():
                    bet_value = int(bet_value)
                else:
                    print(f"--{bet_value}")
                    await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{chatter_username} your command should resemble '{cmd}gamble 100' where 100, put your bet value. Try again")
                    return
                print(f"{bet_value} vs {chatter_document['user_points']}")
                if bet_value > chatter_document['user_points']:
                    await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{chatter_username} you do not have enough points to bet that. You currently have {chatter_document['user_points']}")
                    return
                elif bet_value <= chatter_document['user_points']:
                    if pr.prob(97.5/100):
                        response = f"lost {bet_value}"
                        new_points_value = chatter_document['user_points'] - bet_value
                        await twitch_points_transfer(chatter_document, bet_value, False)
                        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{chatter_username} you lost thee gamble, I ate your points. They tasted yummy! You now have {new_points_value} points.")
                    else:
                        won_amount = bet_value * 10000
                        response = f"won {won_amount} with a bet of {bet_value}"
                        new_points_value = chatter_document['user_points'] + won_amount
                        await twitch_points_transfer(chatter_document, won_amount)
                        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{chatter_username} you won thee gamble, winning {won_amount} making your new total {new_points_value}!! Congratz!!!")
                    formatted_time = fortime()
                    gamble_logger.info(f"{formatted_time}: {chatter_username}/{data.event.chatter_user_id} gambled and {response}.")
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message - gamble command -- {f}")
                gamble_logger.error(f"{formatted_time}: Error in on_stream_chat_message - gamble command -- {f}")
                await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{chatter_username} something wen't wrong, TheeChody will fix it sooner than later. Error logged in thee background")
                return
        elif data.event.message.text.startswith(f"{cmd}hug"):
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.chatter_user_name} Big Chody Hugs!!!", reply_parent_message_id=data.event.message_id)
            write_clock(3600, True)  # ToDo: DON'T LEAVE THIS HERE DUMMY
        elif data.event.message.text.startswith(f"{cmd}pt"):
            try:
                if chatter_document['user_discord_id'] == 0:
                    user_discord_id_temp = str(chatter_document['user_id'])[:5] + str(random.randint(10000, 99999))
                    chatter_document.update(user_discord_id=int(user_discord_id_temp))
                    chatter_document.save()
                    await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{chatter_username} you do not have your discord ID linked to your twitch yet. Will attempt to DM you a special code with instructions to link account", reply_parent_message_id=data.event.message_id)
                    await twitch_bot.send_whisper(id_broadcaster_account, data.event.chatter_user_id, f"Hola, your special discord link code is: {user_discord_id_temp} . Head to any discord server TheeChodebot runs in and use this command: $link_twitch {user_discord_id_temp} . Thee code will automatically expire and your message will be deleted in discord and a response confirming will appear")
                    return
                elif str(chatter_document['user_discord_id']).startswith(data.event.chatter_user_id[:5]):
                    await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{chatter_username} check your DM's if their open, if not reach out to {data.event.broadcaster_user_name} to figure it out", reply_parent_message_id=data.event.message_id)
                    return
                chatter_document_discord = await get_discord_document(chatter_document)
                if chatter_document_discord is None:
                    return
                if data.event.message.text.lstrip(f"{cmd}pt ").startswith("witch"):
                    transfer_value = data.event.message.text.lstrip(f"{cmd}pt twitch ")
                    if transfer_value.isdigit():
                        await document_points_transfer("twitch", transfer_value, chatter_document, chatter_document_discord)
                    else:
                        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"I couldn't ID thee number you're trying to transfer", reply_parent_message_id=data.event.message_id)
                        print(f"--{transfer_value}--{type(transfer_value)}")
                        return
                elif data.event.message.text.lstrip(f"{cmd}pt ").startswith("discord"):
                    transfer_value = data.event.message.text.lstrip(f"{cmd}pt discord ")
                    if transfer_value.isdigit():
                        await document_points_transfer("discord", transfer_value, chatter_document, chatter_document_discord)
                    else:
                        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"I couldn't ID thee number you're trying to transfer", reply_parent_message_id=data.event.message_id)
                        print(f"--{transfer_value}--{type(transfer_value)}")
                        return
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message - pt command -- {f}")
        else:
            try:
                await twitch_points_transfer(chatter_document, standard_points)
                chat_logger.info(f"{data.event.chatter_user_id}/{data.event.chatter_user_name}: {data.event.message.text if data.event.message_type == 'text' else 'not a text message'}")
            except Exception as f:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in on_stream_chat_message - else - twitch_points? -- {f}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in on_stream_chat_message -- {e}")
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Something went wrong in thee backend, error logged. Try again later")
        return


async def on_stream_chat_notification(data: ChannelChatNotificationEvent):
    """
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
        if data.event.notice_type == "resub":
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.chatter_user_name} is on a {data.event.resub.streak_months} streak! {data.event.resub.cumulative_months} total months subscribed. Much Love <3")
        else:
            print(f"on_stream_chat_notification -- {data.event.notice_type}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in on_stream_chat_notification -- {e}")
        return


async def on_stream_cheer(data: ChannelCheerEvent):
    try:
        if data.event.is_anonymous:
            user = "Anonymous"
        else:
            chatter_document = await get_chatter_document(data)
            if chatter_document is None:
                pass
            else:
                points_to_add = round(standard_points * data.event.bits)
                await twitch_points_transfer(chatter_document, points_to_add)
            user = data.event.user_name
        seconds = round(standard_seconds * data.event.bits)
        added_to_clock = try_write_clock(seconds)
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"B-B-Bitties!! {user} has cheered {data.event.bits}{f' adding {datetime.timedelta(seconds=seconds)} to thee timer!!' if added_to_clock else '.'}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_cheer' -- {e}")
        return


async def on_stream_follow(data: ChannelFollowEvent):
    try:
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Welcome {data.event.user_name} to Thee Chodeling's Nest!")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_follow' -- {e}")
        return


async def on_stream_hype_begin(data: HypeTrainEvent):
    try:
        channel_document = await get_channel_document(data)
        if channel_document is None:
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Error grabbing/creating channel document. Try again later")
            return
        channel_document.update(hype_train_current=True, hype_train_current_level=data.event.level)
        channel_document.save()
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Choo Choooooooo!! Hype train started by {data.event.last_contribution.user_name}.")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_hype_begin' -- {e}")
        return


async def on_stream_hype_end(data: HypeTrainEndEvent):
    try:
        channel_document = await get_channel_document(data)
        if channel_document is None:
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Error grabbing/creating channel document. Try again later")
            return
        formatted_time = fortime()
        channel_document.update(hype_train_last=formatted_time, hype_train_current=False, hype_train_current_level=0, hype_train_record_level=data.event.level)
        channel_document.save()
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Hype Train Completed @ {data.event.level}!! Much Love To All <3")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_hype_end' -- {e}")
        return


async def on_stream_hype_progress(data: HypeTrainEvent):
    try:
        channel_document = await get_channel_document(data)
        if channel_document is None:
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Error grabbing/creating channel document. Try again later")
            return
        if data.event.level > channel_document['hype_train_current_level']:
            new_hype_train_current_level = data.event.level
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"New Hype Train Level!! Currently @ {data.event.level}")
        else:
            new_hype_train_current_level = channel_document['hype_train_current_level']
        if new_hype_train_current_level > channel_document['hype_train_record_level']:
            new_hype_train_record_level = data.event.level
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"New Hype Train Record Level!!!!! Record Now @ {data.event.level}")
        else:
            new_hype_train_record_level = channel_document['hype_train_record_level']
        channel_document.update(hype_train_current_level=new_hype_train_current_level, hype_train_record_level=new_hype_train_record_level)
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
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Poll '{data.event.title}' has started. Choices are: {choices[:-3]}. Poll will end at {data.event.ends_at.astimezone().strftime('%H:%M:%S')} MST. Voting with extra channel points is {'enabled' if data.event.channel_points_voting.is_enabled else 'disabled'}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_poll_begin' -- {e}")
        return


async def on_stream_poll_end(data: ChannelPollEndEvent):
    try:
        if data.event.status == "archived":
            pass
        else:
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Poll '{data.event.title}' has ended with status: {data.event.status}.")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_poll_end' -- {e}")
        return


async def on_stream_point_redemption(data: ChannelPointsCustomRewardRedemptionAddEvent):
    try:
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.user_name} used {data.event.reward.cost} Theebucks to redeem {data.event.reward.title}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_point_redemption' -- {e}")
        return


async def on_stream_prediction_begin(data: ChannelPredictionEvent):
    try:
        outcomes = ""
        for n, outcome in enumerate(data.event.outcomes):
            outcomes += f"{n+1}: {outcome.title} - "
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Prediction '{data.event.title}' has started. Choices are: {outcomes[:-3]}. Prediction will end at {data.event.locks_at.astimezone().strftime('%H:%M:%S')} MST.")
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
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Prediction '{data.event.title}' has ended with status: {data.event.status}.")
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
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.user_name} subscribed to Thee Nest.\nMuch Love, Thank You :)")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_subbie' -- {e}")
        return


async def on_stream_subbie_gift(data: ChannelSubscriptionGiftEvent):
    try:
        if data.event.is_anonymous:
            user = "Anonymous"
            response = f"Thank You :) Much Love <3"
        else:
            user = data.event.user_name
            response = f"Giving them a total of {data.event.cumulative_total} gifted subbies. Thank You :) Much Love <3"
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{user} gifted out {data.event.total} {'subbie' if data.event.total == 1 else 'subbies'} to Thee Chodelings. {response}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_subbie_gift' -- {e}")
        return


async def on_stream_raid_in(data: ChannelRaidEvent):
    try:
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.from_broadcaster_user_name} raid with {data.event.viewers} incoming!!!\nGo show them some love back y'all")
        await twitch_bot.send_a_shoutout(id_broadcaster_account, data.event.from_broadcaster_user_id, id_broadcaster_account)
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_raid_in' -- {e}")
        return


async def on_stream_raid_out(data: ChannelRaidEvent):
    try:
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.from_broadcaster_user_name} has sent thee raid with {data.event.viewers} to https://twitch.tv/{data.event.to_broadcaster_user_name}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_raid_out' -- {e}")
        return


async def on_stream_update(data: ChannelUpdateEvent):
    try:
        channel_document = await get_channel_document(data)
        if channel_document is None:
            formatted_time = fortime()
            logger.info(f"{formatted_time}: Channel Document is NONE!!!")
            return
        if channel_document['channel_title'] != data.event.title:
            title_response = f"Title Change to {data.event.title} --"
            channel_document.update(channel_title=data.event.title)
            channel_document.save()
        else:
            title_response = f""
        if channel_document['channel_game_id'] != data.event.category_id:
            game_response = f"Category Change to {data.event.category_name} --"
            channel_document.update(channel_game=data.event.category_name, channel_game_id=data.event.category_id)
            channel_document.save()
        else:
            game_response = f""
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Channel Update: {title_response} {game_response}")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_update' -- {e}")
        return


async def on_stream_start(data: StreamOnlineEvent):
    try:
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.broadcaster_user_name} is now online! Gather one, gather all.")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_start' -- {e}")
        return


async def on_stream_end(data: StreamOfflineEvent):
    try:
        await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"{data.event.broadcaster_user_name} has faded into thee shadows. Much Love All")
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in 'on_stream_end' -- {e}")
        return


async def run():
    twitch_helper = UserAuthenticationStorageHelper(twitch_bot, target_scopes)
    await twitch_helper.bind()

    user = await first(twitch_bot.get_users(user_ids=id_broadcaster_account))  # Don't think I need this, however, I feel more comfortable knowing 100% it's grabbing my account, and not some random somehow by mistake...

    event_sub = EventSubWebsocket(twitch_bot)
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
    # await event_sub.listen_channel_prediction_end(user.id, on_stream_prediction_end)  # ToDo: Find out why this is broke!!!! -- TypeError: twitchAPI.object.eventsub.TopPredictors() argument after ** must be a mapping, not list
    # await event_sub.listen_channel_prediction_lock(user.id, on_stream_prediction_lock)  # This one is fucking broke too... Same error ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    await event_sub.listen_channel_subscribe(user.id, on_stream_subbie)
    await event_sub.listen_channel_subscription_gift(user.id, on_stream_subbie_gift)
    await event_sub.listen_channel_raid(on_stream_raid_in, to_broadcaster_user_id=user.id)
    await event_sub.listen_channel_raid(on_stream_raid_out, from_broadcaster_user_id=user.id)
    await event_sub.listen_channel_update_v2(user.id, on_stream_update)
    await event_sub.listen_stream_online(user.id, on_stream_start)
    await event_sub.listen_stream_offline(user.id, on_stream_end)

    while True:
        async def shutdown():
            try:
                print("Shutting down twitch bot processes. Stand By")
                await asyncio.sleep(1)
                await event_sub.stop()
                await asyncio.sleep(1)
                await twitch_bot.close()
                await asyncio.sleep(1)
                await disconnect_mongo()
                await asyncio.sleep(1)
                print("Twitch bot processes shut down successfully")
            except Exception as e:
                print(f"Error in shutdown() -- {e}")
                pass
        try:
            user_input = input("Enter 1 to Start Timer\nEnter 2 to Stop Timer\nEnter 3 to get time\nEnter 4 to add/subtract time\nEnter 0 to Halt Bot\n")
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await shutdown()
                    break
                elif user_input in (1, 2):
                    print("Values 1 & 2 Not Programmed Yet")
                elif user_input == 3:
                    print(read_clock())
                elif user_input == 4:
                    while True:
                        number = input(f"Enter +/-number to add")
                        if number.startswith("+"):
                            add = True
                            break
                        elif number.startswith("-"):
                            add = False
                            break
                        else:
                            print(f"Invalid Input -- You put '{number}'")
                    number = number.lstrip("+").lstrip("-")
                    if number.isdigit():
                        write_clock(int(number), add)
                    else:
                        print(f"Invalid Input -- You put '{number}' which is a {type(number)} -- USE NUMPAD +/-!!")
                else:
                    print(f"Invalid Input -- You put '{user_input}'")
            else:
                print(f"Invalid Input -- You put '{user_input}' which is a {type(user_input)}")
        except Exception as e:
            if KeyboardInterrupt:
                await shutdown()
                break
            else:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error in BOT Loop -- {e}")
                continue


def fortime():
    try:
        nowtime = datetime.datetime.now()
        formatted_time = nowtime.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_time
    except Exception as e:
        logger.error(f"Error creating formatted_time -- {e}")
        return None


def try_write_clock(seconds):
    if writing_to_clock:
        write_clock(seconds)
        return True
    else:
        return False


def setup_logger(name, log_file, level=logging.INFO):
    try:
        handler = logging.FileHandler(f"{logs_directory}{log_file}")
        console_handler = logging.StreamHandler()
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)
        logger.addHandler(console_handler)
        return logger
    except Exception as e:
        formatted_time = fortime()
        print(f"{formatted_time}: ERROR in setup_logger -- {name}/{log_file}/{level} -- {e}")
        return None


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


async def get_channel_document(data):
    try:
        channel_collection = twitch_database.twitch.get_collection('channel')
        try:
            channel_document = Channel(user_id=data.event.broadcaster_user_id)
        except Exception as f:
            if FileNotFoundError:
                try:
                    new_channel_document = Channel(user_id=data.event.broadcaster_user_id, user_name=data.event.broadcaster_user_name,
                                                   user_login=data.event.broadcaster_user_login)
                    new_channel_document_dict = new_channel_document.to_mongo()
                    channel_collection.insert_one(new_channel_document_dict)
                    channel_document = Channel(user_id=data.event.broadcaster_user_id)
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
        users_collection = twitch_database.twitch.get_collection('users')
        try:
            chatter_document = Users.objects.get(user_id=data.event.chatter_user_id)
        except Exception as f:
            if FileNotFoundError:
                try:
                    formatted_time = fortime()
                    new_chatter_document = Users(user_id=data.event.chatter_user_id, user_name=data.event.chatter_user_name,
                                                 user_login=data.event.chatter_user_login, first_chat_date=formatted_time)
                    new_chatter_document_dict = new_chatter_document.to_mongo()
                    users_collection.insert_one(new_chatter_document_dict)
                    chatter_document = Users.objects.get(user_id=data.event.chatter_user_id)
                    pass
                except Exception as g:
                    formatted_time = fortime()
                    logger.error(f"{formatted_time}: Error creating new document for user -- {data.event.chatter_user_name} - {data.event.chatter_user_id}\n{g}")
                    return None
            else:
                formatted_time = fortime()
                logger.error(f"{formatted_time}: Error reading/creating new document for user -- {data.event.chatter_user_name} - {data.event.chatter_user_id}\n{f}")
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
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"You do not have a document in a server TheeChodebot is in as well.")
            return None
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in get_discord_document -- {chatter_document['user_id']}/{chatter_document['user_name']}/{chatter_document['user_login']}/{chatter_document['user_discord_id']} -- {e}")
        return None


async def document_points_transfer(direction, transfer_value, chatter_document, chatter_document_discord):
    try:
        if None in (chatter_document, chatter_document_discord):
            return
        transfer_value = int(transfer_value)
        if direction == "twitch":
            if transfer_value > chatter_document_discord['points_value']:
                await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"You do not have enough discord points to transfer. You have {chatter_document_discord['points_value']} points")
                return
            new_discord_points = chatter_document_discord['points_value'] - transfer_value
            chatter_document_discord.update(points_value=new_discord_points)
            chatter_document_discord.save()
            new_twitch_points = chatter_document['user_points'] + transfer_value
            chatter_document.update(user_points=new_twitch_points)
            chatter_document.save()
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Transferred {transfer_value} to your twitch profile.")
        elif direction == "discord":
            if transfer_value > chatter_document['user_points']:
                await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"You do not have enough discord points to transfer. You have {chatter_document['user_points']} points")
                return
            new_discord_points = chatter_document_discord['points_value'] + transfer_value
            chatter_document_discord.update(points_value=new_discord_points)
            chatter_document_discord.save()
            new_twitch_points = chatter_document['user_points'] - transfer_value
            chatter_document.update(user_points=new_twitch_points)
            chatter_document.save()
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Transferred {transfer_value} to your discord profile.")
        else:
            await twitch_bot.send_chat_message(id_broadcaster_account, id_broadcaster_account, f"Backend Mess up.... {direction} is thee direction")
            return
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in points_transfer -- {chatter_document['user_id']}/{chatter_document['user_name']}/{chatter_document['user_login']}/{chatter_document['user_discord_id']} -- {chatter_document_discord['author_id']}/{chatter_document_discord['author_name']}/{chatter_document_discord['guild_name']}/{chatter_document_discord['twitch_id']} -- {e}")
        return


async def twitch_points_transfer(chatter_document, value: int, add: bool = True):
    try:
        if chatter_document is not None:
            formatted_time = fortime()
            if add:
                new_user_points = chatter_document['user_points'] + value
            else:
                new_user_points = chatter_document['user_points'] - value
            chatter_document.update(user_points=new_user_points, latest_chat_date=formatted_time)
            chatter_document.save()
    except Exception as e:
        formatted_time = fortime()
        logger.error(f"{formatted_time}: Error in twitch_points_transfer -- {chatter_document['user_id']}/{chatter_document['user_name']}/{chatter_document['user_login']} -- {e}")
        return


logger = setup_logger('logger', 'log.log')
chat_logger = setup_logger('chat_logger', 'chat_log.log')
gamble_logger = setup_logger('gamble_logger', 'gamble_log.log')

if None in (logger, chat_logger, gamble_logger):
    print(f"One of thee loggers isn't setup right -- {logger}/{chat_logger}/{gamble_logger} -- Quitting program")
    quit()

while True:
    try:
        # user_input = input("Enter 1 to start twitch bot\nEnter 2 to compile data\nEnter 0 to Exit Program\n")
        user_input = input("Enter 1 to start twitch bot\nEnter 3 to +/- time\nEnter 0 to Exit Program\n")
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
                    while True:
                        number = input(f"Enter +/-number to add")
                        if number.startswith("+"):
                            add = True
                            break
                        elif number.startswith("-"):
                            add = False
                            break
                        else:
                            print(f"Invalid Input -- You put '{number}'")
                    number = number.lstrip("-").lstrip("+")
                    if number.isdigit():
                        write_clock(int(number), add)
                        break
                    else:
                        print(f"Invalid Input -- You put '{number}' which is a {type(number)} -- USE NUMPAD +/-!!")
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
    except Exception as e:
        if KeyboardInterrupt:
            print(f"Exiting Program")
            break
        else:
            formatted_time = fortime()
            logger.error(f"{formatted_time}: Error in MAIN loop -- {e}")
            continue
