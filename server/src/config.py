"""
Модуль с классом, который дает доступ к конфигу
"""

import json
import itertools

READY = 1
BUSY = 0


class Config:
    """
    Класс для загрузки конфига
    """

    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="UTF-8") as cfg_file:
            data = json.load(cfg_file)

        self.client_secret = data["client_secret"]

        self.db_user = data["db_user"]
        self.db_password = data["db_password"]
        self.db_port = data["db_port"]
        self.db_host = data["db_host"]
        self.db_name = data["db_name"]

        self.gen_context_path = data["gen_context_path"]
        self.gen_from_scratch_context_path = data["gen_from_scratch_context_path"]
        self.append_context_path = data["append_context_path"]
        self.rephrase_context_path = data["rephrase_context_path"]
        self.summarize_context_path = data["summarize_context_path"]
        self.extend_context_path = data["extend_context_path"]
        self.unmask_context_path = data["unmask_context_path"]
        self.fix_grammar_context_path = data["fix_grammar_context_path"]

        if len(data["api_tokens"]) == 0:
            raise Exception("No api tokens in config file")

        self.api_tokens = itertools.cycle(data["api_tokens"])
        self.acquired = 0
        self.available_count = len(data["api_tokens"])

    def next_token(self) -> str:
        """
        Возвращает свободный токен и увеличивает счетчик
        """
        self.acquired += 1
        return next(self.api_tokens)

    def free(self):
        """
        Освобождает токен - уменьшает счетчик
        """
        self.acquired -= 1

    def ready(self) -> bool:
        """
        Возвращает статус
        """
        if self.acquired < self.available_count:
            return True
        return False
