"""
Модуль с моделями
"""
from datetime import datetime

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


class GenerateResultInfo(BaseModel):
    """
    Модель с информации об одном результате генерации.

    post_id - int, айди поста в базе данных. На фронтенде наверное не понадобится

    user_id : int, айди юзера, который сделал пост, тоже не понадобится

    method : str, название метода, которым сделан этот текст

    hint : str, затравка/тема поста, введенные пользователем для генерации

    text : str, сам текст, который сделала нейросеть

    rating : int, оценка поста, целое число (Задать посту оценку - см. /send_feedback)

    date : datetime, дата и время, когда нейросеть создала результат, UTC +00
    """

    post_id: int
    user_id: int
    method: str
    hint: str
    text: str
    rating: int
    date: datetime


class UserResults(BaseModel):
    """
    Модель со списком данных обо всех постах, которые сделал юзер (с пагинацией)

    status - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится текст исключения, если оно произошло

    data - GenerateResultInfo, список результатов генерации юзера
    """

    status: int
    message: str
    data: list[GenerateResultInfo]
