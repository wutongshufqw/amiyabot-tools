import hashlib

from amiyabot.network.download import download_async
from dataclasses import dataclass
from typing import Union

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
class UnsupportedAvatar(ImageSource):
    platform: str

    async def get_image(self) -> bytes:
        raise PlatformUnsupportedError(self.platform)


def user_avatar(user_id: Union[str, int]) -> ImageSource:
    return QQAvatar(qq=str(user_id))
