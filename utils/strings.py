from PIL.ImageFont import FreeTypeFont

L = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ"]


def change_count_l(num: int) -> str:
    res = ""
    while num >= 10:
        num -= 10
        res += L[9]
    if num > 0:
        res += L[num - 1]
    return res


def cut_text(font: FreeTypeFont, origin: str, chars_per_line):
    """将单行超过指定长度的文本切割成多行
    Args:
        font (FreeTypeFont): 字体
        origin (str): 原始文本
        chars_per_line (int): 每行字符数（按全角字符算）
    """
    target = ""
    start_symbol = "[{<(【《（〈〖［〔“‘『「〝"
    end_symbol = ",.!?;:]}>)%~…，。！？；：】》）〉〗］〕”’～』」〞"
    line_width = chars_per_line * font.getlength("一")
    for i in origin.splitlines(False):
        if i == "":
            target += "\n"
            continue
        j = 0
        for ind, elem in enumerate(i):
            if i[j:ind + 1] == i[j:]:
                target += i[j:ind + 1] + "\n"
                continue
            elif font.getlength(i[j:ind + 1]) <= line_width:
                continue
            elif ind - j > 3:
                if i[ind] in end_symbol and i[ind - 1] != i[ind]:
                    target += i[j:ind + 1] + "\n"
                    j = ind + 1
                    continue
                elif i[ind] in start_symbol and i[ind - 1] != i[ind]:
                    target += i[j:ind] + "\n"
                    continue
            target += i[j:ind] + "\n"
            j = ind
    return target.rstrip()


def get_cut_str(string: str, cut: int) -> str:
    si = 0
    i = 0
    cut_str = ""
    for s in string:
        si += 2 if "\u4e00" <= s <= "\u9fff" else 1
        i += 1
        if si > cut:
            cut_str = f"{string[:i]}...."
            break
        else:
            cut_str = string
    return cut_str

