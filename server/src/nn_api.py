"""
Модуль с реализацией общения с апи нейросетей
"""

from revChatGPT.V1 import Chatbot


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
        pass

    def send_request(self):
        try:
            for data in self.chatbot.ask(self.query):
                result = data["message"]
            return result
        except Exception as exc:
            raise NNException(f"Error in send_request: {exc}") from exc

    def get_result(self) -> str:
        return self.result


class GenApi(NNApi):
    """
    Класс для подготовки данных и отправки запроса для генерации текста
    """

    def prepare_query(self, context_data: list[str], hint: str):
        self.query = self.context


class AppendApi(NNApi):
    """
    Класс для подготовки данных и отправки запроса для добавления текста
    """

    def prepare_query(self, context_data: list[str], hint: str):
        self.query = self.context


class RephraseApi(NNApi):
    """
    Класс для подготовки данных и отправки запроса для перефразирования текста
    """

    def prepare_query(self, context_data: list[str], hint: str):
        self.query = self.context


class SummarizeApi(NNApi):
    """
    Класс для подготовки данных и отправки запроса для сокращения текста
    """

    def prepare_query(self, context_data: list[str], hint: str):
        self.query = self.context


class ExtendApi(NNApi):
    """
    Класс для подготовки данных и отправки запроса для удлинения текста
    """

    def prepare_query(self, context_data: list[str], hint: str):
        self.query = self.context


class UnmaskApi(NNApi):
    """
    Класс для подготовки данных и отправки запроса для подстановки слов в [MASK]
    """

    def prepare_query(self, context_data: list[str], hint: str):
        self.query = self.context
