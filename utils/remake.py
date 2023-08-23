import itertools
import json
import random
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Set, Dict, List, Union, Iterator, NamedTuple

from PIL import ImageFont, Image, ImageDraw
from PIL.Image import Image as IMG, Resampling
from PIL.ImageFont import FreeTypeFont

from .utils import parse_condition

# 人生重开

# 静态数据
resource_path = {  # 资源路径
    'data': Path(__file__).parent / 'resource' / 'remake' / 'data',
    'fonts': Path(__file__).parent / 'resource' / 'remake' / 'fonts',
    'images': Path(__file__).parent / 'resource' / 'remake' / 'images',
}
font_path = str(resource_path['fonts'] / 'font.ttf')  # 字体路径


# life.py
@dataclass
class PerAgeProperty:  # 每个年龄段的属性
    AGE: int  # 年龄
    CHR: int  # 颜值
    INT: int  # 智力
    STR: int  # 体质
    MNY: int  # 家境
    SPR: int  # 快乐

    def __str__(self) -> str:  # 转为字符串
        return f'「{self.AGE}岁/颜{self.CHR}智{self.INT}体{self.STR}钱{self.MNY}乐{self.SPR}」'


@dataclass
class PerAgeResult:  # 每个年龄段的结果
    property: PerAgeProperty  # 属性
    event_log: List[str]  # 事件日志
    talent_log: List[str]  # 天赋日志

    def __str__(self) -> str:  # 转为字符串
        return (
            f'{self.property}\n'
            + '\n'.join(self.event_log)
            + '\n'.join(self.talent_log)
        )


class Life:  # 人生
    def __init__(self):  # 初始化
        self.property = Property()
        self.age = AgeManager(self.property)
        self.event = EventManager(self.property)
        self.talent = TalentManager(self.property)

    def load(self):  # 加载数据
        self.age.load(resource_path['data'] / 'age.json')
        self.event.load(resource_path['data'] / 'events.json')
        self.talent.load(resource_path['data'] / 'talents.json')

    def alive(self) -> bool:  # 是否存活
        return self.property.LIF > 0

    def get_property(self) -> PerAgeProperty:  # 获取属性
        return PerAgeProperty(
            self.property.AGE,
            self.property.CHR,
            self.property.INT,
            self.property.STR,
            self.property.MNY,
            self.property.SPR,
        )

    def run(self) -> Iterator[PerAgeResult]:  # 运行
        while self.alive():
            self.age.grow()
            talent_log = self.talent.update_talent()
            event_log = self.event.run_events(self.age.get_events())
            yield PerAgeResult(
                self.get_property(),
                list(event_log),
                list(talent_log)
            )

    def rand_talents(self, num: int) -> List['Talent']:  # 随机天赋
        return list(self.talent.rand_talents(num))

    def set_talents(self, talents: List['Talent']):  # 设置天赋
        for t in talents:
            self.talent.add_talent(t)
        self.talent.update_talent_prop()

    def apply_property(self, effect: Dict[str, int]):  # 应用属性
        self.property.apply(effect)

    def total_property(self):  # 总属性
        return self.property.total

    def gen_summary(self) -> 'Summary':  # 生成总结
        return self.property.gen_summary()


# property.py
class PropGrade(NamedTuple):  # 属性等级
    min: int  # 最小值
    judge: str  # 判定
    grade: int  # 等级


@dataclass
class PropSummary:  # 属性总结
    value: int  # 值

    @property
    def name(self) -> str:  # 名称
        raise NotImplementedError

    def grades(self) -> List[PropGrade]:  # 等级
        raise NotImplementedError

    @property
    def prop_grade(self) -> PropGrade:  # 属性等级
        for g in reversed(self.grades()):
            if self.value >= g.min:
                return g
        return self.grades()[0]

    @property
    def judge(self) -> str:  # 判定
        return self.prop_grade.judge

    @property
    def grade(self) -> int:  # 等级
        return self.prop_grade.grade

    def __str__(self) -> str:  # 转为字符串
        return f'{self.name}: {self.value} ({self.judge})'


class CHRSummary(PropSummary):  # 颜值总结
    @property
    def name(self) -> str:  # 名称
        return '颜值'

    def grades(self) -> List[PropGrade]:  # 等级
        return [
            PropGrade(0, '地狱', 0),
            PropGrade(1, '折磨', 0),
            PropGrade(2, '不佳', 0),
            PropGrade(4, '普通', 0),
            PropGrade(7, '优秀', 1),
            PropGrade(9, '罕见', 2),
            PropGrade(11, '逆天', 3),
        ]


class INTSummary(PropSummary):  # 智力总结
    @property
    def name(self) -> str:  # 名称
        return '智力'

    def grades(self) -> List[PropGrade]:  # 等级
        return [
            PropGrade(0, '地狱', 0),
            PropGrade(1, '折磨', 0),
            PropGrade(2, '不佳', 0),
            PropGrade(4, '普通', 0),
            PropGrade(7, '优秀', 1),
            PropGrade(9, '罕见', 2),
            PropGrade(11, '逆天', 3),
            PropGrade(21, '识海', 3),
            PropGrade(131, '元神', 3),
            PropGrade(501, '仙魂', 3),
        ]


class STRSummary(PropSummary):  # 体质总结
    @property
    def name(self) -> str:  # 名称
        return '体质'

    def grades(self) -> List[PropGrade]:  # 等级
        return [
            PropGrade(0, '地狱', 0),
            PropGrade(1, '折磨', 0),
            PropGrade(2, '不佳', 0),
            PropGrade(4, '普通', 0),
            PropGrade(7, '优秀', 1),
            PropGrade(9, '罕见', 2),
            PropGrade(11, '逆天', 3),
            PropGrade(21, '凝气', 3),
            PropGrade(101, '筑基', 3),
            PropGrade(401, '金丹', 3),
            PropGrade(1001, '元婴', 3),
            PropGrade(2001, '仙体', 3),
        ]


class MNYSummary(PropSummary):  # 家境总结
    @property
    def name(self) -> str:  # 名称
        return '家境'

    def grades(self) -> List[PropGrade]:  # 等级
        return [
            PropGrade(0, '地狱', 0),
            PropGrade(1, '折磨', 0),
            PropGrade(2, '不佳', 0),
            PropGrade(4, '普通', 0),
            PropGrade(7, '优秀', 1),
            PropGrade(9, '罕见', 2),
            PropGrade(11, '逆天', 3),
        ]


class SPRSummary(PropSummary):  # 快乐总结
    @property
    def name(self) -> str:  # 名称
        return '快乐'

    def grades(self) -> List[PropGrade]:  # 等级
        return [
            PropGrade(0, '地狱', 0),
            PropGrade(1, '折磨', 0),
            PropGrade(2, '不幸', 0),
            PropGrade(4, '普通', 0),
            PropGrade(7, '幸福', 1),
            PropGrade(9, '极乐', 2),
            PropGrade(11, '天命', 3),
        ]


class AGESummary(PropSummary):  # 享年总结
    @property
    def name(self) -> str:  # 名称
        return '享年'

    def grades(self) -> List[PropGrade]:  # 等级
        return [
            PropGrade(0, '胎死腹中', 0),
            PropGrade(1, '早夭', 0),
            PropGrade(10, '少年', 0),
            PropGrade(18, '盛年', 0),
            PropGrade(40, '中年', 0),
            PropGrade(60, '花甲', 1),
            PropGrade(70, '古稀', 1),
            PropGrade(80, '杖朝', 2),
            PropGrade(90, '南山', 2),
            PropGrade(95, '不老', 3),
            PropGrade(100, '修仙', 3),
            PropGrade(500, '仙寿', 3),
        ]


class SUMSummary(PropSummary):  # 总评总结
    @property
    def name(self) -> str:  # 名称
        return '总评'

    def grades(self) -> List[PropGrade]:  # 等级
        return [
            PropGrade(0, '地狱', 0),
            PropGrade(41, '折磨', 0),
            PropGrade(50, '不佳', 0),
            PropGrade(60, '普通', 0),
            PropGrade(80, '优秀', 1),
            PropGrade(100, '罕见', 2),
            PropGrade(110, '逆天', 3),
            PropGrade(120, '传说', 3),
        ]


@dataclass
class Summary:  # 总结
    CHR: CHRSummary  # 颜值
    INT: INTSummary  # 智力
    STR: STRSummary  # 体质
    MNY: MNYSummary  # 家境
    SPR: SPRSummary  # 快乐
    AGE: AGESummary  # 享年
    SUM: SUMSummary  # 总评

    def __str__(self) -> str:  # 字符串
        return '==人生总结==\n\n' + '\n'.join([
            str(self.CHR),
            str(self.INT),
            str(self.STR),
            str(self.MNY),
            str(self.SPR),
            str(self.AGE),
            str(self.SUM),
        ])


class Property:
    SUM: int = 0

    def __init__(self):
        self.AGE: int = -1  # 年龄 age AGE
        self.CHR: int = 0  # 颜值 charm CHR
        self.INT: int = 0  # 智力 intelligence INT
        self.STR: int = 0  # 体质 strength STR
        self.MNY: int = 0  # 家境 money MNY
        self.SPR: int = 5  # 快乐 spirit SPR
        self.LIF: int = 1  # 生命 life LIF
        self.TMS: int = 1  # 次数 times TMS
        self.TLT: Set[int] = set()  # 天赋 talent TLT
        self.EVT: Set[int] = set()  # 事件 event EVT
        self.AVT: Set[int] = set()  # 触发过的事件 Achieve Event
        self.total: int = 20

    def apply(self, effect: Dict[str, int]):  # 应用效果
        for key in effect:
            if key == 'RDM':
                k = ['CHR', 'INT', 'STR', 'MNY', 'SPR'][id(key) % 5]
                setattr(self, k, getattr(self, k) + effect[key])
                continue
            setattr(self, key, getattr(self, key) + effect[key])

    def gen_summary(self) -> Summary:  # 生成总结
        self.SUM = (self.CHR + self.INT + self.STR + self.MNY + self.SPR) * 2 + self.AGE // 2
        return Summary(
            CHR=CHRSummary(self.CHR),
            INT=INTSummary(self.INT),
            STR=STRSummary(self.STR),
            MNY=MNYSummary(self.MNY),
            SPR=SPRSummary(self.SPR),
            AGE=AGESummary(self.AGE),
            SUM=SUMSummary(self.SUM),
        )


# drawer.py
def get_font(fontsize: int) -> FreeTypeFont:  # 获取字体
    return ImageFont.truetype(font_path, fontsize)


def get_icon(item: str) -> IMG:  # 获取图标
    return Image.open(resource_path['images'] / f'icon_{item}.png')


def draw_init_properties(prop: PerAgeProperty) -> IMG:  # 绘制初始属性
    image = Image.new('RGBA', (1250, 84))
    font = get_font(45)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, image.width, image.height), 20, '#0A2530')
    x = 0

    def draw_property(item: str, name: str, value: int):  # 绘制属性
        nonlocal x
        icon = get_icon(item)
        image.paste(icon, (x + (84 - icon.width) // 2, (84 - icon.height) // 2), mask=icon)
        draw.text((x + 84, 18), name, font=font, fill='white')
        length = font.getlength(str(value))
        draw.text((x + 170 + (80 - length) // 2, 18), str(value), font=font, fill='#53F8F8')
        x += 250

    draw_property('chr', '颜值', prop.CHR)
    draw_property('int', '智力', prop.INT)
    draw_property('str', '体质', prop.STR)
    draw_property('mny', '家境', prop.MNY)
    draw_property('spr', '快乐', prop.SPR)
    return image


def draw_properties(prop: PerAgeProperty) -> IMG:  # 绘制属性
    image = Image.new("RGBA", (670, 84))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, image.width, image.height), 20, '#153D4F')
    font = get_font(45)
    x = 0

    def draw_property(item: str, value: int):  # 绘制属性
        nonlocal x
        icon = get_icon(item)
        image.paste(
            icon, (x + (84 - icon.width) // 2, (84 - icon.height) // 2), mask=icon
        )
        x += 84
        w = font.getlength(str(value))
        draw.text((x + (46 - w) // 2, 18), str(value), font=font, fill='#53F8F8')
        x += 46

    draw_property('chr', prop.CHR)
    draw_property('int', prop.INT)
    draw_property('str', prop.STR)
    draw_property('mny', prop.MNY)
    draw_property('spr', prop.SPR)
    return image


def text_to_image(texts: List[str], fontsize: int = 10, fill: str = 'black', spacing=4) -> IMG:  # 文字转图片
    texts = sum([text.splitlines() for text in texts], [])
    font = get_font(fontsize)
    max_length = int(max([font.getlength(text) for text in texts]))
    ascent, descent = font.getmetrics()
    h = ascent * len(texts) + spacing * (len(texts) - 1) + descent
    image = Image.new('RGBA', (max_length, h))
    draw = ImageDraw.Draw(image)
    text = '\n'.join(texts)
    draw.multiline_text((0, 0), text, font=font, fill=fill, spacing=spacing)
    return image


def draw_age(age: int) -> IMG:  # 绘制年龄
    return text_to_image([f'{age}岁: '], fontsize=45, fill='#C3DE5A')


def draw_logs(logs: List[str]) -> IMG:  # 绘制日志
    return text_to_image(logs, fontsize=45, fill='#F0F2F3', spacing=30)


def draw_results(results: List[PerAgeResult]) -> IMG:  # 绘制结果
    class ImageResult(NamedTuple):  # 图片结果
        prop: IMG
        age: IMG
        logs: IMG

    images: List[ImageResult] = []
    for result in results:
        image_prop = draw_properties(result.property)
        image_prop = image_prop.resize((image_prop.width * 2 // 3, image_prop.height * 2 // 3), Resampling.LANCZOS)
        image_age = draw_age(result.property.AGE)
        image_logs = draw_logs(result.event_log + result.talent_log)
        images.append(ImageResult(image_prop, image_age, image_logs))

    img_w = max([(image.age.width + image.logs.width) for image in images])
    margin_prop = 20
    margin_logs = 50
    img_h = 0
    for image in images:
        img_h += image.prop.height + max(image.logs.height, image.age.height)
    img_h += margin_prop * len(images)
    img_h += margin_logs * (len(images) - 1)

    age_w = max([image.age.width for image in images])

    img = Image.new('RGBA', (img_w, img_h))
    y = 0
    for image in images:
        img.paste(image.prop, (0, y), mask=image.prop)
        y += image.prop.height + margin_prop
        img.paste(image.age, (age_w - image.age.width, y), mask=image.age)
        img.paste(image.logs, (age_w, y), mask=image.logs)
        y += max(image.logs.height, image.age.height) + margin_logs

    padding = 50
    inner_w = img.width + padding * 2
    inner_h = img.height + padding * 2
    inner_w = max(inner_w, 1250)
    inner = Image.new('RGBA', (inner_w, inner_h), '#0A2530')
    inner.paste(img, (padding, padding), mask=img)

    margin = 6
    border = Image.new('RGBA', (inner.width + margin * 2, inner.height + margin * 2))
    draw = ImageDraw.Draw(border)
    draw.rectangle(
        (margin, margin, border.width - margin, border.height - margin),
        outline='#267674',
        width=2,
    )

    length = 100
    rect = Image.new('RGBA', (length * 2, length * 2))
    draw = ImageDraw.Draw(rect)
    draw.rectangle((0, 0, rect.width, rect.height), outline='#267674', width=margin)
    for crop_box, pos in (
        ((0, 0, length, length), (0, 0)),
        ((length, 0, length * 2, length), (border.width - length, 0)),
        ((0, length, length, length * 2), (0, border.height - length)),
        (
            (length, length, length * 2, length * 2),
            (border.width - length, border.height - length),
        ),
    ):
        corner = rect.crop(crop_box)
        border.paste(corner, pos, mask=corner)

    frame = Image.new('RGBA', (border.width, border.height))
    frame.paste(inner, (margin, margin), mask=inner)
    frame.paste(border, (0, 0), mask=border)
    return frame


def grade_color(grade: int) -> str:
    if grade == 3:
        return '#FDCD44'
    elif grade == 2:
        return '#AC7AF9'
    elif grade == 1:
        return '#54FDFC'
    else:
        return '#CACBCB'


def draw_progress_bar(item: str, summary: PropSummary) -> IMG:  # 绘制进度条
    def draw_progress(value: int, color_: str) -> IMG:  # 绘制进度
        image_ = Image.new('RGBA', (770, 40))
        draw_ = ImageDraw.Draw(image_)
        draw_.rectangle((0, 0, image_.width, image_.height), fill='#273D47')
        count = min(max(value, 0), 10)
        draw_.rectangle((0, 0, image_.width * count // 10, image_.height), fill=color_)
        font_ = get_font(40)
        length_ = font_.getlength(str(value))
        draw_.text(
            ((image_.width - length_) // 2, 0),
            str(value),
            font=font_,
            fill=color_,
            stroke_width=2,
            stroke_fill='black',
        )
        return image_

    image = Image.new('RGBA', (1200, 84))
    icon = get_icon(item)
    image.paste(icon, ((84 - icon.width) // 2, (84 - icon.height) // 2), mask=icon)
    draw = ImageDraw.Draw(image)
    font = get_font(45)
    draw.text((84, 18), summary.name, font=font, fill='white')
    color = grade_color(summary.grade)
    progress = draw_progress(summary.value, color)
    image.paste(progress, (200, (image.height - progress.height) // 2), mask=progress)
    judge = summary.judge
    length = font.getlength(judge)
    draw.text(
        (200 + progress.width + (230 - length) // 2, 18), judge, font=font, fill=color
    )
    return image


def draw_summary(summary: Summary) -> IMG:  # 绘制总结
    def draw_sum(prop_sum: PropSummary) -> IMG:  # 绘制总结
        image = Image.new('RGBA', (1000, 84))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, 300, image.height), 20, '#153D4F')
        font = get_font(45)
        draw.text((20, 18), f'{prop_sum.name}: ', font=font, fill='white')
        length = font.getlength(str(prop_sum.value))
        draw.text(
            (140 + (160 - length) // 2, 18),
            str(prop_sum.value),
            font=font,
            fill='#53F8F8',
        )
        color = grade_color(prop_sum.grade)
        length = font.getlength(prop_sum.judge)
        draw.text(
            (770 + (230 - length) // 2, 18), prop_sum.judge, font=font, fill=color
        )
        return image

    inner = Image.new('RGBA', (1200, 650))
    image_age = draw_sum(summary.AGE)
    image_sum = draw_sum(summary.SUM)
    inner.paste(image_age, (200, 0), mask=image_age)
    inner.paste(image_sum, (200, 110), mask=image_sum)
    progress_bars = [
        draw_progress_bar('chr', summary.CHR),
        draw_progress_bar('int', summary.INT),
        draw_progress_bar('str', summary.STR),
        draw_progress_bar('mny', summary.MNY),
        draw_progress_bar('spr', summary.SPR),
    ]
    y = 230
    for progress_bar in progress_bars:
        inner.paste(progress_bar, (0, y), mask=progress_bar)
        y += progress_bar.height

    bg = Image.open(resource_path['images'] / 'bg_summary.png')
    bg.paste(
        inner,
        ((bg.width - inner.width) // 2, (bg.height - inner.height) // 2),
        mask=inner,
    )
    return bg


def draw_title(text: str) -> IMG:  # 绘制标题
    titlebar = Image.open(resource_path['images'] / 'titlebar.png')
    font = get_font(50)
    length = font.getlength(text)
    draw = ImageDraw.Draw(titlebar)
    draw.text(
        ((titlebar.width - length) // 2, 130),
        text,
        font=font,
        fill="white",
    )
    left = Image.open(resource_path['images'] / 'title_left.png')
    right = Image.open(resource_path['images'] / 'title_right.png')
    titlebar.paste(
        left, (int((titlebar.width - length) / 2 - left.width - 10), 140), mask=left
    )
    titlebar.paste(right, (int((titlebar.width + length) / 2 + 10), 140), mask=right)
    return titlebar


def break_text(text: str, font: FreeTypeFont, length: int) -> List[str]:  # 按长度分割文本
    lines = []
    line = ''
    for word in text:
        if font.getlength(line + word) > length:
            lines.append(line)
            line = ''
        line += word
    if line:
        lines.append(line)
    return lines


def draw_talent(talent: 'Talent') -> IMG:
    bg = Image.open(resource_path['images'] / 'bg_talent.png')
    font = get_font(45)
    draw = ImageDraw.Draw(bg)
    draw.text((40, 50), talent.name, font=font, fill='white')
    font = get_font(35)
    text = "\n".join(break_text(talent.description, font, 300))
    draw.multiline_text((40, 130), text, font=font, fill='#879A9E', spacing=10)
    return bg


def draw_talents(talents: List['Talent']) -> IMG:
    talent_images = [draw_talent(t) for t in talents]
    talent_w = talent_images[0].width
    talent_h = talent_images[0].height
    margin = 30
    image = Image.new('RGBA', (talent_w * 3 + margin * 2, talent_h))
    x = 0
    for talent_image in talent_images:
        image.paste(talent_image, (x, 0), mask=talent_image)
        x += talent_w + margin
    return image


def draw_life(talents: List['Talent'], init_prop: PerAgeProperty, results: List[PerAgeResult], summary: Summary) -> IMG:  # 绘制人生
    images: List[IMG] = [
        draw_title('已选天赋'),
        draw_talents(talents),
        draw_title('初始属性'),
        draw_init_properties(init_prop),
        draw_title('人生经历'),
        draw_results(results),
        draw_title('人生总结'),
        draw_summary(summary)
    ]
    img_w = max([image.width for image in images])
    img_h = sum([image.height for image in images]) + 100
    margin = 50
    frame = Image.new('RGBA', (img_w + margin * 2, img_h + margin * 2), '#04131F')
    y = margin
    for image in images:
        frame.paste(image, (margin + (img_w - image.width) // 2, y), mask=image)
        y += image.height
    return frame


def save_jpg(img: IMG) -> BytesIO:  # 保存为jpg
    output = BytesIO()
    img.convert('RGB').save(output, format='JPEG')
    return output


# 年龄
class AgeManager:
    def __init__(self, prop: Property):
        self.prop = prop
        self.ages: Dict[int, List[WeightedEvent]] = {}

    # noinspection PyTypeChecker
    def load(self, path: Path):
        data: Dict[str, dict] = json.load(path.open('r', encoding='utf-8'))
        self.ages = {
            int(k): [WeightedEvent(s) for s in v.get('event', [])]
            for k, v in data.items()
        }

    def grow(self):
        self.prop.AGE += 1

    def get_events(self) -> List['WeightedEvent']:
        return self.ages[self.prop.AGE]


# 事件

# 事件的分支
class Branch:
    def __init__(self, s: str):
        ss = s.split(':')
        self.condition = parse_condition(ss[0])
        self.event_id = int(ss[1])


# 事件的权重
class WeightedEvent:
    def __init__(self, s: Union[str, int]):
        if not isinstance(s, str) or "*" not in s:
            self.weight: float = 1.0
            self.event_id: int = int(s)
        else:
            ss = s.split("*")
            self.weight: float = float(ss[1])
            self.event_id: int = int(ss[0])


# 事件
class Event:
    def __init__(self, data: dict):
        self.id: int = int(data['id'])
        self.name: str = data['event']
        self.include = (
            parse_condition(data['include']) if 'include' in data else lambda _: True
        )
        self.exclude = (
            parse_condition(data['exclude']) if 'exclude' in data else lambda _: False
        )
        self.effect: Dict[str, int] = data['effect'] if 'effect' in data else {}
        self.branch: List[Branch] = (
            [Branch(s) for s in data['branch']] if 'branch' in data else []
        )
        self.no_random = 'NoRandom' in data and data['NoRandom']
        self.post_event = data['postEvent'] if 'postEvent' in data else None

    def check_condition(self, prop: Property) -> bool:
        return not self.no_random and self.include(prop) and not self.exclude(prop)

    def run(self, prop: Property, runner) -> Iterator[str]:
        for b in self.branch:
            if b.condition(prop):
                prop.apply(self.effect)
                yield self.name
                for text in runner(b.event_id):
                    yield text
                return
        prop.apply(self.effect)
        prop.EVT.add(self.id)
        yield self.name
        if self.post_event:
            yield self.post_event


# 事件处理器
class EventManager:
    def __init__(self, prop: Property):
        self.prop = prop
        self.events: Dict[int, Event] = {}

    # noinspection PyTypeChecker
    def load(self, path: Path):
        data: Dict[str, dict] = json.load(path.open('r', encoding='utf-8'))
        self.events = {int(k): Event(v) for k, v in data.items()}

    def run_events(self, weighted_events: List[WeightedEvent]) -> Iterator[str]:
        event_id = self.rand_event(weighted_events)
        return self.run_event(event_id)

    def rand_event(self, weighted_events: List[WeightedEvent]) -> int:
        event_checked = [e for e in weighted_events if self.events[e.event_id].check_condition(self.prop)]
        total = sum(e.weight for e in event_checked)
        rnd = random.random() * total
        for e in event_checked:
            rnd -= e.weight
            if rnd <= 0:
                return e.event_id
        return weighted_events[0].event_id

    def run_event(self, event_id: int) -> Iterator[str]:
        return self.events[event_id].run(self.prop, self.run_event)


# 天赋

# 天赋
class Talent:
    def __init__(self, data: dict):
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.grade: int = int(data['grade'])
        self.exclusive: List[int] = (
            [int(s) for s in data['exclusive']] if 'exclusive' in data else []
        )
        self.effect: Dict[str, int] = data['effect'] if 'effect' in data else {}
        self.status = int(data['status']) if 'status' in data else 0
        self.condition = (
            parse_condition(data['condition']) if 'condition' in data else lambda _: True
        )

    def __str__(self):
        return f'{self.name}({self.description})'

    def exclusive_with(self, talent: 'Talent') -> bool:
        return talent.id in self.exclusive or self.id in talent.exclusive

    def run(self, prop: Property) -> List[str]:
        if self.check_condition(prop):
            prop.apply(self.effect)
            prop.TLT.add(self.id)
            return [f'天赋「{self.name}」发动: {self.description}']
        return []

    def check_condition(self, prop: Property) -> bool:
        return self.condition(prop)


# 天赋处理器
class TalentManager:
    def __init__(self, prop: Property):
        self.prop = prop
        self.talents: List[Talent] = []
        self.talent_dict: Dict[int, List[Talent]] = {}
        self.grade_count = 4
        self.grade_prob = [0.889, 0.1, 0.01, 0.001]

    # noinspection PyTypeChecker
    def load(self, path: Path):
        data: dict = json.load(path.open('r', encoding='utf-8'))
        talent_list: List[Talent] = [Talent(v) for v in data.values()]
        self.talent_dict = {
            i: [t for t in talent_list if t.grade == i] for i in range(self.grade_count)
        }

    def rand_talents(self, count: int) -> Iterator[Talent]:
        def rand_grade():
            rnd = random.random()
            result = self.grade_count
            while rnd > 0:
                result -= 1
                rnd -= self.grade_prob[result]
            return result

        counts = {i: 0 for i in range(self.grade_count)}
        for _ in range(count):
            counts[rand_grade()] += 1
        for grade in range(self.grade_count - 1, -1, -1):
            count = counts[grade]
            n = len(self.talent_dict[grade])
            if count > n:
                count[grade - 1] += count - n
                count = n
            for talent in random.sample(self.talent_dict[grade], count):
                yield talent

    def add_talent(self, talent: Talent):
        for t in self.talents:
            if t.id == talent.id:
                return
        self.talents.append(talent)

    def update_talent_prop(self):
        self.prop.total += sum(t.status for t in self.talents)

    def update_talent(self) -> Iterator[str]:
        for t in self.talents:
            if t.id in self.prop.TLT:
                continue
            for result in t.run(self.prop):
                yield result
