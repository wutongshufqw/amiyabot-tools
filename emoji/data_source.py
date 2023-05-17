from .download import download_url, download_avatar
from .functions import *

# noinspection PyTypeChecker
commands = [
    Command(("随机表情",), random_expressions, allow_gif=True, arg_num=10, func_random=random_expressions),
    Command(("图片操作",), operations, allow_gif=True, arg_num=2),
    Command(("万能表情",), universal, allow_gif=True, arg_num=10),
    Command(("摸", "摸摸", "摸头", "摸摸头", "rua"), petpet, arg_num=1),
    Command(("亲", "亲亲"), kiss),
    Command(("贴", "贴贴", "蹭", "蹭蹭"), rub),
    Command(("咖波蹭",), capoo_rub),
    Command(("顶", "玩"), play),
    Command(("拍",), pat),
    Command(("撕",), rip, arg_num=1),
    Command(("怒撕",), rip_angrily),
    Command(("丢", "扔"), throw),
    Command(("抛", "掷"), throw_gif),
    Command(("爬", "爪巴"), crawl, arg_num=1),
    Command(("精神支柱",), support),
    Command(("一直",), always, allow_gif=True, arg_num=2),
    Command(("一直一直",), always_always, allow_gif=True, arg_num=2),
    Command(("一直套娃",), always_cycle, allow_gif=True, arg_num=2),
    Command(("加载中",), loading, allow_gif=True),
    Command(("转",), turn),
    Command(("风车转",), windmill_turn),
    Command(("小天使",), littleangel, arg_num=1),
    Command(("催刀", "快出刀"), cuidao, arg_num=1),
    Command(("不要靠近",), dont_touch),
    Command(("一样",), alike),
    Command(("滚",), roll),
    Command(("玩游戏", "来玩游戏"), play_game, allow_gif=True, arg_num=1),
    Command(("膜", "膜拜"), worship),
    Command(("吃",), eat),
    Command(("可莉吃",), klee_eat),
    Command(("啃",), bite),
    Command(("胡桃啃",), hutao_bite),
    Command(("出警",), police),
    Command(("警察",), police1),
    Command(("问问", "去问问"), ask, arg_num=1),
    Command(("舔", "舔屏", "prpr"), prpr, allow_gif=True),
    Command(("搓",), twist),
    Command(("墙纸",), wallpaper, allow_gif=True),
    Command(("国旗",), china_flag),
    Command(("交个朋友",), make_friend, arg_num=1),
    Command(("继续干活", "打工人"), back_to_work),
    Command(("完美", "完美的"), perfect),
    Command(("关注",), follow, arg_num=1),
    Command(("我朋友说", "我有个朋友说"), my_friend, arg_num=10),
    Command(("这像画吗",), paint),
    Command(("震惊",), shock),
    Command(("兑换券",), coupon, arg_num=2),
    Command(("听音乐",), listen_music),
    Command(("典中典",), dianzhongdian, arg_num=3),
    Command(("哈哈镜",), funny_mirror),
    Command(("永远爱你",), love_you),
    Command(("对称",), symmetric, allow_gif=True, arg_num=1),
    Command(("安全感",), safe_sense, arg_num=2),
    Command(("永远喜欢", "我永远喜欢"), always_like, arg_num=10),
    Command(("采访",), interview, arg_num=1),
    Command(("打拳",), punch),
    Command(("群青",), cyan),
    Command(("捣",), pound),
    Command(("捶",), thump),
    Command(("需要", "你可能需要"), need),
    Command(("捂脸",), cover_face),
    Command(("敲",), knock),
    Command(("垃圾", "垃圾桶"), garbage),
    Command(("为什么@我", "为什么at我"), whyatme),
    Command(("像样的亲亲",), decent_kiss),
    Command(("啾啾",), jiujiu),
    Command(("吸", "嗦"), suck),
    Command(("锤",), hammer),
    Command(("紧贴", "紧紧贴着"), tightly),
    Command(("注意力涣散",), distracted),
    Command(("阿尼亚喜欢",), anyasuki, arg_num=1, allow_gif=True),
    Command(("想什么",), thinkwhat, allow_gif=True),
    Command(("远离",), keepaway),
    Command(("结婚申请", "结婚登记"), marriage),
    Command(("小画家",), painter),
    Command(("复读",), repeat, arg_num=1, ),
    Command(("防诱拐",), anti_kidnap),
    Command(("字符画",), charpic, allow_gif=True),
    Command(("共进午餐", "共进晚餐"), have_lunch),
    Command(("这是我的老婆", "我老婆"), mywife),
    Command(("胡桃平板",), walnutpad, allow_gif=True),
    Command(("胡桃放大",), walnut_zoom, allow_gif=True),
    Command(("讲课", "敲黑板"), teach, allow_gif=True, arg_num=1),
    Command(("上瘾", "毒瘾发作"), addition, allow_gif=True, arg_num=1),
    Command(("手枪",), gun),
    Command(("高血压",), blood_pressure, allow_gif=True),
    Command(("看书",), read_book, arg_num=1),
    Command(("遇到困难请拨打",), call_110),
    Command(("迷惑",), confuse, allow_gif=True),
    Command(("打穿", "打穿屏幕"), hit_screen, allow_gif=True),
    Command(("击剑",), fencing),
    Command(("抱大腿",), hug_leg),
    Command(("唐可可举牌",), tankuku_holdsign),
    Command(("无响应",), no_response),
    Command(("抱紧",), hold_tight),
    Command(("看扁",), look_flat, allow_gif=True, arg_num=2),
    Command(("看图标",), look_this_icon, allow_gif=True, arg_num=1),
    Command(("舰长",), captain),
    Command(("急急国王",), jiji_king, arg_num=2),
    Command(("不文明",), incivilization, arg_num=1),
    Command(("一起",), together, arg_num=1),
    Command(("波纹",), wave, allow_gif=True),
    Command(("诈尸", "秽土转生"), rise_dead),
    Command(("卡比锤", "卡比重锤"), kirby_hammer, allow_gif=True, arg_num=1),
    Command(("木鱼",), wooden_fish),
    Command(("凯露指",), karyl_point),
    Command(("踢球",), kick_ball),
    Command(("砸",), smash, allow_gif=True),
    Command(("波奇手稿",), bocchi_draft),
    Command(("坐得住", "坐不住", "坐的住"), sit_still, arg_num=1),
    Command(("偷学",), learn, arg_num=1),
    Command(("恍惚", "开冲"), trance),
    Command(("恐龙", "小恐龙"), dinosaur, allow_gif=True),
    Command(("挠头",), scratch_head),
    Command(("鼓掌",), applaud),
    Command(("追列车", "追火车"), chase_train),
    Command(("万花筒", "万花镜"), kaleidoscope, allow_gif=True, arg_num=1),
    Command(("加班",), overtime),
    Command(("头像公式",), avatar_formula),

]


async def download_image(user: UserInfo, allow_gif: bool = False):
    img = None
    if user.qq:
        img = await download_avatar(user.qq)
    elif user.img_url:
        img = await download_url(user.img_url)

    if img:
        def to_jpg(frame: IMG, bg_color=(255, 255, 255)) -> IMG:
            if frame.mode == "RGBA":
                bg = Image.new("RGB", frame.size, bg_color)
                bg.paste(frame, mask=frame.split()[3])
                return bg
            else:
                return frame.convert("RGB")

        def to_image(data: bytes, is_allow_gif: bool = False) -> IMG:
            image = Image.open(BytesIO(data))
            if not is_allow_gif:
                image = to_jpg(image).convert("RGBA")
            return image

        user.img = BuildImage(to_image(img, allow_gif))


async def make_image(
    command: Command, sender: UserInfo, users: List[UserInfo], args=None
) -> BytesIO:
    if args is None:
        args = []
    await download_image(sender, command.allow_gif)
    for user in users:
        await download_image(user, command.allow_gif)
    return await command.func(users, sender=sender, args=args)
