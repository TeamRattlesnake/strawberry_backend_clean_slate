"""
Модуль с моделями
"""

from pydantic import BaseModel


class OperationResult(BaseModel):
    """
    Модель, описывающая результат операции. Содержит код ошибки и текстовое описание
    Статусы:
    * 0 - OK
    * 1 - VK API Auth error
    * 2 - NN API Auth error
    * 3 - request error
    * 4 - unknown error
    * 5 - not implemented
    """
    code: int
    message: str


class GenerateQueryModel(BaseModel):
    """
    Модель для запроса генерации. Берет на вход данные для контекста (массив строк) и затравку
    """
    context_data: list[str]
    hint: str


class GenerateResultModel(BaseModel):
    """
    Модель с результатами генерации. Возвращает статус операции и текст с полезными данными, а также словарь вспомогательных данных и айди результата (для обратной связи)

    """
    status: OperationResult
    text_data: str
    result_id: int


class FeedbackModel(BaseModel):
    """
    Модель содержащая обратную связь, принимает айди результата и оценку (+1 или -1)
    """
    result_id: int
    score: int
