import copy
import re
from typing import Dict, List

from amiyabot import Message, CQHttpBotInstance, MiraiBotInstance
from meme_generator import Meme

from .config import UserConfig
from .data_source import User, ImageSource, user_avatar, QQUser, ImageUrl, check_user_id
from .utils import split_text

from ...api import GOCQTools, MiraiTools


def restore_last_at_me_seg(data: Message, msg: List):
    def _is_at_me_seg(seg: Dict):
        if type(data.instance) == CQHttpBotInstance:
            return seg['type'] == 'at' and str(seg['data']['qq']) == data.instance.appid
        elif type(data.instance) == MiraiBotInstance:
            return seg['type'] == 'At' and str(seg['target']) == data.instance.appid

    if data.is_at:
        if type(data.instance) == CQHttpBotInstance:
            raw_msg = data.message.get('message', [])
            i = -1
            last_msg_seg = raw_msg[i]
            if (
                last_msg_seg['type'] == 'text'
                and not str(last_msg_seg['data']['text']).strip()
                and len(raw_msg) >= 2
            ):
                i -= 1
                last_msg_seg = raw_msg[i]

            if _is_at_me_seg(last_msg_seg):
                msg.append(last_msg_seg)
        elif type(data.instance) == MiraiBotInstance:
            raw_msg = data.message.get('messageChain', [])
            i = -1
            last_msg_seg = raw_msg[i]
            if (
                last_msg_seg['type'] == 'Plain'
                and not str(last_msg_seg['text']).strip()
                and len(raw_msg) >= 2
            ):
                i -= 1
                last_msg_seg = raw_msg[i]

            if _is_at_me_seg(last_msg_seg):
                msg.append(last_msg_seg)


async def split_msg_v11_cq(data: Message, message: List, meme: Meme, trigger: Dict) -> dict:
    gocq = GOCQTools(data.instance, data=data)
    texts: List[str] = []
    users: List[User] = []
    image_sources: List[ImageSource] = []

    msg = copy.deepcopy(message)
    trigger_text_with_rigger: str = trigger['data']['text'].strip()
    trigger_text = re.sub(rf'^{UserConfig.meme_command_start()}\S+', '', trigger_text_with_rigger).strip()
    trigger_text_seg = [{'type': 'text', 'data': {'text': trigger_text}}]
    for i, m in enumerate(msg):
        if m['type'] == 'text' and m['data']['text'] == trigger['data']['text']:
            msg.pop(i)
            break
    msg = trigger_text_seg + msg

    restore_last_at_me_seg(data, msg)

    for msg_seg in msg:
        if msg_seg['type'] == 'at':
            image_sources.append(user_avatar(str(msg_seg['data']['qq'])))
            users.append(QQUser(data.instance, data, int(msg_seg['data']['qq'])))

        elif msg_seg['type'] == 'image':
            image_sources.append(ImageUrl(url=msg_seg['data']['url']))

        elif msg_seg['type'] == 'reply':
            msg_id = msg_seg['data']['id']
            source_msg = await gocq.get_message(message_id=int(msg_id))
            if source_msg:
                source_qq = str(source_msg['sender']['user_id'])
                msgs = source_msg['message']
                for each_msg in msgs:
                    if each_msg['type'] == 'image':
                        image_sources.append(ImageUrl(url=each_msg['data']['url']))
                        break
                else:
                    image_sources.append(user_avatar(source_qq))
                    users.append(QQUser(data.instance, data, int(source_qq)))

        elif msg_seg['type'] == 'text':
            raw_text = msg_seg['data']['text']
            split_msg = split_text(raw_text)
            for text in split_msg:
                if text.startswith("@") and check_user_id(text[1:]):
                    user_id = text[1:]
                    image_sources.append(user_avatar(user_id))
                    users.append(QQUser(data.instance, data, int(user_id)))

                elif text == "自己":
                    image_sources.append(
                        user_avatar(str(data.user_id))
                    )
                    users.append(QQUser(data.instance, data, int(data.user_id)))

                else:
                    texts.append(text)

    # 当所需图片数为 2 且已指定图片数为 1 时，使用 发送者的头像 作为第一张图
    if meme.params_type.min_images == 2 and len(image_sources) == 1:
        image_sources.insert(0, user_avatar(data.user_id))
        users.insert(0, QQUser(data.instance, data, int(data.user_id)))

    # 当所需图片数为 1 且没有已指定图片时，使用发送者的头像
    if UserConfig.memes_use_sender_when_no_image() and meme.params_type.min_images == 1 and len(image_sources) == 0:
        image_sources.append(user_avatar(data.user_id))
        users.append(QQUser(data.instance, data, int(data.user_id)))

    # 当所需文字数 >0 且没有输入文字时，使用默认文字
    if UserConfig.memes_use_default_when_no_text() and meme.params_type.min_texts > 0 and len(texts) == 0:
        texts = meme.params_type.default_texts

    # 当所需文字数 > 0 且没有输入文字，且仅存在一个参数时，使用默认文字
    # 为了防止误触发，参数必须放在最后一位，且该参数必须是bool，且参数前缀必须是--
    if UserConfig.memes_use_default_when_no_text() and meme.params_type.min_texts > 0 and len(texts) == 1 and texts[-1].startswith("--"):
        temp = copy.deepcopy(meme.params_type.default_texts)
        temp.extend(texts)
        texts = temp
    return {
        "texts": texts,
        "users": users,
        "image_sources": image_sources
    }


async def split_msg_v11_mirai(data: Message, message: List, meme: Meme, trigger: Dict) -> dict:
    mirai = MiraiTools(data.instance, data=data)
    texts: List[str] = []
    users: List[User] = []
    image_sources: List[ImageSource] = []

    msg = copy.deepcopy(message)
    trigger_text_with_rigger: str = trigger['text'].strip()
    trigger_text = re.sub(rf'^{UserConfig.meme_command_start()}\S+', '', trigger_text_with_rigger).strip()
    trigger_text_seg = [{'type': 'Plain', 'text': trigger_text}]
    for i, m in enumerate(msg):
        if m['type'] == 'Plain' and m['text'] == trigger['text']:
            msg.pop(i)
            break
    msg = trigger_text_seg + msg

    restore_last_at_me_seg(data, msg)

    for msg_seg in msg:
        if msg_seg['type'] == 'At':
            image_sources.append(user_avatar(str(msg_seg['target'])))
            users.append(QQUser(data.instance, data, msg_seg['target']))

        elif msg_seg['type'] == 'Image':
            image_sources.append(ImageUrl(url=msg_seg['url']))

        elif msg_seg['type'] == 'Quote':
            msg_id = msg_seg['id']
            source_msg = await mirai.get_message(message_id=int(msg_id), target=int(data.channel_id))
            if source_msg:
                source_qq = str(source_msg['sender']['id'])
                msgs = source_msg['messageChain']
                for each_msg in msgs:
                    if each_msg['type'] == 'Image':
                        image_sources.append(ImageUrl(url=each_msg['url']))
                        break
                else:
                    image_sources.append(user_avatar(source_qq))
                    users.append(QQUser(data.instance, data, int(source_qq)))

        elif msg_seg['type'] == 'Plain':
            raw_text = msg_seg['text']
            split_msg = split_text(raw_text)
            for text in split_msg:
                if text.startswith("@") and check_user_id(text[1:]):
                    user_id = text[1:]
                    image_sources.append(user_avatar(user_id))
                    users.append(QQUser(data.instance, data, int(user_id)))

                elif text == "自己":
                    image_sources.append(
                        user_avatar(str(data.user_id))
                    )
                    users.append(QQUser(data.instance, data, int(data.user_id)))

                else:
                    texts.append(text)

    # 当所需图片数为 2 且已指定图片数为 1 时，使用 发送者的头像 作为第一张图
    if meme.params_type.min_images == 2 and len(image_sources) == 1:
        image_sources.insert(0, user_avatar(data.user_id))
        users.insert(0, QQUser(data.instance, data, int(data.user_id)))

    # 当所需图片数为 1 且没有已指定图片时，使用发送者的头像
    if UserConfig.memes_use_sender_when_no_image() and meme.params_type.min_images == 1 and len(image_sources) == 0:
        image_sources.append(user_avatar(data.user_id))
        users.append(QQUser(data.instance, data, int(data.user_id)))

    # 当所需文字数 >0 且没有输入文字时，使用默认文字
    if UserConfig.memes_use_default_when_no_text() and meme.params_type.min_texts > 0 and len(texts) == 0:
        texts = meme.params_type.default_texts

    # 当所需文字数 > 0 且没有输入文字，且仅存在一个参数时，使用默认文字
    # 为了防止误触发，参数必须放在最后一位，且该参数必须是bool，且参数前缀必须是--
    if UserConfig.memes_use_default_when_no_text() and meme.params_type.min_texts > 0 and len(texts) == 1 and texts[-1].startswith("--"):
        temp = copy.deepcopy(meme.params_type.default_texts)
        temp.extend(texts)
        texts = temp
    return {
        "texts": texts,
        "users": users,
        "image_sources": image_sources
    }
