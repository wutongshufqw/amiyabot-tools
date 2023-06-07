import logging
import os
import shutil

from core import log

resources_dir = 'resource/plugins/tools'
import_success = True

# 尝试导入表情包组件
try:
    try:
        import aiocqhttp
        import httpx
        from meme_generator import Meme
        import pypinyin
        import pydantic
        import yaml
    except ImportError as e:
        log.warning("Some requirements are missing, trying to fix...")
        log.info("Installing requirements...")
        os.system(f"cd {os.path.dirname(__file__)}/../../ && pip install -r requirements.txt")
        log.info("Requirements installed.")
        from meme_generator import Meme
except ImportError as e:
    import_success = False
    shutil.copy(os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt'), resources_dir)
    log.error(
        '表情包组件导入失败, 请检查是否为代码部署, 若为代码部署可以尝试安装`resource/plugins/tools/requirements.txt`中的依赖后重启')
    raise e

if import_success:
    import copy
    import hashlib
    import random
    import re
    import traceback

    from amiyabot import Message, Chain, CQHttpBotInstance, MiraiBotInstance
    from amiyabot.util import run_in_thread_pool
    from io import BytesIO
    from itertools import chain
    from meme_generator import Meme
    from meme_generator.exception import (
        TextOverLength,
        ArgMismatch,
        TextOrNameNotEnough,
        MemeGeneratorException,
        ArgParserExit
    )
    from meme_generator.utils import TextProperties, render_meme_list
    from pathlib import Path
    from pypinyin import pinyin, Style
    from typing import Optional, List, Dict, Any

    from .config import UserConfig
    from .data_source import ImageSource, User, UserInfo
    from .depends import split_msg_v11_cq, split_msg_v11_mirai
    from .exception import PlatformUnsupportedError, NetworkError
    from .manager import meme_manager, ActionResult, MemeMode
    from .utils import meme_info

    from ..main import bot, tool_is_close

    from ...api import GOCQTools

    logging.disable(logging.DEBUG)

memes_cache_dir = Path(os.path.join(os.path.dirname(__file__), 'memes_cache_dir'))
emoji_help = """
`兔兔头像表情包帮助` 发送插件帮助<br/>
`兔兔表情包制作` 发送全部功能帮助<br/>
`兔兔表情帮助 + 表情` 发送选定表情功能帮助<br/>
`兔兔更新表情包制作` 更新表情包资源
"""
prefix = ['阿米娅', '阿米兔', '兔兔', '兔子', '小兔子', 'Amiya', 'amiya']


def check_prefix(match: re.Match, group: int = 1):
    if match is None:
        return False
    if match.group(group) in prefix:
        return True
    return False


@bot.on_message(keywords=re.compile(r'^(.*?)头像表情包帮助$'), level=5)
async def help_text(data: Message):
    match = re.match(r'^(.*?)头像表情包帮助$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    return Chain(data).markdown(emoji_help)


def get_user_id(data: Message, permit: Optional[int] = None):
    if permit is None or permit < 21:
        cid = f'{data.instance.appid}_{data.channel_id}_{data.user_id}'
    else:
        cid = f'{data.instance.appid}_{data.channel_id}'
    return cid


@bot.on_message(keywords=re.compile(r'^(.*?)(表情包制作|(头像|文字)表情包)$'), level=5)
async def emoji_make(data: Message):
    match = re.match(r'^(.*?)(表情包制作|(头像|文字)表情包)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    memes = sorted(
        meme_manager.memes,
        key=lambda meme: ''.join(
            chain.from_iterable(pinyin(meme.keywords[0], style=Style.TONE3))
        )
    )
    user_id = get_user_id(data)
    meme_list = [
        (meme, TextProperties(fill='black' if meme_manager.check(user_id, meme.key) else 'lightgrey')) for meme in memes
    ]

    # 缓存表情包列表
    meme_list_hashable = [
        ({'key': meme.key, 'keywords': meme.keywords}, prop) for meme, prop in meme_list
    ]
    meme_list_hash = hashlib.md5(str(meme_list_hashable).encode('utf8')).hexdigest()
    meme_list_cache_file = memes_cache_dir / f'{meme_list_hash}.jpg'
    if not meme_list_cache_file.exists():
        img: BytesIO = await run_in_thread_pool(render_meme_list, meme_list)
        with open(meme_list_cache_file, 'wb') as f:
            f.write(img.getvalue())
    else:
        img = BytesIO(meme_list_cache_file.read_bytes())
    msg = f"触发方式：“{UserConfig.meme_command_start()}关键词 + 图片/文字”\n发送 “兔兔表情详情 + 关键词” 查看表情参数和预览\n目前支持的表情列表："
    return Chain(data).text(msg).image(img.getvalue())


@bot.on_message(keywords=re.compile(r'^(.*?)表情(帮助|示例|详情)(.*)$'), level=5)
async def emoji_help(data: Message):
    match = re.match(r'^(.*?)表情(帮助|示例|详情)(.*)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    if not match.group(3):
        return Chain(data).text("请发送 “兔兔表情帮助 + 关键词” 查看表情参数和预览")
    meme_name = match.group(3).strip()
    if not (meme := meme_manager.find(meme_name)):
        return Chain(data).text("未找到该表情")
    info = meme_info(meme)
    info += '表情预览：\n'
    img = await meme.generate_preview()
    return Chain(data).text(info).image(img.getvalue())


@bot.on_message(keywords=re.compile(r'^(.*?)禁用表情(.*)$'), level=5)
async def emoji_disable(data: Message):
    match = re.match(r'^(.*?)禁用表情(.*)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    if not match.group(2):
        return Chain(data).text("请发送 “兔兔禁用表情 + 关键词” 禁用表情(关键词用空格隔开)")
    meme_names = match.group(2).strip().split()
    user_id = get_user_id(data)
    results = meme_manager.block(user_id, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f'表情 {name} 禁用成功'
        elif result == ActionResult.NOT_FOUND:
            message = f'表情 {name} 不存在'
        else:
            message = f'表情 {name} 禁用失败'
        messages.append(message)
    return Chain(data).text('\n'.join(messages))


@bot.on_message(keywords=re.compile(r'^(.*?)启用表情(.*)$'), level=5)
async def emoji_enable(data: Message):
    match = re.match(r'^(.*?)启用表情(.*)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    if not match.group(2):
        return Chain(data).text("请发送 “兔兔启用表情 + 关键词” 启用表情(关键词用空格隔开)")
    meme_names = match.group(2).strip().split()
    user_id = get_user_id(data)
    results = meme_manager.unblock(user_id, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f'表情 {name} 启用成功'
        elif result == ActionResult.NOT_FOUND:
            message = f'表情 {name} 不存在'
        else:
            message = f'表情 {name} 启用失败'
        messages.append(message)
    return Chain(data).text('\n'.join(messages))


@bot.on_message(keywords=re.compile(r'^(.*?)全局禁用表情(.*)$'), level=5)
async def emoji_global_disable(data: Message):
    match = re.match(r'^(.*?)全局禁用表情(.*)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    if not match.group(2):
        return Chain(data).text("请发送 “兔兔全局禁用表情 + 关键词” 全局禁用表情(关键词用空格隔开)")
    meme_names = match.group(2).strip().split()
    results = meme_manager.change_mode(MemeMode.WHITE, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f'表情 {name} 已设为白名单模式'
        elif result == ActionResult.NOT_FOUND:
            message = f'表情 {name} 不存在'
        else:
            message = f'表情 {name} 设置失败'
        messages.append(message)
    return Chain(data).text('\n'.join(messages))


@bot.on_message(keywords=re.compile(r'^(.*?)全局启用表情(.*)$'), level=5)
async def emoji_global_enable(data: Message):
    match = re.match(r'^(.*?)全局启用表情(.*)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    if not match.group(2):
        return Chain(data).text("请发送 “兔兔全局启用表情 + 关键词” 全局启用表情(关键词用空格隔开)")
    meme_names = match.group(2).strip().split()
    results = meme_manager.change_mode(MemeMode.BLACK, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f'表情 {name} 已设为黑名单模式'
        elif result == ActionResult.NOT_FOUND:
            message = f'表情 {name} 不存在'
        else:
            message = f'表情 {name} 设置失败'
        messages.append(message)
    return Chain(data).text('\n'.join(messages))


async def process(data: Message, meme: Meme, image_sources: List[ImageSource], texts: List[str], users: List[User],
                  args=None):
    if args is None:
        args = {}
    images: List[bytes] = []
    user_infos: List[UserInfo] = []

    try:
        for image_source in image_sources:
            images.append(await image_source.get_image())
    except PlatformUnsupportedError as ex:
        return Chain(data).text(f'当前平台 “{ex.platform}” 暂不支持获取头像，请使用图片输入'), False
    except NetworkError:
        log.warning(traceback.format_exc())
        return Chain(data).text('网络错误，请稍后再试'), False

    try:
        for user in users:
            user_infos.append(await user.get_info())
            args['user_infos'] = user_infos
    except NetworkError:
        log.warning('获取用户信息失败\n' + traceback.format_exc())
    try:
        result = await meme(images=images, texts=texts, args=args)
        return Chain(data, at=False).image(result.getvalue()), True
    except TextOverLength as ex:
        return Chain(data).text(f'文字“{ex.text}”过长'), False
    except ArgMismatch:
        return Chain(data).text(f'参数解析错误'), False
    except TextOrNameNotEnough:
        return Chain(data).text(f'文字或名字数量不足'), False
    except MemeGeneratorException:
        log.warning(traceback.format_exc())
        return Chain(data).text('出错了，请稍后再试'), False
    except ValueError as ex:
        log.warning(traceback.format_exc())
        return Chain(data).text(f'{ex.args[0]}'), False


async def find_meme(trigger: str, data: Message) -> Optional[Meme]:
    if trigger == '随机表情':
        meme = random.choice(meme_manager.memes)
        uid = get_user_id(data)
        if not meme_manager.check(uid, meme.key):
            await data.send(Chain(data).text('"随机到的表情不可用了捏qwq\n再试一次吧~'))
            return None
        await data.send(Chain(data).text(f'随机到了表情 【{meme.keywords[0]}】'))
        return meme
    meme = meme_manager.find(trigger)
    return meme


async def emoji_verify(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id):
        return False, 0
    split_msg = None
    meme = None
    if type(data.instance) is CQHttpBotInstance:
        gocq = GOCQTools(data.instance, data=data)
        msg: List = copy.deepcopy(data.message.get('message', []))
        if not msg:
            log.debug('消息内容为空, 跳过')
            return False, 0
        if msg[0]['type'] == 'reply':
            # 当回复目标是自己时，去除隐式at自己
            msg_id = msg[0]['data']['id']
            source_msg = await gocq.get_message(int(msg_id))
            if source_msg:
                source_qq = str(source_msg['sender']['user_id'])
                # 隐式at和显示at之间还有一个文本空格
                while len(msg) > 1 and (msg[1]['type'] == 'at' or msg[1]['type'] == 'text' and msg[1]['data']['text'].strip() == ''):
                    if msg[1]['type'] == 'at' and msg[1]['data']['qq'] == source_qq or msg[1]['type'] == 'text' and msg[1]['data']['text'].strip() == '':
                        msg.pop(1)
                    else:
                        break
        for each_msg in msg:
            if each_msg['type'] != 'text':
                continue
            if not each_msg['data']['text'].startswith(UserConfig.meme_command_start()):
                continue
            trigger = each_msg
            break
        else:
            for each_msg in msg:
                if each_msg['type'] != 'text':
                    continue
                trigger = each_msg
                break
            else:
                log.debug('空触发, 跳过')
                return False, 0

        uid = get_user_id(data)
        try:
            trigger_text: str = trigger['data']['text'].split()[0]
        except IndexError:
            log.debug('空触发, 跳过')
            return False, 0
        if not trigger_text.startswith(UserConfig.meme_command_start()):
            log.debug('非前缀触发, 跳过')
            return False, 0
        meme = await find_meme(trigger_text.replace(UserConfig.meme_command_start(), '').strip(), data)
        if meme is None:
            log.debug('未找到表情, 跳过')
            return False, 0
        if not meme_manager.check(uid, meme.key):
            log.debug('表情被关闭, 跳过')
            return False, 0

        split_msg = await split_msg_v11_cq(data, msg, meme, trigger)
    elif type(data.instance) is MiraiBotInstance:
        msg: List = copy.deepcopy(data.message.get('messageChain', []))
        if not msg:
            log.debug('消息内容为空, 跳过')
            return False, 0
        # 第一条永远为Source
        msg.pop(0)
        if msg[0]['type'] == 'Quote':
            # 去除回复消息自动at
            if msg[1]['type'] == 'At' and msg[1]['target'] == msg[0]['senderId']:
                msg.pop(1)
        for each_msg in msg:
            if each_msg['type'] != 'Plain':
                continue
            if not each_msg['text'].startswith(UserConfig.meme_command_start()):
                continue
            trigger = each_msg
            break
        else:
            for each_msg in msg:
                if each_msg['type'] != 'Plain':
                    continue
                trigger = each_msg
                break
            else:
                log.debug('空触发, 跳过')
                return False, 0

        uid = get_user_id(data)
        try:
            trigger_text: str = trigger['text'].split()[0]
        except IndexError:
            log.debug('空触发, 跳过')
            return False, 0
        if not trigger_text.startswith(UserConfig.meme_command_start()):
            log.debug('非前缀触发, 跳过')
            return False, 0
        meme = await find_meme(trigger_text.replace(UserConfig.meme_command_start(), '').strip(), data)
        if meme is None:
            log.debug('未找到表情, 跳过')
            return False, 0
        if not meme_manager.check(uid, meme.key):
            log.debug('表情被关闭, 跳过')
            return False, 0

        split_msg = await split_msg_v11_mirai(data, msg, meme, trigger)
    if split_msg and meme:
        raw_texts: List[str] = split_msg['texts']
        users: List[User] = split_msg['users']
        image_sources: List[ImageSource] = split_msg['image_sources']

        args: Dict[str, Any] = {}
        if meme.params_type.args_type:
            try:
                parse_result = meme.parse_args(raw_texts)
            except ArgParserExit:
                return True, 5, Chain(data).text('参数解析错误')
            texts = parse_result['texts']
            parse_result.pop('texts')
            args = parse_result
        else:
            texts = raw_texts

        if not meme.params_type.min_images <= len(image_sources) <= meme.params_type.max_images:
            if UserConfig.memes_prompt_params_error():
                return True, 5, Chain(data).text(
                    f'输入图片数量不符，图片数量应为 {meme.params_type.min_images}'
                    + (
                        f' ~ {meme.params_type.max_images}'
                        if meme.params_type.max_images > meme.params_type.min_images
                        else ''
                    ) + f', 实际数量为{len(image_sources)}'
                )
            return False, 0

        if not (meme.params_type.min_texts <= len(texts) <= meme.params_type.max_texts):
            if UserConfig.memes_prompt_params_error():
                return True, 5, Chain(data).text(
                    f'输入文字数量不符，文字数量应为 {meme.params_type.min_texts}'
                    + (
                        f' ~ {meme.params_type.max_texts}'
                        if meme.params_type.max_texts > meme.params_type.min_texts
                        else ''
                    ) + f', 实际数量为{len(raw_texts)}'
                )
            return False, 0

        msg, flag = await process(data, meme, image_sources, texts, users, args)
        if flag:
            return True, 5, msg
    return False, 0


@bot.on_message(verify=emoji_verify, check_prefix=False)
async def emoji(data: Message):
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id):
        return
    msg = data.verify.keypoint
    if msg:
        return msg
