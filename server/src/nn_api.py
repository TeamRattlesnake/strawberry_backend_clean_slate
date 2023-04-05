"""
Модуль с реализацией общения с апи нейросетей
"""

import requests


class NNException(Exception):
    """
    Класс исключения, связанного с подготовкой данных и отправкой запроса на апи нейросетей
    """
    pass


class GenApi:
    """
    Класс для подготовки данных и отправки запроса для генерации текста
    """

    def __init__(self):
        pass

    def load_context(self, path: str):
        pass

    def prepate_query(self, context_data: list[str], hint: str):
        pass

    def send_request(self):
        pass

    def get_result(self) -> str:
        return ""


class AppendApi:
    """
    Класс для подготовки данных и отправки запроса для добавления текста
    """

    def __init__(self):
        pass

    def load_context(self, path: str):
        pass

    def prepate_query(self, context_data: list[str], hint: str):
        pass

    def send_request(self):
        pass

    def get_result(self) -> str:
        return ""


class RephraseApi:
    """
    Класс для подготовки данных и отправки запроса для перефразирования текста
    """

    def __init__(self):
        pass

    def load_context(self, path: str):
        pass

    def prepate_query(self, context_data: list[str], hint: str):
        pass

    def send_request(self):
        pass

    def get_result(self) -> str:
        return ""


class SummarizeApi:
    """
    Класс для подготовки данных и отправки запроса для сокращения текста
    """

    def __init__(self):
        pass

    def load_context(self, path: str):
        pass

    def prepate_query(self, context_data: list[str], hint: str):
        pass

    def send_request(self):
        pass

    def get_result(self) -> str:
        return ""


class ExtendApi:
    """
    Класс для подготовки данных и отправки запроса для удлинения текста
    """

    def __init__(self):
        pass

    def load_context(self, path: str):
        pass

    def prepate_query(self, context_data: list[str], hint: str):
        pass

    def send_request(self):
        pass

    def get_result(self) -> str:
        return ""


class UnmaskApi:
    """
    Класс для подготовки данных и отправки запроса для подстановки слов в [MASK]
    """

    def __init__(self):
        pass

    def load_context(self, path: str):
        pass

    def prepate_query(self, context_data: list[str], hint: str):
        pass

    def send_request(self):
        pass

    def get_result(self) -> str:
        return ""
