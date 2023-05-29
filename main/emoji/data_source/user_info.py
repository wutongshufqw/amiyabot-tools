from amiyabot import Message, CQHttpBotInstance, MiraiBotInstance
from dataclasses import dataclass
from typing import TypedDict, Union

from ....api import GOCQTools, MiraiTools


class UserInfo(TypedDict):
    name: str
    gender: str


@dataclass
class User:
    async def get_info(self) -> UserInfo:
        raise NotImplementedError


@dataclass
class QQUser(User):
    instance: Union[CQHttpBotInstance, MiraiBotInstance]
    data: Message
    user_id: int

    async def get_info(self) -> UserInfo:
        helper = None
        if type(self.instance) is CQHttpBotInstance:
            helper = GOCQTools(self.instance, data=self.data)
        elif type(self.instance) is MiraiBotInstance:
            helper = MiraiTools(self.instance, data=self.data)
        if helper is None:
            raise NotImplementedError
        info = await helper.get_group_member_info(group_id=int(self.data.channel_id), user_id=int(self.user_id))
        if not info:
            info = await helper.get_stranger_info(user_id=int(self.user_id))
        name = info.get('card', info.get('nickname', ''))
        gender = info.get('sex', 'unknown').lower()
        return UserInfo(name=name, gender=gender)
