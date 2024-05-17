from mongoengine import Document, BooleanField, IntField, DynamicField, ListField, DateTimeField


class Channel(Document):
    user_id = IntField(primary_key=True)
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    channel_title = DynamicField(default="")
    channel_game = DynamicField(default="")
    channel_game_id = DynamicField(default=0)
    channel_content_class = ListField(default=[])
    hype_train_last = DynamicField(default="")
    hype_train_current = BooleanField(default=False)
    hype_train_current_level = IntField(default=0)
    hype_train_record_level = IntField(default=0)


class Users(Document):
    user_id = IntField(primary_key=True)
    user_name = DynamicField(default="")
    user_login = DynamicField(default="")
    user_points = IntField(default=0)
    first_chat_date = DynamicField(default="")
    latest_chat_date = DynamicField(default="")
    user_discord_id = IntField(default=0)
    meta = {"db_alias": "default"}


class EconomyData(Document):
    author_id = IntField(primary_key=True)
    author_name = DynamicField(default="")
    guild_name = DynamicField(default="")
    last_daily_done = DateTimeField(default=None)
    next_daily_avail = DateTimeField(default=None)
    points_value = DynamicField(default=0)
    last_gained_value = DynamicField(default=0)
    last_lost_value = DynamicField(default=0)
    highest_gained_value = DynamicField(default=0)
    highest_lost_value = DynamicField(default=0)
    highest_gambling_won = DynamicField(default=0)
    highest_gambling_lost = DynamicField(default=0)
    total_gambling_won = DynamicField(default=0)
    total_gambling_lost = DynamicField(default=0)
    twitch_id = DynamicField(default=0)
    meta = {"db_alias": "Discord_Database"}
