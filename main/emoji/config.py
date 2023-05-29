from typing import List

from ..main import bot


class UserConfig:
    @staticmethod
    def meme_command_start() -> str:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return ''
        return config_.get('prefix', '')

    @staticmethod
    def memes_prompt_params_error() -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('tips', True)

    @staticmethod
    def memes_check_resources_on_startup() -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('update', True)

    @staticmethod
    def memes_use_sender_when_no_image() -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('use_avatar', True)

    @staticmethod
    def memes_use_default_when_no_text() -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('use_default', True)

    @staticmethod
    def meme_disabled_list() -> List[str]:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return []
        return config_.get('disabled', [])
