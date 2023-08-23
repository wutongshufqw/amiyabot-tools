import logging
import os
from re import Match
import shutil
import time

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

    from amiyabot import Message, Chain, CQHttpBotInstance, MiraiBotInstance, KOOKBotInstance
    from amiyabot.factory import BotHandlerFactory
    from amiyabot.util import run_in_thread_pool
    from io import BytesIO
    from itertools import chain
    from meme_generator import Meme
    from meme_generator.download import check_resources
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

    from .config import user_config
    from .data_source import ImageSource, User, UserInfo
    from .depends import split_msg_cq, split_msg_mirai, split_msg_kook
    from .exception import PlatformUnsupportedError, NetworkError
    from .manager import meme_manager, ActionResult, MemeMode
    from .utils import meme_info

    from ..main import bot, tool_is_close

    from ...utils import run_async

    logging.disable(logging.DEBUG)

memes_cache_dir = Path(os.path.join(os.path.dirname(__file__), 'memes_cache_dir'))
emoji_help_text = """
`兔兔头像表情包帮助` 发送插件帮助<br/>
`兔兔表情包制作` 发送全部功能帮助<br/>
`兔兔表情帮助 + 表情` 发送选定表情功能帮助<br/>
`兔兔更新表情包制作` 更新表情包资源<br/>
`兔兔(全局)[禁/启]用表情` + 表情` 禁用/启用群聊中指定表情
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
    return Chain(data).markdown(emoji_help_text)


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
    msg = f'触发方式:"{user_config.meme_command_start}关键词 + 图片/文字"\n发送 "兔兔表情详情 + 关键词" 查看表情参数和预览\n目前支持的表情列表:'
    return Chain(data).text(msg).image(img.getvalue())


@bot.on_message(keywords=re.compile(r'^(.*?)表情(帮助|示例|详情)(.*)$'), level=5)
async def emoji_help(data: Message):
    match = re.match(r'^(.*?)表情(帮助|示例|详情)(.*)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    if not match.group(3):
        return Chain(data).text('请发送 "兔兔表情帮助 + 关键词" 查看表情参数和预览')
    meme_name = match.group(3).strip()
    if not (meme := meme_manager.find(meme_name)):
        return Chain(data).text('未找到该表情')
    info = meme_info(meme)
    info += '表情预览:\n'
    img = await meme.generate_preview()
    return Chain(data).text(info).image(img.getvalue())


@bot.on_message(keywords=re.compile(r'^(.*?)(全局)?([禁启]用)表情(.*)$'), level=5)
async def emoji_disable(data: Message):
    match = re.match(r'^(.*?)(全局)?([禁启]用)表情(.*)$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    if not match.group(4):
        return Chain(data).text(f'请发送 "兔兔{"全局" if match.group(2) else ""}{match.group(3)}表情 + 关键词" {match.group(3)}表情(关键词用空格隔开)')
    meme_names = match.group(4).strip().split()
    user_id = get_user_id(data)
    if match.group(3) == '启用':
        if match.group(2):
            results = meme_manager.change_mode(MemeMode.BLACK, meme_names)
        else:
            results = meme_manager.unblock(user_id, meme_names)
    else:
        if match.group(2):
            results = meme_manager.change_mode(MemeMode.WHITE, meme_names)
        else:
            results = meme_manager.block(user_id, meme_names)
    messages = []

    def mode_to_str(match_: Optional[Match[str]]):
        if match_:
            return '黑' if match_.group(3) == '启用' else '白'
        else:
            return ''

    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f'表情 {name} {"已设为"+ mode_to_str(match) + "名单模式" if match.group(2) else match.group(3)+ "成功"}'
        elif result == ActionResult.NOT_FOUND:
            message = f'表情 {name} 不存在'
        else:
            message = f'表情 {name} {"设置" if match.group(2) else match.group(3)}失败'
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
        return Chain(data).text(f'当前平台 "{ex.platform}" 暂不支持获取头像，请使用图片输入'), False
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
        return Chain(data).text(f'文字"{ex.text}"过长'), False
    except ArgMismatch:
        return Chain(data).text('参数解析错误'), False
    except TextOrNameNotEnough:
        return Chain(data).text('文字或名字数量不足'), False
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
    skip_msg = '消息内容为空, 跳过'
    none_msg = '未找到表情, 跳过'
    null_msg = '空触发, 跳过'
    prefix_msg = '非前缀触发, 跳过'
    close_msg = '表情被关闭, 跳过'
    if type(data.instance) is CQHttpBotInstance:
        msg: List = copy.deepcopy(data.message.get('message', []))
        if not msg:
            log.debug(skip_msg)
            return False, 0
        if msg[0]['type'] == 'reply':
            # 当回复目标是自己时，去除隐式at自己
            msg_id = msg[0]['data']['id']
            source_msg: Message = await data.instance.api.get_message(msg_id)
            if source_msg:
                source_qq = source_msg.user_id
                # 隐式at和显示at之间还有一个文本空格
                while len(msg) > 1 and (msg[1]['type'] == 'at' or msg[1]['type'] == 'text' and msg[1]['data']['text'].strip() == ''):
                    if msg[1]['type'] == 'at' and msg[1]['data']['qq'] == source_qq or msg[1]['type'] == 'text' and msg[1]['data']['text'].strip() == '':
                        msg.pop(1)
                    else:
                        break
        for each_msg in msg:
            if each_msg['type'] != 'text':
                continue
            if not each_msg['data']['text'].startswith(user_config.meme_command_start):
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
                log.debug(null_msg)
                return False, 0

        uid = get_user_id(data)
        try:
            trigger_text: str = trigger['data']['text'].split()[0]
        except IndexError:
            log.debug(null_msg)
            return False, 0
        if not trigger_text.startswith(user_config.meme_command_start):
            log.debug(prefix_msg)
            return False, 0
        meme = await find_meme(trigger_text.replace(user_config.meme_command_start, '').strip(), data)
        if meme is None:
            log.debug(none_msg)
            return False, 0
        if not meme_manager.check(uid, meme.key):
            log.debug(close_msg)
            return False, 0

        split_msg = await split_msg_cq(data, msg, meme, trigger)
    elif type(data.instance) is MiraiBotInstance:
        msg: List = copy.deepcopy(data.message.get('messageChain', []))
        if not msg:
            log.debug(skip_msg)
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
            if not each_msg['text'].startswith(user_config.meme_command_start):
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
                log.debug(null_msg)
                return False, 0

        uid = get_user_id(data)
        try:
            trigger_text: str = trigger['text'].split()[0]
        except IndexError:
            log.debug(null_msg)
            return False, 0
        if not trigger_text.startswith(user_config.meme_command_start):
            log.debug(prefix_msg)
            return False, 0
        meme = await find_meme(trigger_text.replace(user_config.meme_command_start, '').strip(), data)
        if meme is None:
            log.debug(none_msg)
            return False, 0
        if not meme_manager.check(uid, meme.key):
            log.debug(close_msg)
            return False, 0

        split_msg = await split_msg_mirai(data, msg, meme, trigger)
    elif type(data.instance) is KOOKBotInstance:
        msg: Dict = copy.deepcopy(data.message.get('extra'))
        if not msg:
            log.debug(skip_msg)
            return False, 0

        # 去除回复默认@
        if msg.get('quote'):
            msg['mention'].pop(0)

        # 去除所有@消息
        trigger = msg['kmarkdown']['raw_content']
        trigger = trigger.split(' ')
        triggers = []
        trigger_text = ''
        for each_trigger in trigger:
            if each_trigger.startswith('@'):
                continue
            triggers.append(each_trigger)
        if len(triggers) > 0:
            trigger_text = triggers[0].strip()
        if not trigger_text:
            log.debug(null_msg)
            return False, 0

        uid = get_user_id(data)
        if not trigger_text.startswith(user_config.meme_command_start):
            log.debug(prefix_msg)
            return False, 0
        meme = await find_meme(trigger_text.replace(user_config.meme_command_start, '').strip(), data)
        if meme is None:
            log.debug(none_msg)
            return False, 0
        if not meme_manager.check(uid, meme.key):
            log.debug(close_msg)
            return False, 0

        split_msg = await split_msg_kook(data, msg, meme, triggers)

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
            if user_config.memes_prompt_params_error:
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
            if user_config.memes_prompt_params_error:
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


@bot.on_message(keywords=re.compile(r'^(.*?)更新表情包制作$'))
async def update_meme_user(data: Message):
    match = re.match(r'^(.*?)更新表情包制作$', data.text_original)
    if await tool_is_close(data.instance.appid, 1, 1, 8, data.channel_id) or not check_prefix(match):
        return
    start = time.time()
    await check_resources()
    end = time.time()
    return Chain(data).text(f'更新完成, 耗时{end - start:.2f}秒')


# noinspection PyUnusedLocal
@bot.timed_task(each=1, sub_tag='meme_update')
async def meme_update(instance: BotHandlerFactory):
    bot.remove_timed_task('meme_update')
    if user_config.memes_check_resources_on_startup:
        log.info('正在检查资源文件更新...')
        run_async(check_resources)
