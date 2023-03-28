import json
import re
import time
from collections import OrderedDict
from io import BytesIO

import requests
from PIL import Image
from amiyabot import log
from amiyabot.network.download import download_async
from amiyabot.util import run_in_thread_pool

# !/usr/bin/env python -u This script requires Python 3+, Requests, and Pillow, a modern fork of PIL, the Python
# Imaging Library: 'easy_install Pillow' and 'easy_install requests' For Windows easy_install setup, download and
# run: https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py After Installation of easy_install,
# it will be located in the python scripts directory.

# This is a basic, likely broken example of how to use the very beta saucenao API... There are several significant
# holes in the api, and in the way in which the site responds and reports error conditions. These holes will likely
# be filled at some point in the future, and it may impact the status checks used below.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE. ################CONFIG##################


minsim = '80!'  # forcing minsim to 80 is generally safe for complex images, but may miss some edge cases. If images
# being checked are primarily low detail, such as simple sketches on white paper, increase this to cut down on false
# positives.

# #############END CONFIG#################

thumbSize = (250, 250)

# enable or disable indexes
index_hmags = '0'
index_reserved = '0'
index_hcg = '0'
index_ddbobjects = '0'
index_ddbsamples = '0'
index_pixiv = '1'
index_pixivhistorical = '1'
index_seigaillust = '1'
index_danbooru = '0'
index_drawr = '1'
index_nijie = '1'
index_yandere = '0'
index_animeop = '0'
index_shutterstock = '0'
index_fakku = '0'
index_hmisc = '0'
index_2dmarket = '0'
index_medibang = '0'
index_anime = '0'
index_hanime = '0'
index_movies = '0'
index_shows = '0'
index_gelbooru = '0'
index_konachan = '0'
index_sankaku = '0'
index_animepictures = '0'
index_e621 = '0'
index_idolcomplex = '0'
index_bcyillust = '0'
index_bcycosplay = '0'
index_portalgraphics = '0'
index_da = '1'
index_pawoo = '0'
index_madokami = '0'
index_mangadex = '0'

# generate appropriate bitmask
db_bitmask = int(
    index_mangadex + index_madokami + index_pawoo + index_da + index_portalgraphics + index_bcycosplay + index_bcyillust
    + index_idolcomplex + index_e621 + index_animepictures + index_sankaku + index_konachan + index_gelbooru
    + index_shows + index_movies + index_hanime + index_anime + index_medibang + index_2dmarket + index_hmisc
    + index_fakku + index_shutterstock + index_reserved + index_animeop + index_yandere + index_nijie + index_drawr
    + index_danbooru + index_seigaillust + index_anime + index_pixivhistorical + index_pixiv + index_ddbsamples
    + index_ddbobjects + index_hcg + index_hanime + index_hmags, 2)
log.info("dbmask=" + str(db_bitmask))

long_cool = 0
short_cool = 0


async def get_saucenao(imageURL, api_key: str, proxy: str = None):
    global long_cool
    global short_cool
    if time.time() - long_cool < 21600:
        return False, '超过每日API限制, 请六小时后重试...', {}
    if time.time() - short_cool < 30:
        return False, '频率过高! 请30s后重试...', {}
    image_bytes = await download_async(imageURL)
    if image_bytes is None:
        return False, '下载图片失败...', {}
    image_data = BytesIO(image_bytes)
    image = Image.open(image_data)
    image.thumbnail(thumbSize, Image.ANTIALIAS)
    image_data = BytesIO()
    image.save(image_data, format='PNG')

    url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim=' + minsim + '&dbmask=' + str(
        db_bitmask) + '&api_key=' + api_key
    files = {'file': ("image.png", image_data.getvalue())}
    image_data.close()

    process_results = True
    while True:
        if proxy:
            r = await run_in_thread_pool(requests.post, url, files=files,
                                         proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy})
        else:
            r = await run_in_thread_pool(requests.post, url, files=files)
        if r.status_code != 200:
            if r.status_code == 403:
                return False, 'API Key 错误，请联系管理员...', {}
            else:
                # generally non 200 statuses are due to either overloaded servers or the user is out of searches
                return False, "status code: " + str(r.status_code), {}
        else:
            results = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(r.text)
            if int(results['header']['user_id']) > 0:
                # api responded
                log.info('Remaining Searches 30s|24h: ' + str(results['header']['short_remaining']) + '|' + str(
                    results['header']['long_remaining']))
                if int(results['header']['status']) == 0:
                    # search succeeded for all indexes, results usable
                    break
                else:
                    if int(results['header']['status']) > 0:
                        # One or more indexes are having an issue. This search is considered partially successful,
                        # even if all indexes failed, so is still counted against your limit. The error may be
                        # transient, but because we don't want to waste searches, allow time for recovery.
                        log.info('API Error. Retrying in 600 seconds...')
                        time.sleep(600)
                    else:
                        # Problem with search as submitted, bad image, or impossible request.
                        # Issue is unclear, so don't flood requests.
                        log.info('Bad image or other request error. Skipping in 10 seconds...')
                        process_results = False
                        time.sleep(10)
                        break
            else:
                # General issue, api did not respond. Normal site took over for this error state.
                # Issue is unclear, so don't flood requests.
                log.info('Bad image, or API failure. Skipping in 10 seconds...')
                process_results = False
                time.sleep(10)
                break

    if process_results:
        # print(results)
        if int(results['header']['long_remaining']) < 0:
            long_cool = time.time()
        if int(results['header']['short_remaining']) < 0:
            short_cool = time.time()

        if int(results['header']['results_returned']) > 0:
            # get vars to use
            member_id = -1
            index_id = results['results'][0]['header']['index_id']
            page_string = ''
            page_match = re.search('(_p[\d]+)\.', results['results'][0]['header']['thumbnail'])
            if page_match:
                page_string = page_match.group(1)

            if index_id == 5 or index_id == 6:
                # 5->pixiv 6->pixiv historical
                service_name = 'pixiv'
                member_id = results['results'][0]['data']['member_id']
                illust_id = results['results'][0]['data']['pixiv_id']
            elif index_id == 8:
                # 8->nico nico seiga
                service_name = 'seiga'
                member_id = results['results'][0]['data']['member_id']
                illust_id = results['results'][0]['data']['seiga_id']
            elif index_id == 10:
                # 10->drawr
                service_name = 'drawr'
                member_id = results['results'][0]['data']['member_id']
                illust_id = results['results'][0]['data']['drawr_id']
            elif index_id == 11:
                # 11->nijie
                service_name = 'nijie'
                member_id = results['results'][0]['data']['member_id']
                illust_id = results['results'][0]['data']['nijie_id']
            elif index_id == 34:
                # 34->da
                service_name = 'da'
                illust_id = results['results'][0]['data']['da_id']
            else:
                # unknown
                return False, '图片来源无法解析...', {}

            # 来源
            picture_url = results['results'][0]['data']['ext_urls'][0]

            return True, "来源: " + service_name + "\n作者id: " + str(member_id) + "\n作品id: " + str(
                illust_id) + page_string + "\n相似度: " + str(
                results['results'][0]['header']['similarity']) + "%\n图片链接: " + picture_url, {
                'service_name': service_name, 'member_id': member_id, 'illust_id': illust_id,
                'page_string': page_string, 'picture_url': picture_url}
        else:
            return False, '没有结果... ;_;', {}
