import hashlib
from pathlib import Path

from amiyabot.network.download import download_async

from ..config import bottle_dir


class Bottle:
    def __init__(self, text: str = '', picture=None):
        if picture is None:
            picture = []
        self.text = text
        self.picture = picture

    def get_message(self) -> str:
        return self.text

    async def get_picture(self) -> str:
        if len(self.picture) == 0:
            return ''
        else:
            path = ''
            for image in self.picture:
                # 下载图片
                image_bytes = await download_async(image)
                # 计算图片的md5
                hash_ = hashlib.md5(image_bytes).hexdigest()
                # 保存图片
                with open(f'{bottle_dir}/{hash_}', 'wb') as f:
                    f.write(image_bytes)
                path += f'{hash_};'
            return path[:-1]
