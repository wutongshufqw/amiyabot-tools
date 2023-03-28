import json
import random

from amiyabot import Event
from amiyabot.adapters.common import CQCode
from amiyabot.adapters.cqhttp import CQHttpBotInstance
from amiyabot.builtin.message import Message
from amiyabot.builtin.messageChain import Chain
from amiyabot.network.download import download_async
from amiyabot.network.httpRequests import http_requests

from core.database.bot import *
from .config import get_url, poke_message_send, request_headers


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

    async def get_group_member_info(self, group_id: int, user_id: int, no_cache: bool = False):
        return await self.post('/get_group_member_info',
                               {'group_id': group_id, 'user_id': user_id, 'no_cache': no_cache})


class GOCQTools:
    def __init__(self, instance: CQHttpBotInstance, event: Event = None, data: Message = None):
        self.instance = instance
        self.event = event
        self.data = data
        self.helper = GOCQHttpHelper(instance)

    async def poke(self, config_):
        message = Chain()
        data = self.event.data
        msg = random.choice(config_['poke']['replies'])
        pattern = re.compile(r'\[.*?]')
        m0 = pattern.findall(msg)
        m1 = pattern.split(msg)
        flag = False
        for i in range(len(m1)):
            # m1
            if m1[i] != '':
                if not flag:
                    message = Chain()
                message = message.text(m1[i])
                flag = True
            # m0
            if i < len(m0):
                if m0[i] == '[pixiv]':
                    if flag:
                        await poke_message_send(message, self.event, self.instance)
                        flag = False
                    res = await http_requests.get(
                        'https://www.pixivs.cn/ajax/illust/discovery?mode=safe&max=1&_vercel_no_cache=1',
                        headers=request_headers)
                    result = json.loads(res)
                    if result['illusts'][0].get('id'):
                        illust = result['illusts'][0]
                    else:
                        illust = result['illusts'][1]
                    img_url = get_url(illust['id'])
                    img_name = illust['title']
                    img_author = illust['userName']
                    img_pid = illust['id']
                    img = await download_async(img_url, request_headers)
                    message = Chain().at(data['user_id']).text(
                        '\n标题：' + img_name + '\n作者：' + img_author + '\nPID：' + str(img_pid)).image(img)
                    await poke_message_send(message, self.event, self.instance)
                elif m0[i] == '[poke]':
                    if flag:
                        await poke_message_send(message, self.event, self.instance)
                        flag = False
                    message = Chain().extend(CQCode('[CQ:poke,qq=' + str(data['user_id']) + ']'))
                    await poke_message_send(message, self.event, self.instance)
                elif m0[i].startswith('[face'):
                    if not flag:
                        message = Chain()
                        flag = True
                    id_ = int(m0[i].split(' ')[1].split(']')[0])
                    message = message.face(id_)
                else:
                    if not flag:
                        message = Chain()
                        flag = True
                    message = message.text(m0[i])
        if flag:
            await poke_message_send(message, self.event, self.instance)
        return

    async def set_group_card(self, group, target, card):
        res = await self.helper.set_group_card(group, target, card)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def set_group_special_title(self, group, target, title):
        res = await self.helper.set_group_special_title(group, target, title)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def new_friend_request(self, operator: int):
        data = self.event.data
        text = f'请求人QQ：{data["user_id"]}\n'
        text += f'请求信息：{data["comment"]}'
        message = Chain().text(
            f'收到新的好友请求\n{text}\n发送"兔兔同意好友 [QQ号] [好友备注]"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求')
        await self.instance.send_message(message, str(operator))

    async def new_friend_request_handle(self, flag: str, approve: bool, remark: str = ''):
        res = await self.helper.set_friend_add_request(flag, approve, remark)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def group_invite(self, operator: int):
        data = self.event.data
        text = f'邀请人QQ：{data["user_id"]}\n群号：{data["group_id"]}'
        message = Chain().text(
            f'收到新的群邀请\n{text}\n发送"兔兔同意邀请 [群号]"以同意邀请\n发送"兔兔拒绝邀请 [群号] [拒绝理由]"以拒绝邀请')
        await self.instance.send_message(message, str(operator))
        return

    async def group_invite_handle(self, flag: str, approve: bool, reason: str = ''):
        res = await self.helper.set_group_add_request(flag, 'invite', approve, reason)
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def recall(self, message: dict):
        message_id = message['data']['id']
        res = await self.helper.delete_msg(int(message_id))
        result = json.loads(res)
        if result['status'] == 'ok':
            return True
        else:
            return False

    async def get_group_member_info(self, group_id: int, user_id: int, no_cache: bool = False):
        res = await self.helper.get_group_member_info(group_id, user_id, no_cache)
        result = json.loads(res)
        if result['status'] == 'ok':
            return result['data']
        else:
            return False
