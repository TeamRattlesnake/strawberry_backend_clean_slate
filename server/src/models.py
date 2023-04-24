"""
Модуль с моделями
"""
from enum import Enum

from pydantic import BaseModel


class Score(int, Enum):
    """
    Модель, модержащая лайк или дизайк
    """

    LIKE = 1
    DISLIKE = -1


class FeedbackModel(BaseModel):
    """
    Модель содержащая обратную связь по
    результаты руботы сервиса

    result_id - int, номер результата работы сервиса.

    score - Score, оценка результата, -1 или 1
    """

    result_id: int
    score: Score


class GenerateQueryModel(BaseModel):
    """
    Модель для запроса генерации. Берет на вход данные для
    контекста (массив строк) и строку с запросом

    context_data - list[str], список текстов существующих
    постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит
    максимально краткую мысль, о чем писать текст

    group_id - int, айди группы, для которой генерируется пост.
    Нужно чтобы связать генерацию с группой и потом выдавать
    статистику для группы по этому айди
    """

    context_data: list[str]
    hint: str
    group_id: int


class SendFeedbackResult(BaseModel):
    """
    Модель, описывающая результат операции. Содержит код
    ошибки и текстовое описание

    status - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится
    текст исключения, если оно произошло
    """

    status: int
    message: str


class GenerateResultID(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и
    текст с полезными данными, а такжеи айди результата (для обратной связи)

    text_id - int, айди текста, по которому можно потом получить результат
    """

    text_id: int


class GenerateResultStatus(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и
    текст с полезными данными, а такжеи айди результата (для обратной связи)

    text_status - int, статус генерации. 0 - не готово, 1 - готово
    """

    text_status: int


class GenerateResultData(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и
    текст с полезными данными, а такжеи айди результата (для обратной связи)

    text_data - str, результат генерации
    """

    text_data: str


class GenerateID(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и текст с
    полезными данными, а такжеи айди результата (для обратной связи)


    status - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится текст исключения,
    если оно произошло

    data - GenerateResultID, text_int, айди текста, по которому
    можно потом получить результат
    """

    status: int
    message: str
    data: GenerateResultID


class GenerateStatus(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и текст с
    полезными данными, а такжеи айди результата (для обратной связи)


    status - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится текст исключения,
    если оно произошло

    data - GenerateResultStatus, text_status, статус генерации. 0 - не готово, 1 - готово, 2 - ошибка
    """

    status: int
    message: str
    data: GenerateResultStatus


class GenerateResult(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и текст с
    полезными данными, а такжеи айди результата (для обратной связи)


    status - int, статус операции:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    * 6 - db error

    message - str, текстовое описание статуса. Тут хранится текст исключения,
    если оно произошло

    data - GenerateResultData, text_data - str, результат генерации
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

    date : int, unix дата, когда был отправлен запрос

    group_id : int, айди группы, для которой сделан пост

    status : str, [READY, NOT_READY, ERROR] - описание статуса запроса

    gen_time : int - количество миллисекунд, затраченных на генерацию. date + gen_time = дата, когда генерация закончена
    """

    post_id: int
    user_id: int
    method: str
    hint: str
    text: str
    rating: int
    date: float
    group_id: int
    status: str
    gen_time: float


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

    message - str, текстовое описание статуса. Тут хранится текст
    исключения, если оно произошло

    data - GenerateResultInfo, список результатов генерации юзера

    count - int, длина массива data
    """

    status: int
    message: str
    data: list[GenerateResultInfo]
    count: int
