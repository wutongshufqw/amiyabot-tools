import json
import os
import shutil
import sys

from core import log, GitAutomation

from .utils import help_image, TrieHandle
from .data_source import commands, make_image
from .config import petpet_command_start as cmd_prefix
from .models import UserInfo
from .data_source import download_avatar
from .download import DownloadError

banned_command = {
    "global": [],
}
banned_config_path = os.path.join(os.path.dirname(__file__), "banned.json")
petpet_handler = TrieHandle()
resources_dir = 'resource/plugins/tools'


def install_emoji():
    shutil.copy(os.path.join(os.path.dirname(__file__), '..', 'requirements.txt'), resources_dir)
    log.info('检查资源文件更新...')
    git_url = 'https://gitlab.com/wutongshufqw/emoji-resources.git'
    GitAutomation(os.path.join(resources_dir, 'emoji_resources'), git_url).update()
    log.info('更新完成')
    # copy resources from bot resource
    shutil.rmtree(os.path.join(os.path.dirname(__file__), 'resources'), ignore_errors=True)
    shutil.copytree(os.path.join(resources_dir, 'emoji_resources'),
                    os.path.join(os.path.dirname(__file__), 'resources'),
                    ignore=shutil.ignore_patterns('*.git*', '*.git', 'README.md'))
    global banned_command, petpet_handler
    if not os.path.exists(banned_config_path):
        open(banned_config_path, 'w').close()
    try:
        banned_command = json.load(open(banned_config_path, encoding='utf-8'))
    except json.decoder.JSONDecodeError:
        banned_command = {
            "global": [],
        }

    if petpet_handler is None:
        petpet_handler = TrieHandle()
    for command in commands:
        for prefix in command.keywords:
            ok = petpet_handler.add(f"{cmd_prefix}{prefix}", command)
            if not ok:
                log.warning(f"Failed to add existing trigger {prefix}")

    log.info('petpet register done.')
