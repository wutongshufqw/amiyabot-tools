import itertools
import random
from io import BytesIO
from pathlib import Path
from typing import Dict, List

from PIL.ImageFont import FreeTypeFont

try:
    import ujson as json
except ModuleNotFoundError:
    from core import log

    log.warning("ujson not found, use json instead")
    import json
from PIL import Image, ImageDraw, ImageFont

from .strings import change_count_l, cut_text, get_cut_str


class Resource(object):
    @property
    def bg(self) -> Image:
        return Image.open(Path(__file__).parent.joinpath("./resource/tarot/背景.png")).resize((2000, 1000))

    @property
    def canvas(self) -> Image:
        c = Image.new("RGB", (2000, 1000), "#FFFFFF")
        c.paste(self.bg)
        return c

    @property
    def card_list(self) -> List[str]:
        return [
            "愚者",
            "魔术师",
            "女祭司",
            "女皇",
            "皇帝",
            "教皇",
            "恋人",
            "战车",
            "力量",
            "隐者",
            "命运之轮",
            "正义",
            "倒吊人",
            "死神",
            "节制",
            "恶魔",
            "塔",
            "星星",
            "月亮",
            "太阳",
            "审判",
            "世界",
        ]

    @property
    def data(self) -> dict:
        return json.loads(Path(__file__).parent.joinpath("./resource/tarot/tarot.json").read_text(encoding="utf-8"))

    @property
    def font(self) -> FreeTypeFont:
        return ImageFont.truetype(Path(__file__).parent.joinpath("./resource/fonts/FZDBSJW.ttf").__str__(), 30)

    @property
    def tarot_data(self) -> dict:
        data = {
            i: Image.open(Path(__file__).parent.joinpath(f"./resource/tarot/{i}.jpg")).resize((120, 240))
            for i in list(self.data)
        }
        data["背面"] = Image.open(Path(__file__).parent.joinpath("./resource/tarot/背面.png")).resize((120, 240))
        return data


class Tarot:
    res = Resource()

    def __init__(self, user_id):
        self.list_tarot = ['背面' for _ in range(22)]
        self.user_id = user_id
        self.tarot_data: List[Dict[str, int]] = [
            {key: random.randint(0, 1)} for key in self.res.card_list
        ]
        random.shuffle(self.tarot_data)
        self.result: List[str] = []

    @classmethod
    def get_bytes(cls, canvas: Image):
        byte_io = BytesIO()
        canvas.save(
            byte_io,
            format="JPEG",
            quality=90,
            optimize=True,
            progressive=True,
            subsampling=2,
            qtables="web_high",
        )
        return byte_io.getvalue()

    @classmethod
    def draw_tarot(cls, list_tarot: List[str]):
        """list_tarot用于存储塔罗牌名称"""
        canvas = cls.res.canvas.copy()
        draw = ImageDraw.Draw(canvas)
        a = 0
        for j, i in itertools.product(range(2), range(7)):
            card = cls.res.tarot_data[list_tarot[a]]
            a += 1
            sr = change_count_l(a)
            canvas.paste(card, (70 + i * 200, 40 + j * 320))
            start = 95 if len(sr) > 1 else 110
            draw.text(
                (start + i * 200, (j + 1) * 320 - 30),
                sr,
                font=cls.res.font,
                color="#3F4C60"
            )
        for i in range(8):
            card = cls.res.tarot_data[list_tarot[a]]
            a += 1
            sr = change_count_l(a)
            canvas.paste(card, (40 + i * 180, 680))
            start = 50 if len(sr) > 2 else 65
            draw.text(
                (start + i * 180, 920),
                sr,
                font=cls.res.font,
                color="#3F4C60"
            )
        return canvas

    def choose(self, num: int):
        key = list(self.tarot_data[num - 1])[0]
        ty = self.tarot_data[num - 1][key]
        key_result = f'{key}逆位' if ty else f'{key}正位'
        self.result.append(key_result)
        if key_result not in self.list_tarot:
            self.list_tarot[num - 1] = key_result
        else:
            return
        return key_result, self.res.data[key_result]

    @classmethod
    def last_draw(cls, list_tarot: List[str]):
        canvas = cls.res.canvas.copy()
        draw = ImageDraw.Draw(canvas)
        count = 0
        for card_name in list_tarot:
            if card_name != '背面':
                offset = 210 if len(card_name) > 4 else 240
                card = cls.res.tarot_data[card_name]
                canvas.paste(card.resize((300, 600)), (150 + count * 580, 100))
                draw.text(
                    (offset + count * 580, 710),
                    card_name,
                    font=cls.res.font,
                    color="#3F4C60"
                )
                draw.text(
                    (70 + count * 580, 760),
                    cut_text(cls.res.font, get_cut_str(cls.res.data[card_name], 100), 13),
                    font=cls.res.font,
                    color="#3F4C60"
                )
                count += 1
        return canvas
