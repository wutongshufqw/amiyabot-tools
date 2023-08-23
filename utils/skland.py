from pathlib import Path
from typing import Tuple, Union

import asyncio
from core import log

from .browser import MyBrowser


class SklandPlus:
    def __init__(self, cred: str, url: str, proxy: str = None):
        self.browser = MyBrowser(url, proxy)
        self.cred = cred

    async def login(self) -> Tuple[Union[bytes, str], str]:
        try:
            stat = await self.browser.gey_browser((1080, 1920))
        except Exception as e:
            log.error(e)
            await self.close()
            return '资源加载失败, 请稍后再试或联系管理员', 'error'
        if not stat:
            await self.close()
            return '资源加载失败, 请稍后再试或联系管理员', 'error'
        await self.browser.input('.p-inputtext', self.cred)
        await self.browser.click('.p-button')
        try:
            await self.browser.click('.p-button-success')
        except Exception:
            await self.close()
            return '登录失败, 您的凭证不正确, 请重新录入', 'warning'
        await self.browser.wait_for_selector(
            '#root > div > div:nth-child(2) > div:nth-child(1) > div > div > div > div > div:nth-child(3)'
        )
        pic = await self.browser.screenshot()
        return pic.getvalue(), 'success'

    async def choose_account(self, index: int) -> Tuple[Union[bytes, str], str]:
        try:
            await self.browser.click(
                f'#root > div > div:nth-child(2) > div:nth-child(1) > div > div > div > div > div:nth-child(3) > div:nth-child({index}) > button'
            )
        except Exception:
            return '选择账户失败, 请重试', 'warning'
        await self.browser.wait_for_selector(
            'div:text("助战干员")'
        )
        await asyncio.sleep(2)
        pic = await self.browser.screenshot(full_page=True)
        await self.close()
        return pic.getvalue(), 'success'

    async def close(self) -> None:
        await self.browser.close()

    @staticmethod
    async def get_tip() -> bytes:
        pic_path = Path(__file__).parent / 'resource' / 'skland' / 'tip.png'
        return pic_path.read_bytes()
