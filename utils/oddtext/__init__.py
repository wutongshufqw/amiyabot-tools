from typing import List, Optional

from .data_source import commands, Command


class OddText:
    @property
    def keywords(self) -> List[str]:
        keys = []
        for command in commands:
            key = command.keywords
            for k in key:
                keys.append(k)
        return keys

    @classmethod
    def get_command(cls, keyword: str) -> Optional[Command]:
        for command in commands:
            if keyword in command.keywords:
                return command
        return None
