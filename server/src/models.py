"""
Модуль с моделями
"""

from pydantic import BaseModel


class OperationResult(BaseModel):
    """
    Модель, описывающая результат операции. Содержит код ошибки и текстовое описание

    code - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API Auth error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится текст исключения, если оно произошло
    """
    code: int
    message: str


class GenerateQueryModel(BaseModel):
    """
    Модель для запроса генерации. Берет на вход данные для контекста (массив строк) и строку с запросом

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит максимально краткую мысль, о чем писать текст
    """
    context_data: list[str]
    hint: str


class GenerateResultModel(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и текст с полезными данными, а такжеи айди результата (для обратной связи)


    status - OperationResult, статус операции и строка с пояснением

    text_data - str, результат генерации

    result_id - int, айди результата генерации для отправки фидбека по нему
    """
    status: OperationResult
    text_data: str
    result_id: int


class FeedbackModel(BaseModel):
    """
    Модель содержащая обратную связь по результаты руботы сервиса

    result_id - номер результата работы сервиса.

    score - изменение оценки 1 или -1 (хотя можно и любое другое целое число)
    """
    result_id: int
    score: int
