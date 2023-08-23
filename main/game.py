import asyncio
import itertools
import math
import random
import re
import time
import traceback
from io import BytesIO
from typing import List, Optional, Tuple

from amiyabot import Message, Chain, Equal, CQHttpBotInstance, MiraiBotInstance
from amiyabot.adapters.cqhttp import CQHTTPForwardMessage
from amiyabot.adapters.mirai import MiraiForwardMessage
from amiyabot.network.download import download_async
from amiyabot.util import run_in_thread_pool

from core import bot as main_bot, Admin, log
from .main import bot, curr_dir, tool_is_close, create_file, remove_file
from ..config import bottle_dir
from ..utils import Bottle, SQLHelper, Tarot, Life, Talent, PerAgeProperty, PerAgeResult, Summary, save_jpg, draw_life

LASTREPLAY = [
    "博士抽出了第三张塔罗牌了，看来这次占卜已经结束了呢，不过不管好运还是坏运，阿米娅都会陪着博士的！",
    "过去，现在，未来的阵列已显现于此，希望博士能够做出正确的选择！",
]


# 扫雷
@bot.on_message(keywords=['扫雷'], allow_direct=False, level=5)
async def sweep_mine(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 1, data.channel_id):
        return
    sucess_msg = '恭喜你, 你赢了!'
    mode = "简单"
    # 难度设置
    settings = [9, 9, 10, 5]
    if '中等' in data.text_original:
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
    if settings[0] < 3 or settings[1] < 3:
        return Chain(data).text('地图太小啦(>.<)! 最小为3×3')
    if settings[0] > 100 or settings[1] > 100:
        return Chain(data).text('地图太大啦(>.<)! 最大为100×100')
    if settings[2] < 1:
        return Chain(data).text('雷太少啦(>.<)! 最少为1个')
    if settings[2] > settings[0] * settings[1] - 1:
        return Chain(data).text('雷太多啦(>.<)! 最多为地图格子数-1')
    if settings[3] < 5:
        return Chain(data).text('时间太短啦(>.<)! 最短为5分钟')
    if settings[3] > 360:
        return Chain(data).text('时间太长啦(>.<)! 最长为6小时')
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
    first = True  # 第一次点击
    while True:
        await asyncio.sleep(0)
        if check:
            event = await data.wait_channel(
                Chain(data, at=False).text(f'剩余格数: {settings[0] * settings[1] - sum_}').html(
                    f'{curr_dir}/../template/html/winmine.html', {'map': game}, math.ceil(width),
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
                    first = False
                    row = int(m.group(1))
                    col = int(m.group(2))
                    if 0 <= row < settings[1] and 0 <= col < settings[0]:
                        if game[row][col] == -1:
                            if map_[row][col] == 9:
                                event.close_event()
                                await data.send(Chain(reply, at=False).text('你踩到雷了, 游戏结束!').html(
                                    f'{curr_dir}/../template/html/winmine.html', {'map': map_}, math.ceil(width),
                                    math.ceil(height)))
                                return
                            # 使用深度优先搜索翻开周围的格子
                            else:
                                check = True
                                stack = [(row, col)]  # 栈
                                while stack:  # 栈不为空
                                    x, y = stack.pop()  # 出栈
                                    if game[x][y] == -1:  # 未翻开
                                        game[x][y] = map_[x][y]  # 翻开
                                        if map_[x][y] == 0:  # 周围没有雷
                                            for i in range(-1, 2):  # 翻开周围的格子
                                                for j in range(-1, 2):  # 遍历周围的格子
                                                    if 0 <= x + i < settings[1] and 0 <= y + j < settings[0] and (
                                                            i != 0 or j != 0):  # 不越界
                                                        stack.append((x + i, y + j))  # 入栈

                            # 判断是否胜利
                            sum_ = 0
                            for y in range(settings[1]):
                                for x in range(settings[0]):
                                    if 0 <= game[y][x] <= 8:
                                        sum_ += 1
                            if sum_ == settings[1] * settings[0] - settings[2]:
                                event.close_event()
                                await data.send(Chain(reply, at=False).text(sucess_msg).html(
                                    f'{curr_dir}/../template/html/winmine.html', {'map': map_}, math.ceil(width),
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
                                await data.send(Chain(reply, at=False).text(sucess_msg).html(
                                    f'{curr_dir}/../template/html/winmine.html', {'map': map_, 'success': True}, math.ceil(width),
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
                elif reply.text_original.startswith(('提示', 'tip', 'Tip', 'TIP')) and first:
                    first = False
                    check = True
                    try_times = 0
                    while True:
                        try_times += 1
                        if try_times <= 1000:
                            row = random.randint(0, settings[1] - 1)
                            col = random.randint(0, settings[0] - 1)
                            if map_[row][col] == 0:
                                break
                        else:
                            row = random.randint(0, settings[1] - 1)
                            col = random.randint(0, settings[0] - 1)
                            if map_[row][col] != 9:
                                break
                    # 使用深度优先搜索翻开周围的格子
                    stack = [(row, col)]  # 栈
                    while stack:  # 栈不为空
                        x, y = stack.pop()  # 出栈
                        if game[x][y] == -1:  # 未翻开
                            game[x][y] = map_[x][y]  # 翻开
                            if map_[x][y] == 0:  # 周围没有雷
                                for i in range(-1, 2):  # 翻开周围的格子
                                    for j in range(-1, 2):  # 遍历周围的格子
                                        if 0 <= x + i < settings[1] and 0 <= y + j < settings[0] and (i != 0 or j != 0):  # 不越界
                                            stack.append((x + i, y + j))  # 入栈

                    # 判断是否胜利
                    sum_ = 0
                    for y in range(settings[1]):
                        for x in range(settings[0]):
                            if 0 <= game[y][x] <= 8:
                                sum_ += 1
                    if sum_ == settings[1] * settings[0] - settings[2]:
                        event.close_event()
                        await data.send(Chain(reply, at=False).text(sucess_msg).html(
                            f'{curr_dir}/../template/html/winmine.html', {'map': map_}, math.ceil(width),
                            math.ceil(height)))
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
    if await tool_is_close(data.instance.appid, 1, 2, 2, data.channel_id):
        return

    async def gomoku_filter1(data_: Message):
        return data_.text_original == '加入'

    timeout_msg = '游戏超时取消'
    time_limit = time.time() + 60
    event = await data.wait_channel(Chain(data).text('发起了一局五子棋对局, 请黑方在60s内输入"加入"加入对局'), True,
                                    True, int(time_limit - time.time()), gomoku_filter1)
    if not event:
        return Chain(data, at=False).text(timeout_msg)
    reply = event.message
    avatar = ''
    if reply.avatar:
        avatar = await download_async(reply.avatar)
    # 写入文件
    player1 = reply.user_id
    img1 = f'player{player1}.jpg'
    file_path1 = f'{curr_dir}/../template/resource/avatar/{img1}'
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
        return Chain(data, at=False).text(timeout_msg)
    reply = event.message
    avatar = ''
    if reply.avatar:
        avatar = await download_async(reply.avatar)
    # 写入文件
    player2 = reply.user_id
    img2 = f'player{player2}.jpg'
    file_path2 = f'{curr_dir}/../template/resource/avatar/{img2}'
    file = create_file(file_path2, 'wb')
    file.write(avatar)
    file.close()
    img2 = f'../resource/avatar/{img2}'
    name2 = reply.nickname
    await data.send(Chain(data, at=False).text('游戏开始!'))
    chess = [['' for _ in range(15)] for _ in range(15)]
    score = [0, 0]
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
            'chessMap': chess,
            'score': score
        }
        event = await data.wait_channel(
            Chain(data, at=False).html(f'{curr_dir}/../template/html/gomoku.html', info, 550, 626),
            True, True, 600, gomoku_filter2
        )
        if not event:
            remove_file(file_path1)
            remove_file(file_path2)
            return Chain(data, at=False).text(timeout_msg)
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
                is_win = False
                if not is_win:
                    for i in range(row - 4, row + 5):
                        if 0 <= i <= 10 and chess[i][col] == flag:
                            check = True
                            for j in range(1, 5):
                                if chess[i + j][col] != flag:
                                    check = False
                                    break
                            if check:
                                for j in range(0, 5):
                                    chess[i + j][col] = ''
                                is_win = True
                if not is_win:
                    for i in range(col - 4, col + 5):
                        if 0 <= i <= 10 and chess[row][i] == flag:
                            check = True
                            for j in range(1, 5):
                                if chess[row][i + j] != flag:
                                    check = False
                                    break
                            if check:
                                for j in range(0, 5):
                                    chess[row][i + j] = ''
                                is_win = True
                if not is_win:
                    for i in range(-4, 5):
                        if 0 <= row + i <= 10 and 0 <= col + i <= 10:
                            if chess[row + i][col + i] == flag:
                                check = True
                                for j in range(1, 5):
                                    if chess[row + i + j][col + i + j] != flag:
                                        check = False
                                        break
                                if check:
                                    for j in range(0, 5):
                                        chess[row + i + j][col + i + j] = ''
                                    is_win = True
                if not is_win:
                    for i in range(-4, 5):
                        if 0 <= row + i <= 10 and 0 <= col - i <= 10:
                            if chess[row + i][col - i] == flag:
                                check = True
                                for j in range(1, 5):
                                    if chess[row + i + j][col - i - j] != flag:
                                        check = False
                                        break
                                if check:
                                    for j in range(0, 5):
                                        chess[row + i + j][col - i - j] = ''
                                    is_win = True
                if is_win:
                    if flag == 'black':
                        score[0] += 1
                    else:
                        score[1] += 1
                    await data.send(Chain(data, at=False).text(f'{name1 if flag == "black" else name2} 获得一分'))
                # 判断棋盘是否已满
                is_full = True
                for i in range(15):
                    for j in range(15):
                        if chess[i][j] == '':
                            is_full = False
                            break
                    if not is_full:
                        break
                if is_full:
                    event.close_event()
                    remove_file(file_path1)
                    remove_file(file_path2)

                    def get_result(score_: list):
                        if score_[0] == score_[1]:
                            return '平局'
                        elif score_[0] > score_[1]:
                            return f'{name1} 获胜'
                        else:
                            return f'{name2} 获胜'

                    await data.send(
                        Chain(data, at=False)
                        .text(f'棋盘已满, 游戏结束\n游戏结果:\n\t{name1}: {score[0]}分\n\t{name2}: {score[1]}分\n')
                        .text(get_result(score))
                    )
                flag = 'black' if flag == 'white' else 'white'
            else:
                await data.send(Chain(data, at=False).text('该位置已有棋子, 请重新输入'))
        else:
            await data.send(Chain(data, at=False).text('输入坐标超出范围, 请重新输入'))


# 漂流瓶
@bot.on_message(
    keywords=re.compile(r'^.*?(扔|捡|删除|(不)?通过|审核|查看)(所有|全部)?漂流瓶\s?(匿名|不匿|\d+)?\s?([\s\S]*)$'),
    allow_direct=True, level=6)
async def bottle(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 3, data.channel_id):
        return
    match = re.match(r'^.*?(扔|捡|删除|(不)?通过|审核|查看)(所有|全部)?漂流瓶\s?(匿名|不匿|\d+)?\s?([\s\S]*)$',
                     data.text_original)
    config_ = bot.get_config('bottle')
    permission_deny = '权限不足哦~'
    none_msg = '漂流瓶不存在'
    form_err = '输入格式错误'
    number_re = r'^(\d+)$'
    if not match:
        return
    else:
        keyword = match.group(1)
        if keyword == '扔':
            text = match.group(5)
            if text.startswith((':', '：')):
                text = text[1:]
            allow_picture = config_.get('picture', False)
            if not text and (not allow_picture or len(data.image) == 0):
                return Chain(data, at=False).text('扔漂流瓶请附带文字或图片')
            bottle_ = Bottle(text if text else '', data.image if allow_picture else [])
            anonymous = not (match.group(4) and match.group(4) == '不匿')
            max_bottle = config_.get('max', 300)
            text = bottle_.get_message()
            if text != '':
                black = config_.get('black', [])
                for i in black:
                    if i in text:
                        return Chain(data).text('漂流瓶中包含敏感词汇, 请重新输入')
            pictures = await bottle_.get_picture()
            check = config_.get('check').get('enable', False)
            res = await SQLHelper.create_bottle(data.user_id, data.nickname, anonymous, max_bottle, data.time,
                                                text if text != '' else None, pictures if pictures != '' else None,
                                                check)
            if res:
                if check:
                    appid = config_.get('check').get('appid', None)
                    group = config_.get('check').get('group', None)
                    instance = main_bot[str(appid)]
                    if instance and group:
                        message = Chain().text(f'有新的漂流瓶需要审核\nid: {res.id}')
                        message.text(f'\n用户: {res.user_name}({res.user_id})')
                        message.text(f'\n状态: {"匿名" if res.anonymous else "不匿名"}')
                        message.text(f'\n兔兔实例：{data.instance.appid}')
                        if data.channel_id:
                            message.text(f'\n群聊: {data.channel_id}')
                        if text != '':
                            message.text('\n内容: ').text_image(text)
                        if pictures != '':
                            message.text('\n图片:')
                            picture = pictures.split(';')
                            for pic in picture:
                                message.image(f'{bottle_dir}{pic}')
                        message.text(
                            f'回复"兔兔通过漂流瓶 {res.id}"通过审核\n回复"兔兔不通过漂流瓶 {res.id}"不通过审核\n回复"兔兔审核漂流瓶"查看待审核的漂流瓶')
                        await instance.send_message(message, channel_id=str(group))
                    await data.send(Chain(data).text('兔兔已经把你的漂流瓶扔出去了~, 正在等待审核'))
                else:
                    await data.send(Chain(data).text('兔兔已经把你的漂流瓶扔出去了~'))
            else:
                await data.send(Chain(data).text('兔兔扔漂流瓶失败了~'))
        elif keyword == '捡':
            self = config_.get('self', False)
            bottle_ = await SQLHelper.get_random_bottle(self, int(data.user_id) if not self else None)
            if bottle_:
                message = Chain(data).text(f'兔兔捡到了一个漂流瓶\nid: {bottle_.id}')
                if not bottle_.anonymous:
                    message.text(f'\n来自: {bottle_.user_name}({bottle_.user_id})')
                if bottle_.text:
                    message.text_image(bottle_.text)
                if bottle_.picture:
                    pictures = bottle_.picture.split(';')
                    for pic in pictures:
                        message.image(f'{bottle_dir}{pic}')
            else:
                notip = config_.get('notip', '抱歉, 兔兔没有捡到任何漂流瓶呢>_<')
                message = Chain(data).text(notip)
            return message
        elif keyword == '删除':
            if match.group(3):
                if bool(Admin.get_or_none(account=data.user_id)):
                    async def data_filter(data_: Message):
                        return re.match(r'^[是否]$', data_.text_original)

                    reply = await data.wait(Chain(data).text('确定要删除所有漂流瓶吗?(是/否)'), data_filter=data_filter)
                    if reply and reply.text_original == '是':
                        await SQLHelper.delete_all_bottle()
                        return Chain(data).text('已删除所有漂流瓶')
                    else:
                        return Chain(data).text('已取消')
                else:
                    return Chain(data).text(permission_deny)
            else:
                if data.is_admin or bool(Admin.get_or_none(account=data.user_id)):
                    if re.match(number_re, match.group(4)):
                        bottle_ = await SQLHelper.get_bottle_by_id(int(match.group(4)))
                        if bottle_:
                            await SQLHelper.delete_bottle_by_id(int(match.group(4)))
                            return Chain(data).text('删除成功')
                        else:
                            return Chain(data).text(none_msg)
                    else:
                        return Chain(data).text(form_err)
                else:
                    return Chain(data).text(permission_deny)
        elif keyword == '查看':
            if bool(Admin.get_or_none(account=data.user_id)):
                if re.match(number_re, match.group(4)):
                    bottle_ = await SQLHelper.get_bottle_by_id(int(match.group(4)))
                    if bottle_:
                        message = Chain(data).text(f'检索到漂流瓶\nid: {bottle_.id}')
                        message.text(f'\n来自: {bottle_.user_name}({bottle_.user_id})')
                        if bottle_.text:
                            message.text_image(bottle_.text)
                        if bottle_.picture:
                            pictures = bottle_.picture.split(';')
                            for pic in pictures:
                                message.image(f'{bottle_dir}{pic}')
                        return message
                    else:
                        return Chain(data).text(none_msg)
                else:
                    return Chain(data).text(form_err)
            else:
                return Chain(data).text(permission_deny)
        elif '通过' in keyword:
            group = config_.get('check').get('group', None)
            if group and data.channel_id == str(group):
                if match.group(3) and match.group(3):
                    async def data_filter(data_: Message):
                        return re.match(r'^[是否]$', data_.text_original)

                    reply = await data.wait(Chain(data).text('确定要回拒所有未审核漂流瓶吗?(是/否)'),
                                            data_filter=data_filter)
                    if reply and reply.text_original == '是':
                        await SQLHelper.delete_unchecked_bottle()
                        return Chain(data).text('已回拒所有漂流瓶')
                    else:
                        return Chain(data).text('已取消')
                if re.match(number_re, match.group(4)):
                    bottle_ = await SQLHelper.get_bottle_by_id(int(match.group(4)))
                    if bottle_:
                        if not bottle_.check:
                            return Chain(data).text('漂流瓶已经通过审核了哦~')
                        if match.group(2):
                            await SQLHelper.delete_bottle_by_id(int(match.group(4)))
                            return Chain(data).text('已删除')
                        else:
                            await SQLHelper.pass_bottle_by_id(int(match.group(4)))
                            return Chain(data).text('已通过审核')
                    else:
                        return Chain(data).text(none_msg)
                else:
                    return Chain(data).text(form_err)
            else:
                return Chain(data).text('未在指定群聊中~')
        elif keyword == '审核':
            group = config_.get('check').get('group', None)
            if group and data.channel_id == str(group):
                bottles = await SQLHelper.get_check_bottles()
                if bottles:
                    message = Chain(data).text('待审核的漂流瓶:')
                    for bottle_ in bottles:
                        message.text(f'\nid: {bottle_.id}')
                        message.text('\n内容: ')
                        if bottle_.text:
                            message.text_image(bottle_.text)
                        if bottle_.picture:
                            pictures = bottle_.picture.split(';')
                            for pic in pictures:
                                message.image(f'{bottle_dir}{pic}')
                    message.text('\n回复"兔兔通过漂流瓶 [id]"通过审核\n回复"兔兔不通过漂流瓶 [id]"不通过审核')
                    return message
                else:
                    return Chain(data).text('没有待审核的漂流瓶哦~')


@bot.on_message(keywords=[Equal('塔罗牌'), Equal('塔罗牌占卜')], allow_direct=True, level=5)
async def tarot(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 4, data.channel_id):
        return
    tarot_ = Tarot(data.user_id)
    await data.send(
        Chain(data, reference=True, at=False).text(
            f'{data.nickname}就这样你走入了占卜店中，少女面带着微笑说着：“博士既然来了，不'
            f'如抽三张塔罗牌看看今天的运势哦~”(输入三次“选择[数字]”抽取三张塔罗牌，如“选择1”)'))
    draw_bytes = Tarot.get_bytes(await run_in_thread_pool(Tarot.draw_tarot, tarot_.list_tarot))
    await data.send(Chain(data).image(draw_bytes))

    async def data_filter(data_: Message):
        return re.match(r'^(选择)?([1-9]|1\d|2[0-2])$', data_.text_original)

    i = 0
    while i < 3:
        res = await data.wait(data_filter=data_filter)
        if res:
            match = re.match(r'^(选择)?([1-9]|1\d|2[0-2])$', res.text_original)
            card = tarot_.choose(int(match.group(2)))
            if not card:
                await data.send(Chain(data).text('唔。。博士!这张卡已经抽过了！'))
                continue
            img = Tarot.get_bytes(await run_in_thread_pool(Tarot.draw_tarot, tarot_.list_tarot))
            await data.send(
                Chain(data)
                .text(f'唔。。博士这次抽到的是 『{card[0]}』呢，这代表着\n————————\n{card[1]}')
                .image(img)
            )
            if i < 2:
                if card[0] in ['恶魔正位', '月亮正位', '塔正位', '塔逆位'] or (
                    "逆位" in card[0] and "恶魔逆位" not in card[0]):
                    await data.send(
                        Chain(data)
                        .text('唔。。看起来博士似乎不太好运的样子呢，不过不要担心，这并不是结局哦，所以博士，再来一次吧！')
                    )
                else:
                    await data.send(Chain(data).text('嗯！。。看起来似乎不错的样子呢，博士，再来一张吧！'))
            else:
                await data.send(Chain(data).text(random.choice(LASTREPLAY)))
            i += 1
        else:
            return Chain(data).text('“博士，真是笨蛋！。。”少女看着你一动不动，于是有点嗔怒的收起了塔罗牌。')
    img = Tarot.get_bytes(await run_in_thread_pool(Tarot.last_draw, tarot_.list_tarot))
    return Chain(data).image(img)


@bot.on_message(keywords=['remake', '人生重开', '人生重来'], level=5)
async def remake(data: Message):
    if await tool_is_close(data.instance.appid, 1, 2, 5, data.channel_id):
        return
    life_ = Life()
    life_.load()
    talents = life_.rand_talents(10)
    msg = '请发送编号选择3个天赋, 如"0 1 2", 或发送"随机"随机选择'
    des = '\n'.join([f'{i}.{t}' for i, t in enumerate(talents)])
    cancle_msg = '人生重开已取消'

    async def data_filter(data_: Message):
        # 匹配0-9的数字
        match_ = re.fullmatch(r"[\d\s]+", data_.text_original)
        if match_:
            return True
        else:
            return re.match(r'^随机$', data_.text_original)

    res = await data.wait(Chain(data).text(f'{msg}\n\n{des}'), max_time=60, data_filter=data_filter, level=5)
    while True:
        if res:
            def conflict_talents(talents_: List[Talent]) -> Optional[Tuple[Talent, Talent]]:
                for (t1, t2) in itertools.combinations(talents_, 2):
                    if t1.exclusive_with(t2):
                        return t1, t2
                return None

            match = re.fullmatch(r"\s*(\d)\s*(\d)\s*(\d)\s*", res.text_original)
            if match:
                nums = list(match.groups())
                nums = [int(i) for i in nums]
                nums.sort()
                if nums[-1] >= 10:
                    res = await data.wait(Chain(data).text('请发送正确的编号'), max_time=60, data_filter=data_filter,
                                          level=5)
                    continue
                talents_selected = [talents[i] for i in nums]
                ts = conflict_talents(talents_selected)
                if ts:
                    res = await data.wait(
                        Chain(data).text(f'你选择的天赋“{ts[0].name}”和“{ts[1].name}”不能同时拥有，请重新选择'),
                        max_time=60, data_filter=data_filter, level=5
                    )
                    continue
            elif res.text_original == '随机':
                while True:
                    nums = random.sample(range(10), 3)
                    nums.sort()
                    talents_selected = [talents[i] for i in nums]
                    if not conflict_talents(talents_selected):
                        break
            elif re.fullmatch(r'[\d\s]+', res.text_original):
                res = await data.wait(
                    Chain(data).text('请发送正确的编号, 如"0 1 2"'), max_time=60, data_filter=data_filter, level=5
                )
                continue
            else:
                return Chain(data).text(cancle_msg)
            break
        else:
            return Chain(data).text(cancle_msg)
    life_.set_talents(talents_selected)
    msg = (
        "请发送4个数字分配“颜值、智力、体质、家境”4个属性，如“5 5 5 5”，或发送“随机”随机选择；"
        f"可用属性点为{life_.total_property()}，每个属性不能超过10"
    )
    res = await res.wait(Chain(res).text(msg), max_time=60, data_filter=data_filter, level=5)
    total_prop = life_.total_property()
    while True:
        if res:
            match = re.fullmatch(r"\s*(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s*", res.text_original)
            if match:
                nums = list(match.groups())
                nums = [int(i) for i in nums]
                if sum(nums) != total_prop:
                    res = await data.wait(
                        Chain(data).text(f'属性之和需为{total_prop}, 请重新发送'), max_time=60, data_filter=data_filter,
                        level=5
                    )
                    continue
                elif max(nums) > 10:
                    res = await res.wait(
                        Chain(res).text('每个属性不能超过10, 请重新发送'), max_time=60, data_filter=data_filter, level=5
                    )
                    continue
            elif res.text_original == '随机':
                half_prop1 = int(total_prop / 2)
                half_prop2 = total_prop - half_prop1
                num1 = random.randint(0, half_prop1)
                num2 = random.randint(0, half_prop2)
                nums = [num1, num2, half_prop1 - num1, half_prop2 - num2]
                random.shuffle(nums)
            elif re.fullmatch(r'[\d\s]+', res.text_original):
                res = await data.wait(
                    Chain(data).text('请发送正确的数字, 如"5 5 5 5"'), max_time=60, data_filter=data_filter, level=5
                )
                continue
            else:
                return Chain(data).text(cancle_msg)
            break
        else:
            return Chain(data).text(cancle_msg)
    prop = {'CHR': nums[0], 'INT': nums[1], 'STR': nums[2], 'MNY': nums[3]}
    life_.apply_property(prop)
    await data.send(Chain(data).text('你的人生正在重开...'))
    init_prop = life_.get_property()
    results = [result for result in life_.run()]
    summary = life_.gen_summary()

    def get_life_msgs(talents_: List[Talent], init_prop_: PerAgeProperty, results_: List[PerAgeResult],
                      summary_: Summary):
        msgs_ = [
            '已选择以下天赋：\n' + '\n'.join([str(t) for t in talents_]),
            '已设置如下属性：\n'
            + f'颜值{init_prop_.CHR} 智力{init_prop_.INT} 体质{init_prop_.STR} 家境{init_prop_.MNY}',
        ]
        life_msgs = [str(result) for result in results_]
        n = bot.get_config('remake').get('num', 5)
        life_msgs = ['\n\n'.join(life_msgs[i: i + n]) for i in range(0, len(life_msgs), n)]
        msgs_.extend(life_msgs)
        msgs_.append(str(summary_))
        return msgs_

    async def get_life_img(talents_: List[Talent], init_prop_: PerAgeProperty, results_: List[PerAgeResult],
                           summary_: Summary) -> BytesIO:
        return save_jpg(draw_life(talents_, init_prop_, results_, summary_))

    try:
        if bot.get_config('remake').get('forward', False) and type(data.instance) in [CQHttpBotInstance,
                                                                                      MiraiBotInstance]:
            msgs = get_life_msgs(talents_selected, init_prop, results, summary)
            forward = CQHTTPForwardMessage(data) if type(data.instance) == CQHttpBotInstance else MiraiForwardMessage(
                data)
            for msg in msgs:
                await forward.add_message(Chain(data, at=False).text(msg), user_id=data.user_id, nickname='人生重开')
            await forward.send()
        else:
            img = await get_life_img(talents_selected, init_prop, results, summary)
            return Chain(data).image(img.getvalue())
    except Exception:
        log.warning(traceback.format_exc())
        return Chain(data).text('你的人生重开失败 :(')
