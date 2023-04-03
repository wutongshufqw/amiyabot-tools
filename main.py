import asyncio
import json
import math
import os
import random
import shutil
import sys
import traceback

import yaml
from amiyabot import PluginInstance, Event, Message
from amiyabot.adapters.cqhttp import CQHttpBotInstance
from amiyabot.adapters.cqhttp.forwardMessage import CQHTTPForwardMessage
from amiyabot.adapters.mirai import MiraiBotInstance
from amiyabot.adapters.mirai.forwardMessage import MiraiForwardMessage
from amiyabot.builtin.messageChain import Chain
from amiyabot.factory import BotHandlerFactory
from amiyabot.network.download import download_async
from amiyabot.network.httpRequests import http_requests
from lxml import etree

from core import bot as main_bot, GitAutomation
from core.database.bot import *
from core.database.user import UserInfo
from core.util import create_dir, read_yaml
from .gocqapi import GOCQTools
from .miraiapi import MiraiTools
from .sauceNAO import get_saucenao
from .sql import *
from .zhconv import convert

curr_dir = os.path.dirname(__file__)
config_file = 'resource/plugins/tools/config.yaml'
avatar_dir = f'{curr_dir}/template/resource/avatar'
poke_cd = {}
special_title_cd = {}
recall_list = []


class BottleFlowPluginInstance(PluginInstance):
    def install(self):
        config_install()
        remove_dir(avatar_dir)
        create_dir(avatar_dir)


bot = BottleFlowPluginInstance(
    name='小工具合集',
    version='1.6.0',
    plugin_id='amiyabot-tools',
    plugin_type='tools',
    description='AmiyaBot小工具合集 By 天基',
    document=f'{curr_dir}/README.md'
)


def add_dict(a, b):
    data = {a: b}
    file = open(config_file, 'a', encoding='utf-8')
    yaml.dump(data, file, allow_unicode=True)
    file.close()


def edit_dict(a, b):
    config_ = read_yaml(config_file, _dict=True)
    config_[a] = b
    file = open(config_file, 'w', encoding='utf-8')
    yaml.dump(config_, file, allow_unicode=True)
    file.close()


def delete_dict(a):
    config_ = read_yaml(config_file, _dict=True)
    del config_[a]
    file = open(config_file, 'w', encoding='utf-8')
    yaml.dump(config_, file, allow_unicode=True)
    file.close()


def create_file(path: str, mode: str = 'a'):
    if not os.path.exists(path):
        create_dir(path, is_file=True)
    try:
        if mode.index('b') != -1:
            return open(path, mode)
    except ValueError:
        return open(path, mode, encoding='utf-8')


def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)


def remove_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)


def config_install():
    create_file(config_file).close()
    config_ = read_yaml(config_file, _dict=True)
    if config_ is None or config_.get('poke') is None:  # 戳一戳配置初始化
        data = {
            'cd': 3,
            'replies': [
                '？',
                'hentai!',
                '( >﹏<。)',
                '好气喔，我要给你起个难听的绰号',
                '那...那里...那里不能戳...',
                '[pixiv]喏',
                '不准戳我啦[face 175]',
                '[poke]'
            ]
        }
        add_dict('poke', data)
    if config_ is None or config_.get('specialTitle') is None:  # 修改群头衔配置初始化
        data = {
            'cd': 1800,
            'admin': False,
            'guest': False
        }
        add_dict('specialTitle', data)
    if config_ is None or config_.get('restart') is None:  # 重启机器人配置初始化
        data = []
        add_dict('restart', data)
    if config_ is None or config_.get('operator') is None:  # 处理好友，群聊事件配置初始化
        if config_ is not None and config_.get('newFriend') is not None:
            data = config_['newFriend']
            delete_dict('newFriend')
        else:
            data = None
        add_dict('operator', data)
    if config_ is None or config_.get('sauceNAO') is None:  # SauceNAO配置初始化
        data = {
            'api_key': None,
            'proxy': None,
        }
        add_dict('sauceNAO', data)


def get_cooldown(flag, map_: dict):
    if not map_.__contains__(flag):
        return 0
    last = map_[flag]
    if time.time() >= last:
        return 0
    return 1


def set_cooldown(flag, map_, cd: int):
    map_[flag] = time.time() + cd


# 戳一戳
@bot.on_event('NudgeEvent')  # Mirai戳一戳
async def poke(event: Event, instance: MiraiBotInstance):
    config_ = read_yaml(config_file, _dict=True)
    if int(instance.appid) == event.data['target'] and config_['poke']['cd'] >= 0:
        if get_cooldown(event.data['subject']['id'], poke_cd) == 1:
            return
        set_cooldown(event.data['subject']['id'], poke_cd, config_['poke']['cd'])
        mirai = MiraiTools(instance, event=event)
        await mirai.poke(config_)
    return


@bot.on_event('notice.notify.poke')  # gocq戳一戳
async def poke(event: Event, instance: CQHttpBotInstance):
    config_ = read_yaml(config_file, _dict=True)
    if int(instance.appid) == event.data['target_id'] and config_['poke']['cd'] >= 0:
        if 'group_id' in event.data:
            if get_cooldown(event.data['group_id'], poke_cd) == 1:
                return
            set_cooldown(event.data['group_id'], poke_cd, config_['poke']['cd'])
        else:
            if get_cooldown(event.data['sender_id'], poke_cd) == 1:
                return
            set_cooldown(event.data['sender_id'], poke_cd, config_['poke']['cd'])
        gocq = GOCQTools(instance, event=event)
        await gocq.poke(config_)
    return


# 今天吃什么
@bot.on_message(keywords=['今天吃什么'], allow_direct=True, level=5)
async def eat(data: Message):
    res = await http_requests.get('https://home.meishichina.com/show-top-type-recipe.html')
    html = etree.HTML(res)
    map_ = {}
    pages = html.xpath('//div[@class="ui-page-inner"]/a/text()')
    page = int(pages[pages.index('下一页') - 1])
    j = 0
    for i in range(1, page + 1):
        if i != 1:
            res = await http_requests.get(f'https://home.meishichina.com/show-top-type-recipe-page-{i}.html')
            # noinspection PyBroadException
            try:
                html = etree.HTML(res)
            except Exception:
                break
        recipe_name = html.xpath('//div[@class="detail"]/h2/a/text()')
        recipe_material = html.xpath('//div[@class="detail"]/p[@class="subcontent"]/text()')
        images = html.xpath('//div[@class="pic"]/a/img/@data-src')
        for k in range(len(recipe_name)):
            map_[j] = {'name': recipe_name[k], 'material': recipe_material[k], 'image': images[k]}
            j += 1
    id_ = random.randint(0, j - 1)
    name = map_[id_]['name']
    material = map_[id_]['material']
    image = await download_async(map_[id_]['image'])
    return Chain(data).text(f'今天吃{name}吧\n{material}').image(image)


# 人工智障
@bot.on_message(keywords=['调整AI概率'], allow_direct=False, level=5)
async def adjust_ai(data: Message):
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        pattern = re.compile('^.*?调整AI概率\\D*?(\\d+)$', re.I)
        m = pattern.match(data.text_original)
        if not m:
            return Chain(data).text('未检测到数字')
        probability = int(m.group(1))
        if probability < 0 or probability > 50:
            return Chain(data).text('请输入0-50的数字')
        await SQLHelper.set_ai_probability(data.instance.appid, data.channel_id, probability)
        return Chain(data).text(f'AI概率已调整为{probability}%')
    return Chain(data).text('你没有权限哦')


def verify_prefix(msg: str):
    if msg.startswith(('兔兔天气', '兔兔歌词', '兔兔计算', '兔兔归属', '兔兔成语', '兔兔翻译')):
        return True
    elif msg.startswith('兔兔'):
        info = msg.replace('兔兔', '')
        try:
            if info.index('笑话') >= 0:
                return True
        except ValueError:
            pass
        patterns = [
            re.compile('^(-?\\d+[.+\\-*/]?)*-?\\d+$'),
            re.compile(
                '^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\.(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\.(1\\d{2}|2['
                '0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\.(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$'),
            re.compile('^(13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[0-35-9])\\d{8}$')
        ]
        for pattern in patterns:
            if pattern.search(info):
                return True
        if info.endswith(('五笔', '拼音',)):
            return True
    return False


async def check_ai(data: Message):
    if data.is_at and '撤回' not in data.text_original and '兔兔chat' not in data.text_original:
        return True, 10, True
    msg = data.text_original
    if msg == '' or re.match(r'^\d+$', msg) or msg in ['初级', '中级', '高级', '资深', '普通', '硬核']:
        return False, -1, False
    probability = await SQLHelper.get_ai_probability(data.instance.appid, data.channel_id)
    if verify_prefix(msg) and (probability is not None and probability.random > 0):
        return True, 5, True
    if probability is None:
        return False, -1, False
    if random.randint(1, 100) <= probability.random:
        return True, -1, False
    return False, -1, False


@bot.on_message(verify=check_ai, check_prefix=False, allow_direct=False)
async def ai(data: Message):
    if data.is_at:
        return
    if data.verify.keypoint:
        data.text_original = data.text_original.replace('兔兔', '')
    if data.text_original.startswith('天气'):
        city = data.text_original.replace('天气', '')
        if city == '':
            city = '北京'
        return Chain(data).html(
            f'https://weathernew.pae.baidu.com/weathernew/pc?query={city}天气&srcid=4982&forecast=long_day_forecast',
            is_template=False, render_time=1000, height=1000, width=1000
        )
    res = await http_requests.get(f'http://api.qingyunke.com/api.php?key=free&appid=0&msg={data.text_original}')
    result = json.loads(res)
    content = convert(result['content'], 'zh-cn').replace('{br}', '\n').replace('菲菲', '兔兔')
    pattern = re.compile(r'\{face:.*?}')
    m0 = pattern.findall(content)
    m1 = pattern.split(content)
    msg = Chain(data, at=False)
    for i in range(len(m1)):
        msg = msg.text(m1[i])
        if i < len(m0):
            msg = msg.face(m0[i].replace('{face:', '').replace('}', ''))
    if content != "未获取到相关信息":
        return msg
    return


# 搜图
@bot.on_message(keywords=['搜索图片'], allow_direct=False, level=5)
async def search_image(data: Message):
    if data.image.__len__() == 0:
        return Chain(data).text('请发送图片')
    elif data.image.__len__() > 1:
        return Chain(data).text('只能发送一张图片>_<')
    else:
        config_ = read_yaml(config_file, _dict=True)
        if config_.get('sauceNAO') is None or config_['sauceNAO'].get('api_key') is None:
            return Chain(data).text('请先配置SauceNAO的API Key')
        flag, tip, json_ = await get_saucenao(data.image[0], config_['sauceNAO']['api_key'],
                                              config_['sauceNAO'].get('proxy'))
        if flag:
            image = None
            if json_['service_name'] == 'pixiv':
                image = await download_async(
                    'https://pixiv.re/' + str(json_['illust_id']) + json_['page_string'].replace('_p', '-') + '.jpg')
            res = await data.send(Chain(data).text(tip).image(image).text('20s后撤回'))
            if res:
                recall_list.append({'res': res, 'time': time.time() + 20})
            return
        else:
            tip = '出错了>_<\n' + '错误信息:\n' + tip
            return Chain(data).text(tip)


# 伪造消息
@bot.on_message(keywords=['伪造消息'], allow_direct=False, level=5)
async def fake_message(data: Message):
    fake = await SQLHelper.get_fake(data.instance.appid, data.channel_id)
    if fake and fake.open:
        if type(data.instance) is MiraiBotInstance:
            forward = MiraiForwardMessage(data)
            helper = MiraiTools(data.instance, data=data)
        elif type(data.instance) is CQHttpBotInstance:
            forward = CQHTTPForwardMessage(data)
            helper = GOCQTools(data.instance, data=data)
        else:
            return Chain(data).text('不支持的机器人类型')
        reply = await data.wait(Chain(data).text('请选择伪造模式：\n[1]单条\n[2]多条'), True)
        if reply:
            try:
                mode = int(reply.text_original)
            except ValueError:
                await data.send(Chain(reply, at=False).text('输入错误'))
                return
            if mode == 1:
                reply = await data.wait(Chain(reply, at=False).text('请发送要伪造的消息并@对方'), True, max_time=60)
                if reply:
                    msg = reply.text_original
                    if not msg:
                        return Chain(reply).text('输入错误')
                    elif reply.at_target.__len__() == 0:
                        return Chain(reply).text('未@任何人')
                    else:
                        member_info = await helper.get_group_member_info(int(data.channel_id), int(reply.at_target[0]))
                        if not member_info:
                            return Chain(reply).text('获取用户信息失败')
                        else:
                            nickname = member_info['nickname']
                            chain = Chain().text(msg)
                            await forward.add_message(chain, int(reply.at_target[0]), nickname)
                            await forward.send()
                            return
            elif mode == 2:
                reply = await data.wait(Chain(reply, at=False).text('请发送要伪造的消息并@对方,发送"\\stop"以结束'),
                                        True,
                                        max_time=60)
                sum_ = 0
                while reply:
                    msg = reply.text_original
                    if not msg:
                        reply = await data.wait(
                            Chain(reply).text('输入错误，请重新发送要伪造的消息并@对方,发送"\\stop"以结束'), True,
                            max_time=60)
                        continue
                    elif msg == '\\stop':
                        await forward.send()
                        return
                    elif reply.at_target.__len__() == 0:
                        reply = await data.wait(
                            Chain(reply).text('未@任何人,请重新发送要伪造的消息并@对方,发送"\\stop"以结束'), True,
                            max_time=60)
                        continue
                    else:
                        member_info = await helper.get_group_member_info(int(data.channel_id), int(reply.at_target[0]))
                        if not member_info:
                            reply = await data.wait(
                                Chain(reply).text('获取用户信息失败,请重新发送要伪造的消息并@对方,发送"\\stop"以结束'),
                                True,
                                max_time=60)
                            continue
                        else:
                            nickname = member_info['nickname']
                            chain = Chain().text(msg)
                            await forward.add_message(chain, int(reply.at_target[0]), nickname)
                            sum_ += 1
                            reply = await data.wait(Chain(reply, at=False).text(f'当前消息数: {sum_}'), True,
                                                    max_time=60)
        return Chain(data).text('回复超时，伪造失败')
    else:
        return Chain(data).text('本群未开启伪造消息功能')


@bot.on_message(keywords=['开启消息伪造', '关闭消息伪造'], allow_direct=False, level=5)
async def fake_message_switch(data: Message):
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        if '开启' in data.text_original:
            if await SQLHelper.set_fake(data.instance.appid, data.channel_id, True):
                return Chain(data).text('开启成功')
        elif '关闭' in data.text_original:
            if await SQLHelper.set_fake(data.instance.appid, data.channel_id, False):
                return Chain(data).text('关闭成功')
        return Chain(data).text('操作失败')
    return Chain(data).text('权限不足')


# 各类API
@bot.on_message(keywords=['每日一言', '猜谜'], allow_direct=True, level=5)
async def api_handler(data: Message):
    if data.text_original.startswith("兔兔每日一言"):
        res = await http_requests.get('https://v.api.aa1.cn/api/yiyan/index.php')
        try:
            html = etree.HTML(res)
            text = html.xpath('//p/text()')[0]
            return Chain(data).text(text)
        except etree.XMLSyntaxError:
            return Chain(data).text('获取失败')
    elif data.text_original.startswith("兔兔猜谜"):
        res = await http_requests.get('https://v.api.aa1.cn/api/api-miyu/index.php')
        try:
            response = json.loads(res)
            if int(response['code']) == 1:
                times = -1
                limit_time = time.time() + 300
                await data.send(Chain(data, at=False).text(f'兔兔找到了一道{response["lx"]}题，快来猜一猜吧！'))
                event = None
                flag = False
                tip = False
                reply = None
                while times < 10:
                    await asyncio.sleep(0)
                    if times == -1:
                        event = await data.wait_channel(Chain(data, at=False).text(f'谜题：{response["mt"]}'), True,
                                                        True,
                                                        int(limit_time - time.time()))
                        times += 1
                    elif flag:
                        event = await data.wait_channel(
                            Chain(reply, at=False).text(f'回答错误({times}/10), 请再猜一猜吧！'),
                            True, True, int(limit_time - time.time()))
                        flag = False
                    else:
                        event = await data.wait_channel(max_time=int(limit_time - time.time()))
                    if event:
                        reply = event.message
                        if reply.text_original.startswith('我猜'):
                            if reply.text_original[2:] == '':
                                continue
                            if reply.text_original[2:] == response['md']:
                                event.close_event()
                                await data.send(
                                    Chain(reply, at=False).text(f'回答正确！答案是：{response["md"]}, 获得600合成玉'))
                                UserInfo.add_jade_point(reply.user_id, 600, 30000)
                                return
                            else:
                                times += 1
                                flag = True
                                continue
                        elif reply.text_original.startswith('提示'):
                            if not tip:
                                await data.send(Chain(reply, at=False).text(f'提示：{response["ts"]}'))
                                tip = True
                            else:
                                await data.send(Chain(reply, at=False).text(f'已经提示过了哦'))
                        elif reply.text_original.startswith('结束'):
                            break
                        else:
                            continue
                    else:
                        await data.send(Chain(reply if reply else data, at=False).text(
                            f'没有博士回答吗，那游戏结束咯，正确答案是：{response["da"]}'))
                event.close_event()
                await data.send(Chain(reply, at=False).text(f'游戏结束，正确答案是：{response["md"]}'))
            else:
                await data.send(Chain(data, at=False).text('谜题获取失败，请稍后再试'))
        except Exception:
            await data.send(Chain(data, at=False).text('谜题获取失败，请稍后再试'))
    return


# 扫雷
@bot.on_message(keywords=['扫雷'], allow_direct=False, level=5)
async def sweep_mine(data: Message):
    mode = "简单"
    # 难度设置
    settings = [9, 9, 10, 5]
    if '简单' in data.text_original:
        pass
    elif '中等' in data.text_original:
        settings = [16, 16, 40, 20]
        mode = "中等"
    elif '困难' in data.text_original:
        settings = [30, 16, 99, 60]
        mode = "困难"
    else:
        pattern = re.compile(r'^\D*(\d+)[×xX*](\d+)\D+(\d+)\D+(\d+)\D*$')
        m = pattern.match(data.text_original)
        if m:
            settings = [int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))]
            mode = "自定义"
    if settings[0] < 9 or settings[1] < 9:
        return Chain(data).text('地图太小啦(> _ <)! 最小为9×9')
    if settings[0] > 50 or settings[1] > 50:
        return Chain(data).text('地图太大啦(> _ <)! 最大为50×50')
    if settings[2] < 10:
        return Chain(data).text('雷太少啦(> _ <)! 最少为10个')
    if settings[2] > settings[0] * settings[1] - 1:
        return Chain(data).text('雷太多啦(> _ <)! 最多为地图格子数-1')
    if settings[3] < 5:
        return Chain(data).text('时间太短啦(> _ <)! 最短为5分钟')
    if settings[3] > 360:
        return Chain(data).text('时间太长啦(> _ <)! 最长为6小时')
    width = settings[0] * 36.4 + 40
    height = settings[1] * 36.4 + 40
    # 生成地图
    map_ = [[0 for _ in range(settings[0])] for _ in range(settings[1])]
    for _ in range(settings[2]):
        while True:
            x = random.randint(0, settings[0] - 1)
            y = random.randint(0, settings[1] - 1)
            if map_[y][x] == 0:
                map_[y][x] = 9
                break
    for y in range(settings[1]):
        for x in range(settings[0]):
            if map_[y][x] == 9:
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if 0 <= y + i < settings[1] and 0 <= x + j < settings[0] and map_[y + i][x + j] != 9:
                            map_[y + i][x + j] += 1
    # 游戏开始
    game = [[-1 for _ in range(settings[0])] for _ in range(settings[1])]
    start_time = time.time()
    end_time = start_time + settings[3] * 60
    await data.send(
        Chain(data).text(f'扫雷游戏开始, 难度: {mode}, 共计有 {settings[2]} 颗地雷, 限时: {settings[3]}分钟'))
    check = True
    sum_ = 0
    while True:
        await asyncio.sleep(0)
        if check:
            event = await data.wait_channel(
                Chain(data, at=False).text(f'剩余格数: {settings[0] * settings[1] - sum_}').html(
                    f'{curr_dir}/template/html/winmine.html', {'map': game}, math.ceil(width),
                    math.ceil(height)), True, True, int(end_time - time.time()))
            check = False
        else:
            event = await data.wait_channel(max_time=int(end_time - time.time()))
        try:
            if event:
                reply = event.message
                pattern = re.compile(r'^(\d+)\D+(\d+)$')
                m = pattern.match(reply.text_original)
                if m:
                    row = int(m.group(1))
                    col = int(m.group(2))
                    if 0 <= row < settings[1] and 0 <= col < settings[0]:
                        if game[row][col] == -1:
                            if map_[row][col] == 9:
                                event.close_event()
                                await data.send(Chain(reply, at=False).text('你踩到雷了, 游戏结束!').html(
                                    f'{curr_dir}/template/html/winmine.html', {'map': map_}, math.ceil(width),
                                    math.ceil(height)))
                                return
                            # 递归打开格子及周围的空白格子
                            else:
                                check = True
                                flag = [[0 for _ in range(settings[0])] for _ in range(settings[1])]

                                def open_blank(row_, col_, first=False):
                                    flag[row_][col_] = 1
                                    if (game[row_][col_] == -1 or game[row_][col_] == 10) and map_[row_][col_] != 9:
                                        game[row_][col_] = map_[row_][col_]
                                    for i_ in range(-1, 2):
                                        for j_ in range(-1, 2):
                                            if settings[1] > row_ + i_ >= 0 and 0 <= col_ + j_ < settings[0] and \
                                                flag[row_ + i_][col_ + j_] == 0:
                                                if map_[row_][col_] == 0 or (map_[row_][col_] != 9 and map_[row_ + i_][
                                                    col_ + j_] == 0 and first):
                                                    open_blank(row_ + i_, col_ + j_)

                                open_blank(row, col, True)
                            # 判断是否胜利
                            sum_ = 0
                            for y in range(settings[1]):
                                for x in range(settings[0]):
                                    if 0 <= game[y][x] <= 8:
                                        sum_ += 1
                            if sum_ == settings[1] * settings[0] - settings[2]:
                                event.close_event()
                                await data.send(Chain(reply, at=False).text('恭喜你, 你赢了!').html(
                                    f'{curr_dir}/template/html/winmine.html', {'map': map_}, math.ceil(width),
                                    math.ceil(height)))
                                return
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                elif reply.text_original.startswith(('f', 'F', '旗', 'flag', 'Flag', 'FLAG')):
                    pattern = re.compile(r'^.*?(\d+)\D+(\d+)$')
                    m = pattern.match(reply.text_original)
                    if m:
                        row = int(m.group(1))
                        col = int(m.group(2))
                        if 0 <= row < settings[1] and 0 <= col < settings[0]:
                            check = True
                            if game[row][col] == -1:
                                game[row][col] = 10
                            elif game[row][col] == 10:
                                game[row][col] = -1
                            else:
                                continue
                            # 判断是否胜利
                            sum_ = 0
                            for y in range(settings[1]):
                                for x in range(settings[0]):
                                    if 0 <= game[y][x] <= 8:
                                        sum_ += 1
                            if sum_ == settings[1] * settings[0] - settings[2]:
                                event.close_event()
                                await data.send(Chain(reply, at=False).text('恭喜你, 你赢了!').html(
                                    f'{curr_dir}/template/html/winmine.html', {'map': map_}, math.ceil(width),
                                    math.ceil(height)))
                                return
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                elif reply.text_original.startswith(('退出', 'quit', 'Quit', 'QUIT')):
                    event.close_event()
                    await data.send(Chain(reply, at=False).text('游戏退出'))
                    return
                else:
                    continue
            else:
                await data.send(Chain(data).text('时间到, 游戏结束!'))
                return
        except Exception:
            traceback.print_exc()
            if event:
                event.close_event()
            await data.send(Chain(data).text('发生错误，游戏结束!'))
            return


# 五子棋
@bot.on_message(keywords=['五子棋'], allow_direct=False, level=5)
async def gomoku(data: Message):
    async def gomoku_filter1(data_: Message):
        return data_.text_original == '加入'
    time_limit = time.time() + 60
    event = await data.wait_channel(Chain(data).text('发起了一局五子棋对局, 请黑方在60s内输入"加入"加入对局'), True,
                                    True, int(time_limit - time.time()), gomoku_filter1)
    if not event:
        return Chain(data, at=False).text('游戏超时取消')
    reply = event.message
    avatar = ''
    if reply.avatar:
        avatar = await download_async(reply.avatar)
    # 写入文件
    player1 = reply.user_id
    img1 = f'player{player1}.jpg'
    file_path1 = f'{curr_dir}/template/resource/avatar/{img1}'
    file = create_file(file_path1, 'wb')
    file.write(avatar)
    file.close()
    img1 = f'../resource/avatar/{img1}'
    name1 = reply.nickname
    time_limit = time.time() + 60
    event = await data.wait_channel(Chain(data, at=False).text('请白方在60s内输入"加入"加入对局'), True, True,
                                    int(time_limit - time.time()), gomoku_filter1)
    if not event:
        remove_file(file_path1)
        return Chain(data, at=False).text('游戏超时取消')
    reply = event.message
    avatar = ''
    if reply.avatar:
        avatar = await download_async(reply.avatar)
    # 写入文件
    player2 = reply.user_id
    img2 = f'player{player2}.jpg'
    file_path2 = f'{curr_dir}/template/resource/avatar/{img2}'
    file = create_file(file_path2, 'wb')
    file.write(avatar)
    file.close()
    img2 = f'../resource/avatar/{img2}'
    name2 = reply.nickname
    await data.send(Chain(data, at=False).text('游戏开始!'))
    chess = [['' for _ in range(15)] for _ in range(15)]
    flag = 'black'
    pattern = re.compile(r'^(\d+)\D+(\d+)$')

    async def gomoku_filter2(data_: Message):
        if flag == 'black':
            return data_.user_id == player1 and (pattern.match(data_.text_original)) or data_.text_original == '退出'
        else:
            return data_.user_id == player2 and (pattern.match(data_.text_original)) or data_.text_original == '退出'

    while True:
        info = {
            'avatar': img1 if flag == 'black' else img2,
            'player': name1 if flag == 'black' else name2,
            'chessColor': flag,
            'chessMap': chess
        }
        if flag == 'black':
            event = await data.wait_channel(
                Chain(data, at=False).html(f'{curr_dir}/template/html/gomoku.html', info, 550, 626), True, True, 600,
                gomoku_filter2)
        else:
            event = await data.wait_channel(
                Chain(data, at=False).html(f'{curr_dir}/template/html/gomoku.html', info, 550, 626), True, True, 600,
                gomoku_filter2)
        if not event:
            remove_file(file_path1)
            remove_file(file_path2)
            return Chain(data, at=False).text('游戏超时取消')
        reply = event.message
        if reply.text_original == '退出':
            event.close_event()
            remove_file(file_path1)
            remove_file(file_path2)
            await data.send(Chain(data, at=False).text('游戏退出'))
            return
        m = pattern.match(reply.text_original)
        row = int(m.group(1))
        col = int(m.group(2))
        if 0 <= row <= 14 and 0 <= col <= 14:
            if chess[row][col] == '':
                chess[row][col] = flag
                # 判断是否胜利
                for i in range(row - 4, row + 5):
                    if 0 <= i <= 10:
                        if chess[i][col] == flag:
                            check = True
                            for j in range(1, 5):
                                if chess[i + j][col] != flag:
                                    check = False
                                    break
                            if check:
                                event.close_event()
                                remove_file(file_path1)
                                remove_file(file_path2)
                                await data.send(Chain(data, at=False).text(f'{name1 if flag == "black" else name2} 赢了!'))
                for i in range(col - 4, col + 5):
                    if 0 <= i <= 10:
                        if chess[row][i] == flag:
                            check = True
                            for j in range(1, 5):
                                if chess[row][i + j] != flag:
                                    check = False
                                    break
                            if check:
                                event.close_event()
                                remove_file(file_path1)
                                remove_file(file_path2)
                                await data.send(Chain(data, at=False).text(f'{name1 if flag == "black" else name2} 赢了!'))
                                return
                for i in range(-4, 5):
                    if 0 <= row + i <= 10 and 0 <= col + i <= 10:
                        if chess[row + i][col + i] == flag:
                            check = True
                            for j in range(1, 5):
                                if chess[row + i + j][col + i + j] != flag:
                                    check = False
                                    break
                            if check:
                                event.close_event()
                                remove_file(file_path1)
                                remove_file(file_path2)
                                await data.send(Chain(data, at=False).text(f'{name1 if flag == "black" else name2} 赢了!'))
                                return
                for i in range(-4, 5):
                    if 0 <= row + i <= 10 and 0 <= col - i <= 10:
                        if chess[row + i][col - i] == flag:
                            check = True
                            for j in range(1, 5):
                                if chess[row + i + j][col - i - j] != flag:
                                    check = False
                                    break
                            if check:
                                event.close_event()
                                remove_file(file_path1)
                                remove_file(file_path2)
                                await data.send(Chain(data, at=False).text(f'{name1 if flag == "black" else name2} 赢了!'))
                                return
                flag = 'black' if flag == 'white' else 'white'
            else:
                await data.send(Chain(data, at=False).text('该位置已有棋子, 请重新输入'))
        else:
            await data.send(Chain(data, at=False).text('输入坐标超出范围, 请重新输入'))


# 修改群名片&群头衔
@bot.on_message(keywords=['修改群名片'], allow_direct=False, level=5)
async def set_group_card(data: Message):
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        msg = data.text_original.split(' ')
        if msg.__len__() == 1:
            return Chain(data).text('请输入新的群名片')
        elif msg.__len__() > 2:
            return Chain(data).text('群名片不能有空格')
        new_card = msg[1]
        at_member = data.at_target
        if at_member.__len__() == 0:
            target = data.instance.appid
        elif at_member.__len__() == 1:
            target = at_member[0]
        else:
            return Chain(data).text('请不要@多个人')
        group = data.channel_id
        res = False
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            res = await mirai.set_group_card(group, int(target), new_card)
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            res = await gocq.set_group_card(group, int(target), new_card)
        if res:
            return Chain(data).text('修改成功')
        else:
            return Chain(data).text('修改失败, 请检查兔兔权限和昵称是否符合QQ规则')
    else:
        return Chain(data).text('权限不足')


@bot.on_message(keywords=['修改群头衔'], allow_direct=False, level=5)
async def set_group_special_title(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    flag = 'deny'
    if bool(Admin.get_or_none(account=data.user_id)):
        flag = 'super'
    elif data.is_admin and config_['specialTitle']['admin']:
        flag = 'admin'
    elif config_['specialTitle']['guest']:
        flag = 'guest'
    if flag == 'deny':
        return Chain(data).text('权限不足')
    if flag == 'guest':
        if get_cooldown(f'{data.channel_id}-{data.user_id}', special_title_cd) == 1:
            return Chain(data).text('请勿频繁使用')
        set_cooldown(f'{data.channel_id}-{data.user_id}', special_title_cd, config_['specialTitle']['cd'])
    msg = data.text_original.split(' ')
    if msg.__len__() == 1:
        return Chain(data).text('请输入新的群头衔')
    elif msg.__len__() > 2:
        return Chain(data).text('群头衔不能有空格')
    new_title = msg[1]
    at_member = data.at_target
    if at_member.__len__() > 1:
        return Chain(data).text('请不要@多个人')
    elif at_member.__len__() == 1:
        if at_member[0] == data.user_id:
            target = data.user_id
        else:
            target = at_member[0]
    else:
        target = data.user_id
    target = int(target)
    group = data.channel_id
    res = False
    if type(data.instance) is MiraiBotInstance:
        mirai = MiraiTools(data.instance, data=data)
        res = await mirai.set_group_special_title(group, target, new_title)
    if type(data.instance) is CQHttpBotInstance:
        gocq = GOCQTools(data.instance, data=data)
        res = await gocq.set_group_special_title(group, target, new_title)
    if res:
        return Chain(data).text('修改成功')
    else:
        return Chain(data).text('修改失败, 请检查兔兔权限和头衔是否符合QQ规则')


# 撤回消息
@bot.on_message(keywords=['撤回'], allow_direct=True, level=5)
async def recall(data: Message):
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        if type(data.instance) is MiraiBotInstance:
            info = data.message['messageChain']
            for i in info:
                if i['type'] == 'Quote':
                    mirai = MiraiTools(data.instance, data=data)
                    await mirai.recall(i)
        if type(data.instance) is CQHttpBotInstance:
            info = data.message['message']
            for i in info:
                if i['type'] == 'reply':
                    gocq = GOCQTools(data.instance, data=data)
                    await gocq.recall(i)
    return


# 群欢迎消息
@bot.on_message(keywords=['设置欢迎消息'], allow_direct=False, level=5)
async def set_welcome(data: Message):
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        try:
            welcome = data.text_original.split(' ', 1)[1]
            await SQLHelper.set_welcome(data.instance.appid, data.channel_id, welcome)
            return Chain(data).text('欢迎消息设置成功')
        except IndexError:
            return Chain(data).text('请输入欢迎消息')
    return Chain(data).text('权限不足')


@bot.on_message(keywords=['清除欢迎消息'], allow_direct=False, level=5)
async def clear_welcome(data: Message):
    if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
        await SQLHelper.delete_welcome(data.instance.appid, data.channel_id)
        return Chain(data).text('欢迎消息已清除')
    return Chain(data).text('权限不足')


@bot.on_event('MemberJoinEvent')  # Mirai群成员入群
async def member_join(event: Event, instance: MiraiBotInstance):
    message = await SQLHelper.get_welcome(instance.appid, event.data['member']['group']['id'])
    if message is not None:
        await instance.send_message(Chain().at(str(event.data['member']['id']), True).text(message.message),
                                    channel_id=str(event.data['member']['group']['id']))
    return


@bot.on_event('notice.group_increase')  # GOCQ群成员入群
async def member_join(event: Event, instance: CQHttpBotInstance):
    message = await SQLHelper.get_welcome(instance.appid, event.data['group_id'])
    if message is not None:
        await instance.send_message(Chain().at(str(event.data['user_id']), True).text(message.message),
                                    channel_id=str(event.data['group_id']))
    return


# 重启
@bot.on_message(keywords=['重启'], direct_only=True, level=5)
async def restart(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    if config_.get('restart') is not None and int(data.user_id) in config_['restart']:
        await data.send(Chain(data, at=False).text('重启中...'))
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        return Chain(data).text('权限不足')


async def check_restart(t: int):
    if t > 10:
        return True
    else:
        return False


# noinspection PyUnusedLocal
@bot.timed_task(custom=check_restart, sub_tag='tools-restart')
async def restart_task(instance: BotHandlerFactory):
    bot.remove_timed_task('tools-restart')
    config_ = read_yaml(config_file, _dict=True)
    if config_.get('restart') is not None:
        for i in config_['restart']:
            for j in main_bot:
                await j.send_message(Chain().text('兔兔启动成功或小工具插件安装成功！'), str(i))

    return


# 好友申请
@bot.on_event('NewFriendRequestEvent')  # Mirai新好友申请
async def new_friend_request(event: Event, instance: MiraiBotInstance):
    config_ = read_yaml(config_file, _dict=True)
    operator = config_['operator']
    if operator is None:
        return
    mirai = MiraiTools(instance, event=event)
    await mirai.new_friend_request(operator)
    await SQLHelper.add_friend(instance.appid, 'mirai', event_id=event.data['eventId'], from_id=event.data['fromId'],
                               group_id=event.data['groupId'], nick=event.data['nick'], message=event.data['message'])
    return


@bot.on_event('request.friend')  # GOCQ新好友申请
async def new_friend_request(event: Event, instance: CQHttpBotInstance):
    config_ = read_yaml(config_file, _dict=True)
    operator = config_['operator']
    if operator is None:
        return
    gocq = GOCQTools(instance, event=event)
    await gocq.new_friend_request(operator)
    await SQLHelper.add_friend(instance.appid, 'gocq', flag=event.data['flag'], user_id=event.data['user_id'],
                               comment=event.data['comment'])
    return


@bot.on_message(keywords=['同意好友', '拒绝好友', '拉黑好友'], direct_only=True, level=5)
async def new_friend_request(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    if data.text_original.startswith('兔兔'):
        data.text_original = data.text_original.replace('兔兔', '', 1)
    elif data.text_original.startswith('阿米娅'):
        data.text_original = data.text_original.replace('阿米娅', '', 1)
    elif data.text_original.startswith('Amiya'):
        data.text_original = data.text_original.replace('Amiya', '', 1)
    elif data.text_original.startswith('amiya'):
        data.text_original = data.text_original.replace('amiya', '', 1)
    if config_.get('operator') is not None and int(data.user_id) == config_['operator']:
        msg = data.text_original.split(' ')
        flag = False
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入QQ号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_friend(data.instance.appid, 'mirai', msg[1])
                if info is None:
                    return Chain(data).text('该好友申请不存在')
            if msg[0] == '同意好友':
                if len(msg) == 2:
                    flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 0)
                else:
                    text = ' '.join(msg[2:])
                    flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 0, text)
            elif msg[0] == '拒绝好友':
                flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 1)
            elif msg[0] == '拉黑好友':
                flag = await mirai.new_friend_request_handle(info.event_id, info.from_id, info.group_id, 2)
            else:
                return Chain(data).text('请输入正确的指令')
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入QQ号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_friend(data.instance.appid, 'gocq', msg[1])
                if info is None:
                    return Chain(data).text('该好友请求不存在')
            if msg[0] == '同意好友':
                if len(msg) == 2:
                    flag = await gocq.new_friend_request_handle(info.flag, True)
                else:
                    flag = await gocq.new_friend_request_handle(info.flag, True, msg[2])
            elif msg[0] == '拒绝好友':
                flag = gocq.new_friend_request_handle(info.flag, False)
            else:
                return Chain(data).text('请输入正确的指令')
        if flag:
            await SQLHelper.delete_friend(data.instance.appid, msg[1])
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


@bot.on_message(keywords=['查看好友申请'], direct_only=True, level=5)
async def view_new_friends(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    if config_.get('operator') is not None and int(data.user_id) == config_['operator']:
        if type(data.instance) is MiraiBotInstance:
            info = await SQLHelper.get_friends(data.instance.appid, 'mirai')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无好友申请')
            else:
                msg = '好友申请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. QQ号: {i.from_id} 申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意好友 [QQ号] ([回复信息])"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求\n发送"兔兔拉黑好友 [QQ号]"以拉黑请求'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'QQ号: {info[id_ - 1].from_id}\n昵称: {info[id_ - 1].nick}\n申请信息: {info[id_ - 1].message}\n申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break
        if type(data.instance) is CQHttpBotInstance:
            info = await SQLHelper.get_friends(data.instance.appid, 'gocq')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无好友申请')
            else:
                msg = '好友申请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. QQ号: {i.user_id} 申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意好友 [QQ号] ([好友备注])"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'QQ号: {info[id_ - 1].user_id}\n申请信息: {info[id_ - 1].comment}\n申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break
    return


@bot.on_message(keywords=['清空好友申请'], allow_direct=True, level=5)
async def clear_new_friends(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    if config_.get('operator') is not None and int(data.user_id) == config_['operator']:
        res = False
        if type(data.instance) is MiraiBotInstance:
            res = await SQLHelper.delete_friends(data.instance.appid, 'mirai')
        if type(data.instance) is CQHttpBotInstance:
            res = await SQLHelper.delete_friends(data.instance.appid, 'gocq')
        if res:
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


# 群聊邀请
@bot.on_event('BotInvitedJoinGroupRequestEvent')  # Mirai群聊邀请
async def group_invite(event: Event, instance: MiraiBotInstance):
    config_ = read_yaml(config_file, _dict=True)
    operator = config_['operator']
    if operator is None:
        return
    mirai = MiraiTools(instance, event=event)
    await mirai.group_invite(operator)
    await SQLHelper.add_invite(instance.appid, 'mirai', event.data['groupId'], event_id=event.data['eventId'],
                               from_id=event.data['fromId'], group_name=event.data['groupName'],
                               nick=event.data['nick'], message=event.data['message'])
    return


@bot.on_event('request.group.invite')  # GOCQ群聊邀请
async def group_invite(event: Event, instance: CQHttpBotInstance):
    config_ = read_yaml(config_file, _dict=True)
    operator = config_['operator']
    if operator is None:
        return
    gocq = GOCQTools(instance, event=event)
    await gocq.group_invite(operator)
    await SQLHelper.add_invite(instance.appid, 'gocq', event.data['group_id'], flag=event.data['flag'],
                               user_id=event.data['user_id'], comment=event.data['comment'])


@bot.on_message(keywords=['同意邀请', '拒绝邀请'], allow_direct=True, level=5)
async def group_invite(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    if data.text_original.startswith('兔兔'):
        data.text_original = data.text_original.replace('兔兔', '', 1)
    elif data.text_original.startswith('阿米娅'):
        data.text_original = data.text_original.replace('阿米娅', '', 1)
    elif data.text_original.startswith('Amiya'):
        data.text_original = data.text_original.replace('Amiya', '', 1)
    elif data.text_original.startswith('amiya'):
        data.text_original = data.text_original.replace('amiya', '', 1)
    if config_.get('operator') is not None and int(data.user_id) == config_['operator']:
        msg = data.text_original.split(' ')
        flag = False
        if type(data.instance) is MiraiBotInstance:
            mirai = MiraiTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入群号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_invite(data.instance.appid, 'mirai', msg[1])
                if info is None:
                    return Chain(data).text('该群聊邀请不存在')
            if msg[0] == '同意邀请':
                if len(msg) == 2:
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 0)
                else:
                    text = ' '.join(msg[2:])
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 0, text)
            elif msg[0] == '拒绝邀请':
                if len(msg) == 2:
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 1)
                else:
                    text = ' '.join(msg[2:])
                    flag = await mirai.group_invite_handle(info.event_id, info.from_id, info.group_id, 1, text)
            else:
                return Chain(data).text('请输入正确的指令')
        if type(data.instance) is CQHttpBotInstance:
            gocq = GOCQTools(data.instance, data=data)
            if len(msg) == 1:
                return Chain(data).text('请输入群号, 注意空格')
            else:
                msg[1] = int(msg[1])
                info = await SQLHelper.get_invite(data.instance.appid, 'gocq', msg[1])
                if info is None:
                    return Chain(data).text('该群聊邀请不存在')
            if msg[0] == '同意邀请':
                flag = await gocq.group_invite_handle(info.flag, True)
            elif msg[0] == '拒绝邀请':
                if len(msg) == 2:
                    flag = await gocq.group_invite_handle(info.flag, True)
                else:
                    text = ' '.join(msg[2:])
                    flag = await gocq.group_invite_handle(info.flag, True, text)
            else:
                return Chain(data).text('请输入正确的指令')
        if flag:
            await SQLHelper.delete_invite(data.instance.appid, msg[1])
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


@bot.on_message(keywords=['查看邀请'], allow_direct=True, level=5)
async def view_group_invites(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    if config_.get('operator') is not None and int(data.user_id) == config_['operator']:
        if type(data.instance) is MiraiBotInstance:
            info = await SQLHelper.get_invites(data.instance.appid, 'mirai')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无群聊邀请')
            else:
                msg = '群聊邀请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. 群号: {i.group_id} 邀请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意邀请 [群号] [回复消息]"以同意邀请\n发送"兔兔拒绝邀请 [群号] [回复消息]"以拒绝邀请'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'邀请人: {info[id_ - 1].nick}\n邀请人QQ: {info[id_ - 1].from_id}\n群聊: {info[id_ - 1].group_name}\n群号: {info[id_ - 1].group_id}\n邀请信息: {info[id_ - 1].message}\n邀请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break
        if type(data.instance) is CQHttpBotInstance:
            info = await SQLHelper.get_invites(data.instance.appid, 'gocq')
            if info is None or len(info) == 0:
                return Chain(data).text('暂无群聊邀请')
            else:
                msg = '群聊邀请列表:\n'
                j = 1
                for i in info:
                    msg += f'{j}. 群号: {i.group_id} 邀请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.date))}\n'
                    j += 1
                msg += '回复 [序号] 查看申请信息\n发送"兔兔同意好友 [QQ号] ([好友备注])"以同意请求\n发送"兔兔拒绝好友 [QQ号]"以拒绝请求'
                while True:
                    reply = await data.wait(Chain(data).text(msg))
                    if reply:
                        try:
                            id_ = int(reply.text_original)
                        except ValueError:
                            break
                        if id_ > len(info):
                            break
                        else:
                            msg = f'邀请人QQ: {info[id_ - 1].user_id}\n群号: {info[id_ - 1].group_id}\n申请时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info[id_ - 1].date))}'
                    else:
                        break
    return


@bot.on_message(keywords=['清空邀请'], allow_direct=True, level=5)
async def clear_new_friends(data: Message):
    config_ = read_yaml(config_file, _dict=True)
    if config_.get('operator') is not None and int(data.user_id) == config_['operator']:
        res = False
        if type(data.instance) is MiraiBotInstance:
            res = await SQLHelper.delete_invites(data.instance.appid, 'mirai')
        if type(data.instance) is CQHttpBotInstance:
            res = await SQLHelper.delete_invites(data.instance.appid, 'gocq')
        if res:
            return Chain(data).text('操作成功')
        else:
            return Chain(data).text('操作失败')
    else:
        return Chain(data).text('权限不足')


async def verify_gacha(data: Message):
    if '更新卡池图片' in data.text_original:
        return True, 5
    else:
        return False, 0


@bot.on_message(verify=verify_gacha, direct_only=True)
async def update_gacha_pool(data: Message):
    if bool(Admin.get_or_none(account=data.user_id)):
        await data.send(Chain(data).text('开始更新卡池图片...'))
        git_path = 'resource/plugins/gacha/pool'
        git_url = 'https://gitlab.com/wutongshufqw/arknights-pool.git'
        GitAutomation(git_path, git_url).update()
        await data.send(Chain(data).text('更新完成'))


# 撤回控制
# noinspection PyUnusedLocal
@bot.timed_task(each=1)
async def _(instance: BotHandlerFactory):
    for recall_ in recall_list:
        if recall_.__contains__('res') and recall_.__contains__('time'):
            r = recall_['res']
            t = recall_['time']
            cur = time.time()
            if r and cur > t:
                await r.recall()
                recall_list.remove(recall_)
