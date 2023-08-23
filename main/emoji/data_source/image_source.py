import hashlib

from amiyabot import BotAdapterProtocol, KOOKBotInstance
from amiyabot.network.download import download_async
from dataclasses import dataclass
from typing import Union, Optional

from ..exception import PlatformUnsupportedError


@dataclass
class ImageSource:
    async def get_image(self) -> bytes:
        raise NotImplementedError


@dataclass
class ImageUrl(ImageSource):
    url: str

    async def get_image(self) -> bytes:
        return await download_async(self.url)


@dataclass
class QQAvatar(ImageSource):
    qq: str

    async def get_image(self) -> bytes:
        url = f'https://q1.qlogo.cn/g?b=qq&nk={self.qq}&s=640'
        data = await download_async(url)
        if hashlib.md5(data).hexdigest() == 'acef72340ac0e914090bd35799f5594e':
            url = f'https://q1.qlogo.cn/g?b=qq&nk={self.qq}&s=100'
            data = await download_async(url)
        return data


@dataclass
class KOOKAvatar(ImageSource):
    kook: str
    instance: KOOKBotInstance

    async def get_image(self) -> bytes:
        return await self.instance.api.get_user_avatar(self.kook)


@dataclass
class UnsupportedAvatar(ImageSource):
    platform: str

    async def get_image(self) -> bytes:
        raise PlatformUnsupportedError(self.platform)


def user_avatar(user_id: Union[str, int], adapter_type: str = 'QQ', instance: Optional[BotAdapterProtocol] = None) -> ImageSource:
    if adapter_type == 'QQ':
        return QQAvatar(qq=str(user_id))
    elif adapter_type == 'KOOK' and type(instance) is KOOKBotInstance:
        return KOOKAvatar(kook=str(user_id), instance=instance)
    else:
        return UnsupportedAvatar(platform=adapter_type)
