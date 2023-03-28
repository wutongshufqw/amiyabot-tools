import time

from amiyabot.database import *

from core.database import config, is_mysql

db = connect_database('tools' if is_mysql else 'resource/plugins/tools/tools.db', is_mysql, config)


class ToolsBaseModel(ModelClass):
    class Meta:
        database = db


@table
class NewFriends(ToolsBaseModel):
    # Common
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    adapter: str = CharField()
    date: int = IntegerField()
    # Mirai
    event_id: int = IntegerField(null=True)
    from_id: int = IntegerField(null=True)
    group_id: int = IntegerField(null=True)
    nick: str = CharField(null=True)
    message: str = CharField(null=True)
    # Gocq
    flag: str = CharField(null=True)
    user_id: int = IntegerField(null=True)
    comment: str = CharField(null=True)


@table
class GroupInvite(ToolsBaseModel):
    # Common
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    adapter: str = CharField()
    date: int = IntegerField()
    group_id: int = IntegerField()
    # Mirai
    event_id: int = IntegerField(null=True)
    from_id: int = IntegerField(null=True)
    group_name: str = CharField(null=True)
    nick: str = CharField(null=True)
    message: str = CharField(null=True)
    # Gocq
    flag: str = CharField(null=True)
    user_id: int = IntegerField(null=True)
    comment: str = CharField(null=True)


@table
class AiBot(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    channel_id: str = CharField()
    random: int = IntegerField()


@table
class Welcome(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    channel_id: str = CharField()
    message: str = CharField()


@table
class Fake(ToolsBaseModel):
    id: int = IntegerField(primary_key=True)
    appid: int = IntegerField()
    channel_id: str = CharField()
    open: bool = BooleanField()


class SQLHelper:
    @staticmethod
    async def add_friend(appid: str, adapter: str, event_id: int = None, from_id: int = None, group_id: int = None,
                         nick: str = None, message: str = None, flag: str = None, user_id: int = None,
                         comment: str = None):
        date = int(time.time())
        friend = NewFriends.get_or_none(NewFriends.appid == appid, NewFriends.adapter == adapter,
                                        NewFriends.user_id == user_id, NewFriends.from_id == from_id)
        if friend:
            friend.date = date
            friend.event_id = event_id
            friend.from_id = from_id
            friend.group_id = group_id
            friend.nick = nick
            friend.message = message
            friend.flag = flag
            friend.comment = comment
            friend.save()
        else:
            NewFriends.create(appid=appid, adapter=adapter, date=date, event_id=event_id, from_id=from_id,
                              group_id=group_id, nick=nick, message=message, flag=flag, user_id=user_id,
                              comment=comment)

    @staticmethod
    async def get_friend(appid: str, adapter: str, qq: int):
        if adapter == 'mirai':
            return NewFriends.get(appid=appid, adapter=adapter, from_id=qq)
        elif adapter == 'gocq':
            return NewFriends.get(appid=appid, adapter=adapter, user_id=qq)

    @staticmethod
    async def get_friends(appid: str, adapter: str):
        return NewFriends.select().where((NewFriends.appid == appid) & (NewFriends.adapter == adapter))

    @staticmethod
    async def delete_friend(appid: str, qq: int):
        NewFriends.delete().where(
            (NewFriends.appid == appid) & ((NewFriends.from_id == qq) | (NewFriends.user_id == qq))).execute()

    @staticmethod
    async def delete_friends(appid: str, adapter: str):
        return NewFriends.delete().where(
            (NewFriends.appid == appid) & (NewFriends.adapter == adapter)).execute() is not None

    @staticmethod
    async def add_invite(appid: str, adapter: str, group_id: int, event_id: int = None, from_id: int = None,
                         group_name: str = None, nick: str = None, message: str = None, flag: str = None,
                         user_id: int = None, comment: str = None):
        date = int(time.time())
        invite = GroupInvite.get_or_none(GroupInvite.appid == appid, GroupInvite.adapter == adapter,
                                         GroupInvite.group_id == group_id)
        if invite:
            invite.date = date
            invite.event_id = event_id
            invite.from_id = from_id
            invite.group_name = group_name
            invite.nick = nick
            invite.flag = flag
            invite.user_id = user_id
            invite.comment = comment
            invite.save()
        else:
            GroupInvite.create(appid=appid, adapter=adapter, date=date, event_id=event_id, from_id=from_id,
                               group_id=group_id, group_name=group_name, nick=nick, message=message, flag=flag,
                               user_id=user_id, comment=comment)

    @staticmethod
    async def get_invite(appid: str, adapter: str, group_id: int):
        return GroupInvite.get(appid=appid, adapter=adapter, group_id=group_id)

    @staticmethod
    async def get_invites(appid: str, adapter: str):
        return GroupInvite.select().where((GroupInvite.appid == appid) & (GroupInvite.adapter == adapter))

    @staticmethod
    async def delete_invite(appid: str, group_id: int):
        GroupInvite.delete().where((GroupInvite.appid == appid) & (GroupInvite.group_id == group_id)).execute()

    @staticmethod
    async def delete_invites(appid: str, adapter: str):
        return GroupInvite.delete().where(
            (GroupInvite.appid == appid) & (GroupInvite.adapter == adapter)).execute() is not None

    @staticmethod
    async def set_ai_probability(appid: str, channel_id: str, random: int):
        ai = AiBot.get_or_none(AiBot.appid == appid, AiBot.channel_id == channel_id)
        if ai:
            ai.random = random
            ai.save()
        else:
            AiBot.create(appid=appid, channel_id=channel_id, random=random)

    @staticmethod
    async def get_ai_probability(appid: str, channel_id: str):
        return AiBot.get_or_none(AiBot.appid == appid, AiBot.channel_id == channel_id)

    @staticmethod
    async def set_welcome(appid: str, channel_id: str, message: str):
        welcome = Welcome.get_or_none(Welcome.appid == appid, Welcome.channel_id == channel_id)
        if welcome:
            welcome.message = message
            welcome.save()
        else:
            Welcome.create(appid=appid, channel_id=channel_id, message=message)

    @staticmethod
    async def get_welcome(appid: str, channel_id: str):
        return Welcome.get_or_none(Welcome.appid == appid, Welcome.channel_id == channel_id)

    @staticmethod
    async def delete_welcome(appid: str, channel_id: str):
        Welcome.delete().where((Welcome.appid == appid) & (Welcome.channel_id == channel_id)).execute()

    @staticmethod
    async def set_fake(appid: str, channel_id: str, open_: bool):
        fake = Fake.get_or_none(Fake.appid == appid, Fake.channel_id == channel_id)
        if fake:
            fake.open = open_
            return fake.save()
        else:
            return Fake.create(appid=appid, channel_id=channel_id, open=open_)

    @staticmethod
    async def get_fake(appid: str, channel_id: str):
        return Fake.get_or_none(Fake.appid == appid, Fake.channel_id == channel_id)
