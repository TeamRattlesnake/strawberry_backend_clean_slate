"""
Модуль с реализацией общения с апи нейросетей
"""

from revChatGPT.V1 import Chatbot

MAX_WORDS_LEN = 2700
NO_SOURCE_TEXTS_REPLACEMENT = "There are no source texts, just be creative. You must write your answer in the language of the given text"


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
            sourse_texts_string = ""

            if len(hint.split(" ")) >= MAX_WORDS_LEN:
                raise NNException(
                    "Error in prepare_query: the request is too long (hint alone is larger than allowed input in model)"
                )

            for text in sourse_texts_quoted:
                # Собираем строку с постами чтобы она была не длиннее, чем нужно
                if (
                    len(sourse_texts_string.split(" "))
                    + len(text.split(" "))
                    + len(hint.split(" "))
                    >= MAX_WORDS_LEN
                ):
                    continue
                sourse_texts_string += f"{text}, "
            # Обрезать запятую и пробел
            sourse_texts_string = sourse_texts_string[:-2]

            if (
                len(sourse_texts_string) > 5
            ):  # Минимальная проверка на валидность контекста
                self.query = self.context.replace("[1]", sourse_texts_string)
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

        except Exception as exc:
            raise NNException(f"Error in send_request: {exc}") from exc

    def get_result(self) -> str:
        """
        Возвращает ответ нейросети
        """
        return self.result
