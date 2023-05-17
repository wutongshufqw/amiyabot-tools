import json
from typing import Union

from amiyabot import Event
from amiyabot.adapters.common import CQCode
from amiyabot.adapters.cqhttp import CQHttpBotInstance
from amiyabot.builtin.message import Message
from amiyabot.builtin.messageChain import Chain
from amiyabot.network.httpRequests import http_requests


async def poke_message_send(message_, event: Event, instance: CQHttpBotInstance):
    if 'group_id' in event.data:
        await instance.send_message(message_, channel_id=event.data['group_id'])
    else:
        await instance.send_message(message_, user_id=event.data['sender_id'])
    return


class GOCQHttpHelper:
    # noinspection HttpUrlsUsage
    def __init__(self, instance: CQHttpBotInstance):
        self.token = instance.token
        host = instance.host
        port = instance.http_port
        self.url = f'http://{host}:{port}'

    async def post(self, path: str, data: dict):
        return await http_requests.post(self.url + path, data, {'Authorization': self.token})

    async def get(self, path: str, data: dict):
        return await http_requests.get(self.url + path, params=data, headers={'Authorization': self.token})

    async def set_group_card(self, group_id: int, user_id: int, card: str):
        return await self.post('/set_group_card', {'group_id': group_id, 'user_id': user_id, 'card': card})

    async def set_group_special_title(self, group_id: int, user_id: int, special_title: str, duration: int = -1):
        return await self.post('/set_group_special_title',
                               {'group_id': group_id, 'user_id': user_id, 'special_title': special_title,
                                'duration': duration})

    async def set_friend_add_request(self, flag: str, approve: bool, remark: str = ''):
        return await self.post('/set_friend_add_request', {'flag': flag, 'approve': approve, 'remark': remark})

    async def set_group_add_request(self, flag: str, sub_type: str, approve: bool, reason: str = ''):
        return await self.post('/set_group_add_request',
                               {'flag': flag, 'sub_type': sub_type, 'approve': approve, 'reason': reason})

    async def delete_msg(self, message_id: int):
        return await self.post('/delete_msg', {'message_id': message_id})

    async def get_group_list(self, no_cache: bool = False):
        return await self.get('/get_group_list', {no_cache: no_cache})

    async def get_group_member_list(self, group_id: int):
        return await self.get('/get_group_member_list', {'group_id': group_id})

    async def get_group_member_info(self, group_id: int, user_id: int, no_cache: bool = False):
        return await self.post('/get_group_member_info',
                               {'group_id': group_id, 'user_id': user_id, 'no_cache': no_cache})

    async def set_group_leave(self, group_id: int, is_dismiss: bool = False):
        return await self.post('/set_group_leave', {'group_id': group_id, 'is_dismiss': is_dismiss})

    async def get_stranger_info(self, user_id: int, no_cache: bool = False):
        return await self.post('/get_stranger_info', {'user_id': user_id, 'no_cache': no_cache})

    async def get_msg(self, message_id: int):
        return await self.post('/get_msg', {'message_id': message_id})


class GOCQTools:
    def __init__(self, instance: CQHttpBotInstance, event: Event = None, data: Message = None):
        self.instance = instance
        self.event = event
        self.data = data
        self.helper = GOCQHttpHelper(instance)

    async def poke(self, event: Event) -> Union[bool, dict]:
        data = event.data
        message = Chain().extend(CQCode('[CQ:poke,qq=' + str(data['user_id']) + ']'))
        await poke_message_send(message, event, self.instance)
        return True

    async def set_group_card(self, group, target, card) -> Union[bool, dict]:
        res = await self.helper.set_group_card(group, target, card)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def set_group_special_title(self, group, target, title) -> Union[bool, dict]:
        res = await self.helper.set_group_special_title(group, target, title)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def new_friend_request(self, operator: int) -> Union[str, dict]:
        data = self.event.data
        text = f'请求人QQ：{data["user_id"]}\n'
        user = await self.get_stranger_info(data["user_id"])
        text += f'请求人昵称：{user.get("nickname")}\n'
        text += f'请求信息：{data["comment"]}'
        message = Chain().text(
            f'收到新的好友请求\n{text}\n发送"兔兔同意好友 [QQ号] [好友备注]"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求')
        await self.instance.send_message(message, str(operator))
        return user.get("nickname")

    async def new_friend_request_handle(self, flag: str, approve: bool, remark: str = '') -> Union[bool, dict]:
        res = await self.helper.set_friend_add_request(flag, approve, remark)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def group_invite(self, operator: int) -> Union[bool, dict]:
        data = self.event.data
        text = f'邀请人QQ：{data["user_id"]}\n群号：{data["group_id"]}'
        message = Chain().text(
            f'收到新的群邀请\n{text}\n发送"兔兔同意邀请 [群号]"以同意邀请\n发送"兔兔拒绝邀请 [群号] [拒绝理由]"以拒绝邀请')
        await self.instance.send_message(message, str(operator))
        return True

    async def group_invite_handle(self, flag: str, approve: bool, reason: str = '') -> Union[bool, dict]:
        res = await self.helper.set_group_add_request(flag, 'invite', approve, reason)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def recall(self, message: dict) -> Union[bool, dict]:
        message_id = message['data']['id']
        res = await self.helper.delete_msg(int(message_id))
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def get_group_list(self, no_cache: bool = False) -> Union[bool, dict]:
        res = await self.helper.get_group_list(no_cache)
        result = json.loads(res)
        if result['status'] == 'ok':
            return result['data']
        else:
            return False

    async def get_group_member_list(self, channel_id: int) -> Union[bool, dict]:
        res = await self.helper.get_group_member_list(channel_id)
        result = json.loads(res)
        if result['status'] == 'ok':
            return result['data']
        else:
            return False

    async def get_group_member_info(self, group_id: int, user_id: int, no_cache: bool = False) -> Union[bool, dict]:
        res = await self.helper.get_group_member_info(group_id, user_id, no_cache)
        result = json.loads(res)
        if result['status'] == 'ok':
            return result['data']
        else:
            return False

    async def quit_group(self, group_id: int) -> Union[bool, dict]:
        res = await self.helper.set_group_leave(group_id)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def get_stranger_info(self, user_id: int, no_cache: bool = False) -> Union[bool, dict]:
        res = await self.helper.get_stranger_info(user_id, no_cache)
        result = json.loads(res)
        if result['status'] == 'ok':
            return result['data']
        else:
            return False

    async def get_message(self, message_id: int) -> Union[bool, dict]:
        res = await self.helper.get_msg(message_id)
        result = json.loads(res)
        if result['status'] == 'ok':
            return result['data']
        else:
            return False
