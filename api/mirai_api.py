import json
from typing import Union

from amiyabot import Event
from amiyabot.adapters.mirai import MiraiBotInstance
from amiyabot.builtin.message import Message
from amiyabot.builtin.messageChain import Chain
from amiyabot.network.httpRequests import http_requests


class MiraiHttpHelper:
    # noinspection HttpUrlsUsage
    def __init__(self, instance: MiraiBotInstance):
        self.session = instance.session
        host = instance.host
        port = instance.http_port
        self.url = f'http://{host}:{port}'

    async def post(self, path: str, data: dict):
        return await http_requests.post(self.url + path, data)

    async def get(self, path: str, data: dict):
        return await http_requests.get(self.url + path, params=data)

    async def send_nudge(self, target: int, subject: int, kind: str):
        return await self.post('/sendNudge',
                               {'sessionKey': self.session, 'target': target, 'subject': subject, 'kind': kind})

    async def member_info(self, target: int, member_id: int, name: str = None, special_title: str = None):
        if name is not None:
            return await self.post('/memberInfo', {'sessionKey': self.session, 'target': target, 'memberId': member_id,
                                                   'info': {'name': name}})
        elif special_title is not None:
            return await self.post('/memberInfo', {'sessionKey': self.session, 'target': target, 'memberId': member_id,
                                                   'info': {'specialTitle': special_title}})
        elif name is not None and special_title is not None:
            return await self.post('/memberInfo', {'sessionKey': self.session, 'target': target, 'memberId': member_id,
                                                   'info': {'name': name, 'specialTitle': special_title}})

    async def new_friend_request_event(self, eventId: int, from_id: int, group_id: int, operate: int,
                                       message: str = ''):
        return await self.post('/resp/newFriendRequestEvent', {'sessionKey': self.session, 'eventId': eventId,
                                                               'fromId': from_id, 'groupId': group_id,
                                                               'operate': operate,
                                                               'message': message})

    async def bot_invited_join_group_request_event(self, eventId: int, from_id: int, group_id: int, operate: int,
                                                   message: str = ''):
        return await self.post('/resp/botInvitedJoinGroupRequestEvent', {'sessionKey': self.session, 'eventId': eventId,
                                                                         'fromId': from_id, 'groupId': group_id,
                                                                         'operate': operate,
                                                                         'message': message})

    async def recall(self, target: int, message_id: int):
        return await self.post('/recall', {'sessionKey': self.session, 'target': target, 'messageId': message_id})

    async def group_list(self):
        return await self.get('/groupList', {'sessionKey': self.session})

    async def member_list(self, target: int):
        return await self.get('/memberList', {'sessionKey': self.session, 'target': target})

    async def member_profile(self, target: int, member_id: int):
        return await self.get('/memberProfile', {'sessionKey': self.session, 'target': target, 'memberId': member_id})

    async def quit(self, target: int):
        return await self.post('/quit', {'sessionKey': self.session, 'target': target})

    async def user_profile(self, target: int):
        return await self.get('/userProfile', {'sessionKey': self.session, 'target': target})

    async def mute(self, target: int, member_id: int, time: int):
        return await self.post(
            '/mute',
            {'sessionKey': self.session, 'target': target, 'memberId': member_id, 'time': time}
        )


class MiraiTools:
    def __init__(self, instance: MiraiBotInstance, event: Event = None, data: Message = None):
        self.instance = instance
        self.event = event
        self.data = data
        self.helper = MiraiHttpHelper(instance)

    async def poke(self, event: Event) -> Union[bool, dict]:
        data = event.data
        res = await self.helper.send_nudge(data['fromId'], data['subject']['id'], data['subject']['kind'])
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def set_group_card(self, group: int, target: int, card: str) -> Union[bool, dict]:
        res = await self.helper.member_info(group, target, name=card)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def set_group_special_title(self, group, target, title) -> Union[bool, dict]:
        res = await self.helper.member_info(group, target, special_title=title)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def new_friend_request(self, operator: int) -> Union[bool, dict]:
        data = self.event.data
        text = f'请求人QQ：{data["fromId"]}\n请求人昵称：{data["nick"]}\n'
        if data['groupId'] != 0:
            text += f'来自群聊：{data["groupId"]}\n'
        text += f'请求信息：{data["message"]}'
        message = Chain().text(
            f'收到新的好友请求\n{text}\n发送"兔兔同意好友 [QQ号] [回复信息]"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求\n'
            f'发送"兔兔拉黑好友 [QQ号]"以拉黑请求')
        await self.instance.send_message(message, str(operator))
        return True

    async def new_friend_request_handle(self, event_id: int, from_id: int, group_id: int, operate: int,
                                        message: str = '') -> Union[bool, dict]:
        res = await self.helper.new_friend_request_event(event_id, from_id, group_id, operate, message)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def group_invite(self, operator: int) -> Union[bool, dict]:
        data = self.event.data
        text = f'邀请人：{data["nick"]}\n邀请人QQ：{data["fromId"]}\n群聊：{data["groupName"]}\n' \
               f'群号：{data["groupId"]}\n邀请信息：{data["message"]}'
        message = Chain().text(
            f'收到新的群聊邀请\n{text}\n发送"兔兔同意邀请 [群号] [回复消息]"以同意邀请\n发送"兔兔拒绝邀请 [群号] [回复消息]"以拒绝邀请')
        await self.instance.send_message(message, str(operator))
        return True

    async def group_invite_handle(
        self,
        event_id: int,
        from_id: int,
        group_id: int,
        operate: int,
        message: str = ''
    ) -> Union[bool, dict]:
        res = await self.helper.bot_invited_join_group_request_event(event_id, from_id, group_id, operate, message)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def recall(self, message: dict) -> Union[bool, dict]:
        message_id = message['id']
        if message['groupId'] != 0:
            target = message['groupId']
            res = await self.helper.recall(target, message_id)
            result = json.loads(res)
            if result['code'] == 0:
                return True
        return False

    async def get_group_list(self) -> Union[bool, dict]:
        res = await self.helper.group_list()
        result = json.loads(res)
        if result['code'] == 0:
            return result['data']
        else:
            return False

    async def get_group_member_list(self, channel_id: int) -> Union[bool, dict]:
        res = await self.helper.member_list(channel_id)
        result = json.loads(res)
        if result['code'] == 0:
            return result['data']
        else:
            return False

    async def get_group_member_info(self, group_id: int, user_id: int) -> Union[bool, dict]:
        res = await self.helper.member_profile(group_id, user_id)
        result = json.loads(res)
        if result.get('nickname'):
            return result
        else:
            return False

    async def quit_group(self, target: int) -> Union[bool, dict]:
        res = await self.helper.quit(target)
        result = json.loads(res)
        if result['code'] == 0:
            return True
        else:
            return False

    async def get_stranger_info(self, user_id: int) -> Union[bool, dict]:
        res = await self.helper.user_profile(user_id)
        result = json.loads(res)
        if result.get('nickname'):
            return result
        else:
            return False

    async def ban(self, channel_id: int, user_id: int, ban_time: int) -> bool:
        res = await self.helper.mute(channel_id, user_id, ban_time)
        result = json.loads(res)
        return result['code'] == 0
