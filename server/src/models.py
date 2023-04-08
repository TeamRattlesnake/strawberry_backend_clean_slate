"""
Модуль с моделями
"""

from pydantic import BaseModel


class FeedbackModel(BaseModel):
    """
    Модель содержащая обратную связь по результаты руботы сервиса

    result_id - int, номер результата работы сервиса.

    score - int, оценка результата
    """

    result_id: int
    score: int


class GenerateQueryModel(BaseModel):
    """
    Модель для запроса генерации. Берет на вход данные для контекста (массив строк) и строку с запросом

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит максимально краткую мысль, о чем писать текст
    """

    context_data: list[str]
    hint: str


class SendFeedbackResult(BaseModel):
    """
    Модель, описывающая результат операции. Содержит код ошибки и текстовое описание

    status - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится текст исключения, если оно произошло
    """

    status: int
    message: str


class GenerateResultData(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и текст с полезными данными, а такжеи айди результата (для обратной связи)

    text_data - str, результат генерации

    result_id - int, айди результата генерации для отправки фидбека по нему
    """

    text_data: str
    result_id: int


class GenerateResult(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и текст с полезными данными, а такжеи айди результата (для обратной связи)


    status - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится текст исключения, если оно произошло

    data - GenerateResultData, text_data - str, результат генерации, result_id - int, айди результата генерации для отправки фидбека по нему
    """

    status: int
    message: str
    data: GenerateResultData
