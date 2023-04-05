"""
Главный модуль с сервером FastAPI
"""

import logging
import time

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from models import OperationResult, GenerateQueryModel, GenerateResultModel, FeedbackModel
from config import Config
from utils import is_valid, parse_query_string

logging.basicConfig(format="%(asctime)s %(message)s", handlers=[logging.FileHandler(
    f"/home/logs/log_{time.ctime()}.txt", mode="w", encoding="UTF-8")], datefmt="%H:%M:%S %z", level=logging.INFO)

app = FastAPI()
config = Config("config.json")

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DESCRIPTION = """
Выпускной проект ОЦ VK в МГТУ команды Team Rattlesnake. Сервис, генерирующий контент для социальной сети ВКонтакте. Посты генерируются сами с помощью нейросетей, также можно сократить текст, перефразировать его и заменить слово на более подходящее. Станьте популярным в сети с помощью Strawberry!

* Коленков Андрей - Team Lead, Backend Python Dev 🍓
* Роман Медников - Frontend React Dev 🍓
* Василий Ермаков - Data Scientist 🍓

"""


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry🍓",
        version="0.0.1 - Clean Slate",
        description=DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.post('/send_feedback', response_model=OperationResult)
async def send_feedback(data: FeedbackModel, Authorization=Header()):
    """
    Оценить результат по айди
    """
    auth_data = parse_query_string(Authorization)

    if not is_valid(query=auth_data, secret=config.client_secret):
        return OperationResult(code=1, message="Ошибка авторизации")

    result_id = data.result_id
    score = data.score

    return OperationResult(code=5, message="Метод пока не реализован")


@app.post("/generate_text", response_model=GenerateResultModel)
async def generate_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Пишет целый пост по текстовому описанию
    """

    auth_data = parse_query_string(Authorization)

    if not is_valid(query=auth_data, secret=config.client_secret):
        return GenerateResultModel(status=OperationResult(code=1, message="Ошибка авторизации"), text_data="", result_id=-1)

    texts = data.context_data
    hint = data.hint

    result = "Outaspace to find another race"
    result_id = 0

    return GenerateResultModel(status=OperationResult(code=5, message="Метод пока не реализован"), text_data=result, result_id=result_id)


@app.post("/append_text", response_model=GenerateResultModel)
async def append_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Добавляет несколько слов к затравке и возвращает все вместе
    """

    auth_data = parse_query_string(Authorization)

    if not is_valid(query=auth_data, secret=config.client_secret):
        return GenerateResultModel(status=OperationResult(code=1, message="Ошибка авторизации"), text_data="", result_id=-1)

    texts = data.context_data
    hint = data.hint

    result = "Outaspace to find another race"
    result_id = 0

    return GenerateResultModel(status=OperationResult(code=5, message="Метод пока не реализован"), text_data=result, result_id=result_id)


@app.post("/rephrase_text", response_model=GenerateResultModel)
async def rephrase_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Перефразирует поданный текст
    """

    auth_data = parse_query_string(Authorization)

    if not is_valid(query=auth_data, secret=config.client_secret):
        return GenerateResultModel(status=OperationResult(code=1, message="Ошибка авторизации"), text_data="", result_id=-1)

    texts = data.context_data
    hint = data.hint

    result = "Outaspace to find another race"
    result_id = 0

    return GenerateResultModel(status=OperationResult(code=5, message="Метод пока не реализован"), text_data=result, result_id=result_id)


@app.post("/summarize_text", response_model=GenerateResultModel)
async def summarize_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Резюмирует поданный текст
    """

    auth_data = parse_query_string(Authorization)

    if not is_valid(query=auth_data, secret=config.client_secret):
        return GenerateResultModel(status=OperationResult(code=1, message="Ошибка авторизации"), text_data="", result_id=-1)

    texts = data.context_data
    hint = data.hint

    result = "Outaspace to find another race"
    result_id = 0

    return GenerateResultModel(status=OperationResult(code=5, message="Метод пока не реализован"), text_data=result, result_id=result_id)


@app.post("/extend_text", response_model=GenerateResultModel)
async def extend_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Удлиняет поданный текст
    """

    auth_data = parse_query_string(Authorization)

    if not is_valid(query=auth_data, secret=config.client_secret):
        return GenerateResultModel(status=OperationResult(code=1, message="Ошибка авторизации"), text_data="", result_id=-1)

    texts = data.context_data
    hint = data.hint

    result = "Outaspace to find another race"
    result_id = 0

    return GenerateResultModel(status=OperationResult(code=5, message="Метод пока не реализован"), text_data=result, result_id=result_id)


@app.post("/unmask_text", response_model=GenerateResultModel)
async def unmask_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Заменяет [MASK] на наиболее подходящие слова
    """

    auth_data = parse_query_string(Authorization)

    if not is_valid(query=auth_data, secret=config.client_secret):
        return GenerateResultModel(status=OperationResult(code=1, message="Ошибка авторизации"), text_data="", result_id=-1)

    texts = data.context_data
    hint = data.hint

    result = "Outaspace to find another race"
    result_id = 0

    return GenerateResultModel(status=OperationResult(code=5, message="Метод пока не реализован"), text_data=result, result_id=result_id)
