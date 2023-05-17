import asyncio
import datetime
import json
import os
import random
import re
import time
from io import BytesIO
from typing import Union, Dict

from amiyabot import MiraiBotInstance, CQHttpBotInstance, Event, Chain, Message, Equal
from amiyabot.adapters.cqhttp import CQHTTPForwardMessage
from amiyabot.adapters.mirai import MiraiForwardMessage
from amiyabot.network.download import download_async
from amiyabot.network.httpRequests import http_requests
from core import log
from lxml import etree

from core import read_yaml, Admin
from core.database.user import UserInfo, UserGachaInfo
from .main import bot, tool_is_close, get_cooldown, set_cooldown, recall_list, download_avatar
from ..api import GOCQTools, MiraiTools
from ..config import poke_message_send, request_headers, get_url
from ..utils import SQLHelper, convert, get_saucenao, Waifu, Caiyun

poke_cd = {}
BROWSER = 0


async def poke_helper(instance: Union[MiraiBotInstance, CQHttpBotInstance], event: Event, config_: dict):
    api = MiraiTools(instance, event=event) if type(instance) == MiraiBotInstance else GOCQTools(instance, event=event)
    message = Chain()
    data = event.data
    weekday = datetime.datetime.now().weekday() + 1
    if weekday == 4:
        msg = random.choice(config_.get('replies'))
    else:
        while True:
            msg = random.choice(config_.get('replies'))
            if msg.find('[crazy]') == -1:
                break
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
                    await poke_message_send(message, event, instance)
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
                message = Chain().at(data['fromId'] if type(instance) == MiraiBotInstance else data['user_id']).text(
                    '\n标题：' + img_name + '\n作者：' + img_author + '\nPID：' + str(img_pid)).image(img)
                await poke_message_send(message, event, instance)
            elif m0[i] == '[poke]':
                if flag:
                    await poke_message_send(message, event, instance)
                    flag = False
                await api.poke(event)
            elif m0[i].startswith('[face'):
                if not flag:
                    message = Chain()
                    flag = True
                id_ = int(m0[i].split(' ')[1].split(']')[0])
                message = message.face(id_)
            elif m0[i] == '[emoji]':
                if not flag:
                    message = Chain()
                    flag = True
                image_path = config_.get('emojiPath')
                image_list = os.listdir(image_path)
                if len(image_list) == 0:
                    continue
                image = random.choice(image_list)
                image = f'{os.path.dirname(__file__)}/../../{image_path}/{image}'
                message = message.image(image)
            elif m0[i] == '[crazy]':
                crazy = read_yaml(f'{os.path.dirname(__file__)}/crazy.yaml', _dict=True)
                if not flag:
                    message = Chain()
                    flag = True
                message = message.text(random.choice(crazy['crazy']))
            else:
                if not flag:
                    message = Chain()
                    flag = True
                message = message.text(m0[i])
    if flag:
        await poke_message_send(message, event, instance)
    return


# 戳一戳
@bot.on_event('NudgeEvent')  # Mirai戳一戳
async def poke(event: Event, instance: MiraiBotInstance):
    channel_id = event.data['subject']['id'] if event.data['subject']['kind'] == 'Group' else None
    if await tool_is_close(instance.appid, 1, 1, 1, channel_id):
        return
    config_ = bot.get_config('poke')
    if int(instance.appid) == event.data['target'] and config_.get('cd') >= 0:
        if get_cooldown(event.data['subject']['id'], poke_cd) == 1:
            return
        set_cooldown(event.data['subject']['id'], poke_cd, config_.get('cd'))
        await poke_helper(instance, event, config_)


@bot.on_event('notice.notify.poke')  # gocq戳一戳
async def poke(event: Event, instance: CQHttpBotInstance):
    channel_id = event.data.get('group_id')
    if await tool_is_close(instance.appid, 1, 1, 1, channel_id):
        return
    config_ = bot.get_config('poke')
    if int(instance.appid) == event.data['target_id'] and config_.get('cd') >= 0:
        if 'group_id' in event.data:
            if get_cooldown(event.data['group_id'], poke_cd) == 1:
                return
            set_cooldown(event.data['group_id'], poke_cd, config_.get('cd'))
        else:
            if get_cooldown(event.data['sender_id'], poke_cd) == 1:
                return
            set_cooldown(event.data['sender_id'], poke_cd, config_.get('cd'))
        await poke_helper(instance, event, config_)


# 今天吃什么
@bot.on_message(keywords=['今天吃什么'], allow_direct=True, level=5)
async def eat(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 2, data.channel_id):
        return
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
    if await tool_is_close(data.instance.appid, 1, 1, 3, data.channel_id):
        return
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
    if await tool_is_close(data.instance.appid, 1, 1, 3, data.channel_id):
        return False, -1, False
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
    if await tool_is_close(data.instance.appid, 1, 1, 4, data.channel_id):
        return
    if data.image.__len__() == 0:
        return Chain(data).text('请发送图片')
    elif data.image.__len__() > 1:
        return Chain(data).text('只能发送一张图片>_<')
    else:
        config_ = bot.get_config('sauceNAO')
        if config_.get('api_key') == 'your api key':
            return Chain(data).text('请先配置SauceNAO的API Key')
        flag, tip, json_ = await get_saucenao(data.image[0], config_.get('api_key'),
                                              config_.get('proxy'))
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
    if await tool_is_close(data.instance.appid, 1, 1, 5, data.channel_id):
        return
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
    if await tool_is_close(data.instance.appid, 1, 1, 5, data.channel_id):
        return
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
    if await tool_is_close(data.instance.appid, 1, 1, 6, data.channel_id):
        return
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


# 抽奖
@bot.on_message(keywords=['抽奖'], allow_direct=False, level=5)
async def lottery(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 7, data.channel_id):
        return
    config_ = bot.get_config('lottery')
    if config_ is not None:
        day = config_.get('day')
        times = config_.get('times')
        coupon = config_.get('coupon')
        probability = config_.get('probability')
        lottery_ = await SQLHelper.get_lottery(data.instance.appid, data.channel_id)
        last_date = lottery_.date if lottery_.date else None
        minus = float('inf') if last_date is None else (datetime.date.today() - last_date).days
        # 计算剩余次数
        if minus >= day:  # 更新抽奖周期
            left = times
            flag = True
        else:  # 不更新抽奖周期
            left = times - lottery_.times if lottery_.times else times
            flag = False
        if left > 0:
            if random.random() <= probability:
                if flag:
                    await SQLHelper.set_lottery(lottery_.id, 1, datetime.date.today())
                else:
                    await SQLHelper.set_lottery(lottery_.id, lottery_.times + 1)
                UserGachaInfo.get_or_create(user_id=data.user_id)
                UserGachaInfo.update(
                    coupon=UserGachaInfo.coupon + coupon
                ).where(UserGachaInfo.user_id == data.user_id).execute()
                return Chain(data).text(f'恭喜{data.nickname}获得了{coupon}寻访凭证！')
            else:
                return Chain(data).text(f'很遗憾，{data.nickname}没有抽中奖品！')
        else:
            return Chain(data, at=False).text(f'该周期中奖名额已满，下次再来吧！')
    return


# 今日老婆
@bot.on_message(keywords=[Equal('群友老婆'), Equal('qylp')], allow_direct=False, level=5)
async def today_wife(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 9, data.channel_id):
        return
    wife = await SQLHelper.get_today_wife(int(data.instance.appid), int(data.channel_id), int(data.user_id))
    if wife:
        try:
            avatar = await download_avatar(str(wife.wife_id))
            return Chain(data).text('今天已经娶过群友老婆了哦，你的今日老婆是').image(avatar).text(
                f'{wife.nickname}({wife.wife_id})')
        except Exception:
            return Chain(data).text('今天已经娶过群友老婆了哦，你的今日老婆是').text(f'{wife.nickname}({wife.wife_id})')
    else:
        helper = MiraiTools(data.instance) if type(data.instance) == MiraiBotInstance else GOCQTools(data.instance) \
            if type(data.instance) == CQHttpBotInstance else None
        if helper:
            group_member_list = await helper.get_group_member_list(int(data.channel_id))
            if group_member_list:
                while True:
                    wife = random.choice(group_member_list)
                    wife_id = wife.get('user_id') or wife.get('id')
                    if int(wife_id) != int(data.user_id):
                        break
                nickname = wife.get('card') or wife.get('nickname') or wife.get('memberName')
                await SQLHelper.set_today_wife(int(data.instance.appid), int(data.channel_id), int(data.user_id),
                                               int(wife_id), nickname)
                try:
                    avatar = await download_avatar(str(wife_id))
                    return Chain(data).text('你的今日老婆是').image(avatar).text(f'{nickname}({wife_id})')
                except Exception:
                    return Chain(data).text('你的今日老婆是').text(f'{nickname}({wife_id})')
    return


# 今日老婆
@bot.on_message(keywords=['Lab头像生成', '头像生成'], check_prefix=False, allow_direct=True, level=5)
async def today_wife(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 10, data.channel_id):
        return

    async def get_pic(pic_id: str):
        url = f"https://www.thiswaifudoesnotexist.net/example-{pic_id}.jpg"
        res = await download_async(url)
        return BytesIO(res).getvalue()

    if 'Lab' not in data.text_original:
        ran = random.randint(1, 100000)
        img = await get_pic(ran)
        return Chain(data).image(img)
    else:
        config_ = bot.get_config('avatar')
        global BROWSER
        if BROWSER > 5:
            return Chain(data).text('当前进程过多，等一会再来哦~')
        BROWSER += 1
        water = re.match(r'^.*?头像生成\s*?(无水印)?.*$', data.text_original)
        water_mark = True if water and water.group(1) is None else False
        proxy = config_.get('proxy')
        if re.match(
            r'^(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d{2}|2['
            r'0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5]):([0-9]|[1-9]\d|[1-9]\d{2}|[1-9]\d{3}|[1-5]\d{'
            r'4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$', proxy):
            proxy = f'http://{proxy}'
        else:
            proxy = None
        page = Waifu(water_mark=water_mark, proxy=proxy)
        await data.send(Chain(data).text('正在获取中，请稍后...'))
        try:
            stat = await page.gey_browser()
        except Exception as e:
            log.error(e)
            BROWSER -= 1
            return Chain(data).text('获取失败，请稍后再试')
        if not stat:
            BROWSER -= 1
            return Chain(data).text('获取失败，请稍后再试')
        pic = await page.first_shot()

        func_dict = {
            "选择": page.other_shot,
            "继续": page.continues,
            "返回": page.back,
            "退出": page.close,
        }

        async def get_waifu():
            nonlocal pic

            async def my_filter(data_: Message):
                if re.match(r'^(选择|继续|返回|退出)?\s*?(\d+)?$', data_.text_original):
                    return True

            if isinstance(pic, tuple):
                reply = await data.wait(
                    Chain(data).text('获取成功，请选择下一步\n选择[序号]\n继续\n返回\n退出')
                    .image(pic[0].getvalue()).image(pic[1].getvalue()),
                    data_filter=my_filter
                )
            else:
                reply = await data.wait(
                    Chain(data).text('获取成功，请选择下一步\n选择[序号]\n继续\n返回\n退出').image(pic.getvalue()),
                    data_filter=my_filter
                )
            tar = 0
            if reply:
                index = re.match(r'^(选择|继续|返回|退出)?\s*?(\d+)?$', reply.text_original)
                if not index:
                    await data.send(Chain(data).text('输入错误'))
                    return
                if (index.group(1) and index.group(1).startswith('选择')) or index.group(2):
                    if index.group(2):
                        choose = int(index.group(2))
                        if choose not in range(1, 17):
                            await data.send(Chain(data).text('超出选择范围'))
                            return
                        tar = choose
                    else:
                        await data.send(Chain(data).text('未检测到序号'))
                        return
                img_ = func_dict.get(index.group(1) if index.group(1) else '选择', None)
                if tar != 0:
                    pic = await img_(tar)
                else:
                    pic = await img_()
                if not pic:
                    return False
                elif isinstance(pic, tuple):
                    return True
                else:
                    await data.send(Chain(data, at=False).text('获取成功').image(pic.getvalue()))
                    return False
            else:
                return False

        sign = True
        while sign:
            sign = await get_waifu()
        BROWSER -= 1
        return Chain(data, at=False).text('已退出')


@bot.on_message(keywords=['彩云小梦'], check_prefix=False, allow_direct=True, level=5)
async def caiyun_ai(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 11, data.channel_id):
        return

    nums = 0
    caiyun = None

    async def data_filter1(data_: Message):
        if re.match(r'^[1-6]$', data_.text_original):
            return True

    async def data_filter2(data_: Message):
        if re.match(r'^[1-5]$', data_.text_original):
            return True

    async def data_filter3(data_: Message):
        if re.match(r'^\d+$', data_.text_original):
            choose_ = int(data_.text_original)
            if 1 <= choose_ <= nums:
                return True

    while True:
        await asyncio.sleep(0.1)
        reply = await data.wait(
            Chain(data).text('请选择功能\n1.apikey帮助\n2.设置apikey\n3.设置续写模型\n4.开始续写\n5.剧情选择\n6.退出'),
            data_filter=data_filter1, max_time=300)
        if reply:
            choose = int(reply.text_original)
            if choose == 1:
                await data.send(Chain(data)
                                .text("apikey获取教程：\n1、前往 http://if.caiyunai.com/dream 注册彩云小梦用户；\n2、注册完成后，"
                                      "在 chrome 浏览器地址栏输入(或者按下F12在控制台输入) javascript:alert(JSON.parse(localSto"
                                      "rage.getItem('pro_new-dreamily-user')).value)，（前缀javascript也需要复制），弹出窗口中"
                                      "的uid即为apikey")
                                )
            elif choose == 2:
                reply = await data.wait(Chain(reply).text('请输入apikey'))
                if reply:
                    apikey = reply.text_original
                    if re.match(r'^[0-9a-f]{24}$', apikey):
                        int(apikey, base=16)
                        res = await SQLHelper.set_caiyun_apikey(int(data.user_id), apikey)
                        if res:
                            await data.send(Chain(data).text('设置成功'))
                        else:
                            await data.send(Chain(data).text('设置失败'))
                    else:
                        await data.send(Chain(data).text('apikey格式错误'))
                else:
                    continue
            elif choose == 3:
                info = await SQLHelper.get_caiyun_info(int(data.user_id))
                if not info:
                    await data.send(Chain(data).text('请先设置apikey'))
                    continue
                reply = await data.wait(
                    Chain(reply).text('请选择续写模型：\n1.小梦0号\n2.小梦1号\n3.纯爱\n4.言情\n5.玄幻'),
                    data_filter=data_filter2)
                if reply:
                    choose = reply.text_original
                    res = await SQLHelper.set_caiyun_model(int(data.user_id), choose)
                    if res:
                        await data.send(
                            Chain(reply)
                            .text(f'模型已切换为: {Caiyun.model_list().get(choose)["name"]}\n')
                        )
                    else:
                        await data.send(Chain(data).text('设置失败'))
                else:
                    continue
            elif choose == 4:
                res = await SQLHelper.get_caiyun_info(int(data.user_id))
                if not res:
                    await data.send(Chain(reply).text('博士还没有设置apikey哦~'))
                    continue
                reply = await data.wait(Chain(reply).text('请输入续写内容'), max_time=300)
                if reply:
                    caiyun = Caiyun(str(res.apikey), str(res.model))
                    caiyun.content = reply.text_original
                    await data.send(Chain(reply).text('正在续写中，请稍后'))
                    await caiyun.next()
                    new_list = [
                                   "当前续写结果：",
                                   caiyun.content,
                                   "请选择接下来的剧情分支哦~(使用->剧情选择)"
                               ] + [f"{i + 1}.{j}" for i, j in enumerate(caiyun.contents)]
                    nums = len(caiyun.contents)
                    msg = '\n'.join(new_list)
                    await data.send(Chain(data).text(msg))
                else:
                    continue
            elif choose == 5:
                if not caiyun:
                    await data.send(Chain(data).text('请先开始续写哦~'))
                    continue
                reply = await data.wait(Chain(reply).text('请输入剧情序号'), data_filter=data_filter3, max_time=300)
                if reply:
                    if not caiyun:
                        await data.send(Chain(data).text('请先开始续写哦~'))
                        continue
                    choose = int(reply.text_original)
                    caiyun.select(choose - 1)
                    await caiyun.next()
                    new_list = [
                        "当前续写结果：",
                        caiyun.content,
                        "请选择接下来的剧情分支哦~(使用->剧情选择)"
                    ] + [f"{i + 1}.{j}" for i, j in enumerate(caiyun.contents)]
                    nums = len(caiyun.contents)
                    msg = '\n'.join(new_list)
                    await data.send(Chain(reply).text(msg))
            elif choose == 6:
                return Chain(reply).text('已退出')
        else:
            return Chain(data).text('已退出')
