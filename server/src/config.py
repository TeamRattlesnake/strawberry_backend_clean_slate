"""
Модуль с классом, который дает доступ к конфигу
"""

import json
from itertools import cycle


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
