"""
Модуль с реализацией общения с апи нейросетей
"""

import json

from revChatGPT.V1 import Chatbot

MAX_WORDS_LEN = 2700


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
        self.chatbot = Chatbot(config={
            "access_token": self.token,
        })
        self.context = ""
        self.query = ""
        self.result = ""

    def load_context(self, path: str):
        try:
            with open(path, "r", encoding="UTF-8") as ctx_file:
                self.context = ctx_file.read()
        except Exception as exc:
            raise NNException(f"Error in load_context: {exc}") from exc

    def prepare_query(self, context_data: list[str], hint: str):
        sourse_texts_quoted = ['"'+text+'"' for text in context_data]
        sourse_texts_string = ""

        if len(hint.split(" ")) >= MAX_WORDS_LEN:
            raise NNException(
                "Error in prepare_query: the request is too long (hint alone is larger than allowed input in model)")

        for text in sourse_texts_quoted:
            while len(sourse_texts_quoted.split(" ")) + len(text.split(" ")) + len(hint.split(" ")) <= MAX_WORDS_LEN:
                sourse_texts_string += f"{text}, "

        # Обрезать запятую и пробел
        sourse_texts_string = sourse_texts_string[:-2]

        self.query = self.context.replace("[1]", sourse_texts_string)
        self.query = self.query.replace("[2]", hint)
        self.query = self.query.strip()

    def send_request(self):
        try:
            for data in self.chatbot.ask(self.query):
                self.result = data["message"]

            json_response = json.loads(self.result)
            if json_response["error"] is None:
                self.result = json_response["result"]
            else:
                raise NNException(
                    f"Error in send_request (generation failed): {json_response['error']}")

        except Exception as exc:
            raise NNException(f"Error in send_request: {exc}") from exc

    def get_result(self) -> str:
        return self.result
