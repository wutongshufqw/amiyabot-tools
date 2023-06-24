from typing import List

from ..main import bot


class UserConfig:
    @property
    def meme_command_start(self) -> str:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return ''
        return config_.get('prefix', '')

    @property
    def memes_prompt_params_error(self) -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('tips', True)

    @property
    def memes_check_resources_on_startup(self) -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('update', True)

    @property
    def memes_use_sender_when_no_image(self) -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('use_avatar', True)

    @property
    def memes_use_default_when_no_text(self) -> bool:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return True
        return config_.get('use_default', True)

    @property
    def meme_disabled_list(self) -> List[str]:
        config_ = bot.get_config('emoji')
        if config_ is None:
            return []
        return config_.get('disabled', [])


user_config = UserConfig()
