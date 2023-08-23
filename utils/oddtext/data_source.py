import math
import random
from dataclasses import dataclass

from core import log
from typing import Union, List, Protocol, Tuple

from .bug import bug_code, bug_level
from .cxh import emoji, pinyin
from .flip import flip_table
from .hxw import encharhxw, enchars, ftw, hxw, jtw


def cxh_text(text: str) -> str:
    def get_pinyin(s: str) -> str:
        if s in pinyin:
            return pinyin[s]
        return ''

    result = ''
    for i in range(len(text)):
        pinyin1 = get_pinyin(text[i])
        pinyin2 = get_pinyin(text[i + 1]) if i + 1 < len(text) else ''
        if pinyin1 + pinyin2 in emoji:
            result += emoji[pinyin1 + pinyin2]
        elif pinyin1 in emoji:
            result += emoji[pinyin1]
        else:
            result += text[i]
    return result


def hxw_text(text: str) -> str:
    result = ''
    for s in text:
        c = s
        if s in enchars:
            c = encharhxw[enchars.index(s)]
        elif s in jtw:
            c = hxw[jtw.index(s)]
        elif s in ftw:
            c = hxw[ftw.index(s)]
        result += c
    return result


def ant_text(text: str) -> str:
    result = ''
    for s in text:
        result += s + chr(1161)
    return result


def flip_text(text: str) -> str:
    text = text.lower()
    result = ''
    for s in text[::-1]:
        result += flip_table[s] if s in flip_table else s
    return result


def bug_text(text: str) -> str:
    def bug(p: str, n: Union[int, List]) -> str:
        result_ = ''
        if isinstance(n, list):
            n = math.floor(random.random() * (n[1] - n[0] + 1)) + n[0]
        for _ in range(n):
            result_ += bug_code[p][int(random.random() * len(bug_code[p]))]
        return result_

    level = 12
    u = bug_level[level]
    result = ''
    for s in text:
        result += s
        if s != ' ':
            result += (
                bug('mid', u['mid'])
                + bug('above', u['above'])
                + bug('under', u['under'])
                + bug('up', u['up'])
                + bug('down', u['down'])
            )
    return result


def guwen_code(text: str) -> str:
    return text.encode('u8').decode('gbk', 'replace')


def kouzi_code(text: str) -> str:
    return text.encode('gbk').decode('utf-8', 'replace')


def fuhao_code(text: str) -> str:
    return text.encode('u8').decode('iso8859-1')


def pinyin_code(text: str) -> str:
    return text.encode('gbk').decode('iso8859-1')


def fuhao_decode(text: str) -> str:
    try:
        return text.encode('iso8859-1').decode('u8')
    except UnicodeDecodeError:
        return '请输入正确的符号码，否则无法解码'


def pinyin_decode(text: str) -> str:
    try:
        return text.encode('iso8859-1').decode('gbk')
    except UnicodeDecodeError:
        return '请输入正确的拼音码，否则无法解码'


def wenju_code(text: str) -> str:
    return text.encode('u8').decode('gbk', 'replace').encode('gbk', 'replace').decode('u8', 'ignore')


def kunkao_code(text: str) -> str:
    return text.encode('gbk').decode('u8', 'replace').encode('u8').decode('gbk', 'ignore')


def rcnb_code(text: str) -> str:
    try:
        import rcnb
    except ImportError:
        log.warning('rcnb模块未安装, 尝试安装中...')
        try:
            import pip
            pip.main(['install', 'rcnb', '-i', 'https://mirrors.aliyun.com/pypi/simple/'])
            import rcnb
        except Exception as e:
            log.error(f'安装失败: {e}')
            return 'rcnb模块尝试安装失败, 请管理员手动安装后重试'
    return rcnb.encode(text)


def rcnb_decode(text: str) -> str:
    try:
        import rcnb
    except ImportError:
        log.warning('rcnb模块未安装, 尝试安装中...')
        try:
            import pip
            pip.main(['install', 'rcnb', '-i', 'https://mirrors.aliyun.com/pypi/simple/'])
            import rcnb
        except Exception as e:
            log.error(f'安装失败: {e}')
            return 'rcnb模块尝试安装失败, 请管理员手动安装后重试'
    try:
        return rcnb.decode(text)
    except Exception as e:
        log.error(f'解码失败: {e}')
        return '请输入正确的rcnb码，否则无法解码'


class Func(Protocol):
    def __call__(self, text: str) -> str:
        ...


@dataclass
class Command:
    keywords: Tuple[str, ...]
    func: Func


commands = [
    Command(('抽象话',), cxh_text),
    Command(('火星文',), hxw_text),
    Command(('蚂蚁文',), ant_text),
    Command(('翻转文字',), flip_text),
    Command(('故障文字',), bug_text),
    Command(('古文码',), guwen_code),
    Command(('口字码',), kouzi_code),
    Command(('符号码',), fuhao_code),
    Command(('拼音码',), pinyin_code),
    Command(("还原符号码", "解码符号码"), fuhao_decode),
    Command(("还原拼音码", "解码拼音码"), pinyin_decode),
    Command(("问句码",), wenju_code),
    Command(("锟拷码", "锟斤拷"), kunkao_code),
    Command(("rcnb",), rcnb_code),
    Command(("解码rcnb",), rcnb_decode)
]
