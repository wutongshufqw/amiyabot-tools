import json
import os
import sys

from core import log

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


def install_emoji():
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
