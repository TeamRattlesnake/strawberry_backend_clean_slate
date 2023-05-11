"""
Модуль с классом, который дает доступ к конфигу
"""

import json

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
        self.append_context_path = data["append_context_path"]
        self.rephrase_context_path = data["rephrase_context_path"]
        self.summarize_context_path = data["summarize_context_path"]
        self.extend_context_path = data["extend_context_path"]
        self.unmask_context_path = data["unmask_context_path"]

        self.api_tokens = {token: READY for token in data["api_tokens"]}

        if len(self.api_tokens) == 0:
            raise Exception("No api tokens in config file")

    def next_token(self) -> str:
        """
        Возвращает свободный токен и помечает его как занятый
        """
        for token in self.api_tokens:
            if self.api_tokens[token] == READY:
                self.api_tokens[token] = BUSY
                return token
        return None

    def free_token(self, token: str):
        """
        Освобождает токен
        """
        if token in self.api_tokens:
            self.api_tokens[token] = READY

    def ready(self) -> bool:
        """
        Возвращает статус
        """
        for token in self.api_tokens:
            if self.api_tokens[token] == READY:
                return True
        return False
