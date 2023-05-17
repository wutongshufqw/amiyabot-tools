import asyncio
import base64
from io import BytesIO

from playwright.async_api import async_playwright, Page
from core import log

waifu_url = "https://waifulabs.com/generate"


class Waifu:
    def __init__(self, proxy=None, url=waifu_url, water_mark=True) -> None:
        self.browser = None
        self.page = None
        self.url = url
        self.water_mark = water_mark
        self.proxy = proxy

    async def gey_browser(self):
        url = self.url
        pw = await async_playwright().start()
        if self.proxy:
            browser = await pw.chromium.launch(headless=True, proxy={"server": f'{self.proxy}'})
        else:
            browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await asyncio.wait_for(page.goto(url), timeout=2000)
        except Exception as e:
            log.error(e)
            return None
        self.page = page
        self.browser = browser
        return True

    async def shot(
        self, page: Page, ShotSelector: str, WaitSelector: str = None
    ) -> BytesIO:
        if WaitSelector:
            try:
                await page.wait_for_selector(WaitSelector, timeout=6000)
            except asyncio.TimeoutError:
                return
        await page.wait_for_timeout(3000)
        shot = await page.query_selector(ShotSelector)
        return BytesIO(await shot.screenshot(type="jpeg"))

    async def first_shot(self, page=None, browser=None) -> BytesIO:
        page = self.page
        selector = "#wizard-container > div > div > div.waifu-container > div"
        selector2 = "#wizard-container > div > div > div.waifu-container > div > div:nth-child(16) > div > div > div:nth-child(3)"
        buffer = await self.shot(
            page=page, WaitSelector=selector2, ShotSelector=selector
        )
        return buffer

    async def other_shot(self, choose: int = 1) -> list:
        page = self.page
        end_selector = "#wizard-container > div > div > div.waifu-preview.shadow.cross-fade-appear-done.cross-fade-enter-done > img"
        # 下载按钮
        selector = f"#wizard-container > div > div > div.waifu-container > div > div:nth-child({choose}) > div > div > div:nth-child(3)"
        get_page = await page.query_selector(selector)
        await get_page.click()
        try:
            byt_no_water = await self.get_product()
            await page.wait_for_selector(end_selector, timeout=2000)
            return await self.get_product() if self.water_mark else byt_no_water
        except:
            return await self.page_shot()

    async def page_shot(self) -> tuple:
        page = self.page
        selector = "#wizard-container > div > div > div.waifu-container > div > div:nth-child(16) > div > div > div:nth-child(3)"
        ChooseSelector = "#wizard-container > div > div > div.waifu-container > div"
        PicturSelector = "#wizard-container > div > div > div.waifu-preview.shadow.cross-fade-enter-done > img"
        PictureBuffer = await self.shot(
            page=page, WaitSelector=selector, ShotSelector=PicturSelector
        )  # 大图片截图
        await page.wait_for_timeout(1000)
        ChooseBuffer = await self.shot(
            page=page, WaitSelector=selector, ShotSelector=ChooseSelector
        )  # 小图片截图
        return PictureBuffer, ChooseBuffer

    async def get_product(self) -> BytesIO:
        """
        获取左边的大图片，有延迟就是有水印，无延迟就是无水印
        """
        page = self.page
        # //*[@id="wizard-container"]/div/div/div[1]/img
        # selector=f"#wizard-container > div > div > div.waifu-container > div > div:nth-child({choose}) > div > div > div:nth-child(3)"
        # get_page=await page.query_selector(selector)
        # await get_page.click()#wizard-container > div > div > div.waifu-container > div > div:nth-child(7) > div > div > div:nth-child(3)
        # PictureSelector="#wizard-container > div > div > div.waifu-preview.shadow.cross-fade-appear-done.cross-fade-enter-done > img"
        # pic=await page.wait_for_selector(PictureSelector, timeout=6000)
        # await page.wait_for_timeout(2000)
        # img_get=await pic.inner_text()
        # print(img_get)
        # ims=Image.open(str_url)
        # ims.show()
        # page.wait_for_timeout(500)
        # imgs=await page.query_selector(imgs_se)
        # imgs=await imgs.get_attribute("src")
        # imgs=imgs.split("base64,")[1]
        # str_url = BytesIO(base64.b64decode(imgs))
        # ims=Image.open(str_url)
        # ims.show()
        # buffer = BytesIO(await pic.screenshot(type='jpeg'))

        imgs_selector = '//*[@id="wizard-container"]/div/div/div[1]/img'
        imgs = await page.query_selector(imgs_selector)  # 获取图片选择器
        imgs = await imgs.get_attribute("src")
        imgs = imgs.split("base64,")[1]
        return BytesIO(base64.b64decode(imgs))

    async def close(self):
        await self.browser.close()
        return

    async def back(self):
        back_selector = "#wizard-container > div > div > div.waifu-preview.shadow.cross-fade-enter-done > div > button:nth-child(1) > span"
        page = self.page
        back = await page.query_selector(back_selector)
        await back.click()
        return await self.page_shot()

    async def continues(self):

        continues_selector = "#wizard-container > div > div > div.waifu-preview.shadow.cross-fade-enter-done > div > button:nth-child(2) > span"
        page = self.page
        continues = await page.query_selector(continues_selector)
        await continues.click()
        return await self.page_shot()
