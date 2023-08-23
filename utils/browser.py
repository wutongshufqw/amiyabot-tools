import asyncio
from core import log
from io import BytesIO
from playwright.async_api import Page, async_playwright
from typing import Optional, Tuple


class MyBrowser:
    def __init__(self, url: Optional[str] = None, proxy: Optional[str] = None):
        self.browser = None
        self.context = None
        self.page = None
        self.url = url
        self.proxy = proxy

    async def gey_browser(self, size: Optional[Tuple[int, int]] = None) -> Optional[bool]:
        url = self.url
        pw = await async_playwright().start()
        if self.proxy:
            browser = await pw.chromium.launch(headless=True, proxy={"server": f'{self.proxy}'})
        else:
            browser = await pw.chromium.launch(headless=True)
        if size:
            context = await browser.new_context(viewport={"width": size[0], "height": size[1]})
        else:
            context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(url, timeout=60000)
        except Exception as e:
            log.error(e)
            return None
        self.page = page
        self.context = context
        self.browser = browser
        return True

    async def shot(
        self, page: Page, shot_selector: str = 'body', wait_selector: str = None
    ) -> Optional[BytesIO]:
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=6000)
            except asyncio.TimeoutError:
                return
        await page.wait_for_timeout(3000)
        shot = await page.query_selector(shot_selector)
        return BytesIO(await shot.screenshot(type="jpeg"))

    async def shot_selector(self, shot_selector: str = 'body', wait_selector: str = None) -> Optional[BytesIO]:
        page = self.page
        buffer = await self.shot(page, shot_selector, wait_selector)
        return buffer

    async def screenshot(self, full_page: bool = False) -> Optional[BytesIO]:
        page = self.page
        return BytesIO(await page.screenshot(full_page=full_page, type="jpeg"))

    async def input(self, selector: str, text: str) -> None:
        page = self.page
        await page.fill(selector, text)

    async def click(self, selector: str) -> None:
        page = self.page
        body = await page.query_selector('body')
        element = await body.wait_for_selector(selector, state='attached')
        await element.click()

    # 等待页面加载完成
    async def wait_for_page(self) -> None:
        page = self.page
        await page.wait_for_load_state('networkidle')

    async def wait_for_selector(self, selector: str) -> None:
        page = self.page
        await page.wait_for_selector(selector)

    async def close(self) -> None:
        await self.browser.close()
