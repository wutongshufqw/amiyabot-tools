from amiyabot import Message, CQHttpBotInstance, MiraiBotInstance, KOOKBotInstance
from dataclasses import dataclass
from typing import TypedDict, Union

from amiyabot.adapters._adapterApi import RelationType


class UserInfo(TypedDict):
    name: str
    gender: str


@dataclass
class User:
    async def get_info(self) -> UserInfo:
        raise NotImplementedError


@dataclass
class QQGroupUser(User):
    instance: Union[CQHttpBotInstance, MiraiBotInstance]
    data: Message
    user_id: int

    async def get_info(self) -> UserInfo:
        info = await self.instance.api.get_user_info(self.user_id,
                                                     RelationType.GROUP if self.data.channel_id else RelationType.STRANGER,
                                                     self.data.channel_id)
        name = info['nickname']
        gender = info['gender'].__str__()
        return UserInfo(name=name, gender=gender)


@dataclass
class KOOKGroupUser(User):
    instance: KOOKBotInstance
    data: Message
    user_id: int

    async def get_info(self) -> UserInfo:
        info = await self.instance.api.get_user_info(self.user_id, self.data.guild_id)
        name = info.get('nickname', info['username'])
        gender = 'unknown'
        return UserInfo(name=name, gender=gender)
