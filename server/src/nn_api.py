"""
Модуль с реализацией общения с апи нейросетей
"""

import json

from revChatGPT.V1 import Chatbot

MAX_WORDS_LEN = 2800
NO_SOURCE_TEXTS_REPLACEMENT = "There are no past texts, just be creative. You must write your answer in the language of the given text"


class NNException(Exception):
    """
    Класс исключения, связанного с подготовкой данных и отправкой запроса на апи нейросетей
    """

    pass


class NNApi:
    """
    Базовый класс. Нужно реализовать только prepare_query
    """

    def __init__(self, token):
        self.token = token
        self.chatbot = Chatbot(
            config={
                "access_token": self.token,
                "model": "gpt-4",
            }
        )
        self.context = ""
        self.query = ""
        self.result = ""

    def load_context(self, path: str):
        """
        Загружает шаблон контекста из файлика
        """
        try:
            with open(path, "r", encoding="UTF-8") as ctx_file:
                self.context = ctx_file.read()
        except Exception as exc:
            raise NNException(f"Error in load_context: {exc}") from exc

    def prepare_query(self, context_data: list[str], hint: str):
        """
        Расставляет данные по шаблону контекста
        """
        try:
            sourse_texts_quoted = ['"' + text + '"' for text in context_data]
            source_texts_string = ""

            if len(hint) >= MAX_WORDS_LEN:
                raise NNException(
                    "Error in prepare_query: the request is too long (hint alone is larger than allowed input in model)"
                )

            for text in sourse_texts_quoted:
                # Собираем строку с постами чтобы она была не длиннее, чем нужно.
                # Считаю не количество слов, а количество букв потому что токенизатор не любит русский
                if (len(source_texts_string) + len(text) + len(hint)) >= MAX_WORDS_LEN:
                    continue
                source_texts_string += f"{text}, "
            # Обрезать запятую и пробел
            source_texts_string = source_texts_string[:-2]

            if (
                len(source_texts_string) > 5
            ):  # Минимальная проверка на валидность контекста
                self.query = self.context.replace("[1]", source_texts_string)
            else:
                self.query = self.context.replace("[1]", NO_SOURCE_TEXTS_REPLACEMENT)

            self.query = self.query.replace("[2]", hint)
            self.query = self.query.strip()
        except Exception as exc:
            raise NNException(f"Error in prepare_query: {exc}") from exc

    def send_request(self):
        """
        Отправляет запрос к API ChatGPT
        """
        try:
            for data in self.chatbot.ask(self.query):
                self.result = data["message"]

            json_response = json.loads(self.result)

            if json_response["error"] is None:
                self.result = json_response["result"]
            else:
                raise NNException(
                    f"Error in send_request (generation failed): {json_response['error']}"
                )

        except Exception as exc:
            raise NNException(f"Error in send_request: {exc}") from exc

    def get_result(self) -> str:
        """
        Возвращает ответ нейросети
        """
        return self.result
