import os

from amiyabot import Event
from amiyabot.adapters import BotAdapterProtocol
from amiyabot.adapters.cqhttp import CQHttpBotInstance
from amiyabot.adapters.mirai import MiraiBotInstance

curr_dir = os.path.dirname(__file__)
request_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36',
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Type': 'application/json;charset=UTF-8'
}
tools = [
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 1, 'name': '戳一戳'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 2, 'name': '今日菜单'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 3, 'name': '小小AI'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 4, 'name': 'sauceNAO'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 5, 'name': '伪造消息'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 6, 'name': '一些小功能'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 7, 'name': '兔兔抽奖'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 8, 'name': '合成表情'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 9, 'name': '群友老婆'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 10, 'name': '头像生成'},
    {'main_id': 1, 'sub_id': 1, 'sub_sub_id': 11, 'name': '彩云小梦'},

    {'main_id': 1, 'sub_id': 2, 'sub_sub_id': 1, 'name': '扫雷'},
    {'main_id': 1, 'sub_id': 2, 'sub_sub_id': 2, 'name': '五子棋'},
    {'main_id': 1, 'sub_id': 2, 'sub_sub_id': 3, 'name': '漂流瓶'},
    {'main_id': 1, 'sub_id': 2, 'sub_sub_id': 4, 'name': '塔罗牌'},

    {'main_id': 1, 'sub_id': 3, 'sub_sub_id': 1, 'name': '修改群名片'},
    {'main_id': 1, 'sub_id': 3, 'sub_sub_id': 2, 'name': '修改群头衔'},
    {'main_id': 1, 'sub_id': 3, 'sub_sub_id': 3, 'name': '兔兔撤回'},
    {'main_id': 1, 'sub_id': 3, 'sub_sub_id': 4, 'name': '入群欢迎'},
    {'main_id': 1, 'sub_id': 3, 'sub_sub_id': 5, 'name': '机器人退群'},
    {'main_id': 1, 'sub_id': 3, 'sub_sub_id': 6, 'name': '群禁言'},

    {'main_id': 2, 'sub_id': 1, 'sub_sub_id': 1, 'name': '兔兔重启'},
    {'main_id': 2, 'sub_id': 1, 'sub_sub_id': 2, 'name': '好友申请'},
    {'main_id': 2, 'sub_id': 1, 'sub_sub_id': 3, 'name': '群邀请'},
    {'main_id': 2, 'sub_id': 1, 'sub_sub_id': 4, 'name': '卡池图片更新'},
    {'main_id': 2, 'sub_id': 1, 'sub_sub_id': 5, 'name': '禁言退群'},
]
avatar_dir = f'{curr_dir}/../template/resource/avatar'
bottle_dir = 'resource/plugins/tools/bottle/'


def get_url(id_):
    return 'https://pixiv.re/' + id_ + '.jpg'


async def poke_message_send(message_, event: Event, instance: BotAdapterProtocol):
    if type(instance) is MiraiBotInstance:
        if event.data['subject']['kind'] == 'Group':
            await instance.send_message(message_, channel_id=event.data['subject']['id'])
        elif event.data['subject']['kind'] == 'Friend':
            await instance.send_message(message_, user_id=event.data['subject']['id'])
    elif type(instance) is CQHttpBotInstance:
        if 'group_id' in event.data:
            await instance.send_message(message_, channel_id=event.data['group_id'])
        else:
            await instance.send_message(message_, user_id=event.data['sender_id'])
    return
