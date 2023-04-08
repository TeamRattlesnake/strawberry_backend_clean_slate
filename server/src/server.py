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
from database import Database, DBException
from utils import is_valid, parse_query_string, UtilsException
from nn_api import NNException, NNApi

logging.basicConfig(format="%(asctime)s %(message)s", handlers=[logging.FileHandler(
    f"/home/logs/log_{time.ctime()}.txt", mode="w", encoding="UTF-8")], datefmt="%H:%M:%S UTC", level=logging.INFO)

app = FastAPI()
config = Config("config.json")
db = Database(config.db_user, config.db_password,
              config.db_name, config.db_port, config.db_host)

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
    """
    Это нужно для кастомной страницы с документацией
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry🍓",
        version="0.5.0 - Clean Slate",
        description=DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
def startup():
    """
    При старте сервера проверить, нужна ли миграция и сделать ее, если да
    """
    logging.info("Server started")
    try:
        if db.need_migration():
            logging.info("Creating tables...")
            db.migrate()
            logging.info("Creating tables...\tOK")
    except DBException as exc:
        logging.error(f"Error while checking tables: {exc}")
        raise Exception(f"Error! {exc} Restarting...") from exc


@app.post('/send_feedback', response_model=OperationResult)
def send_feedback(data: FeedbackModel, Authorization=Header()):
    """
    Метод для отправки фидбека по результату работы сервиса.

    result_id - int, номер результата работы сервиса.

    score - int,  изменение оценки 1 или -1 (хотя можно и любое другое целое число)
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return OperationResult(code=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}")
        return OperationResult(code=3, message=f"{exc}")

    result_id = data.result_id
    score = data.score
    logging.info(f"/send_feedback\tresult_id={result_id}; score={score}")

    try:
        db.change_rating(result_id, score)
        logging.info(
            f"/send_feedback\tresult_id={result_id}; score={score}\tOK")
        return OperationResult(code=0, message="Score updated")
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return OperationResult(code=6, message=f"{exc}")


@app.post("/generate_text", response_model=GenerateResultModel)
def generate_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Метод для получения целого текста по введенному запросу

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит максимально краткую мысль, о чем писать текст
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return OperationResult(code=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}")
        return OperationResult(code=3, message=f"{exc}")

    texts = data.context_data
    hint = data.hint
    logging.info(f"/generate_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.gen_context_path)
        api.prepare_query(texts, hint)
        logging.info(
            f"Ready to send request to ChatGPT with token={api.token}; query={api.query}")
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result)
        logging.info(
            f"/generate_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResultModel(status=OperationResult(code=0, message="Text generated"), text_data=result, result_id=result_id)
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=2, message=f"{exc}"), text_data="", result_id=-1)
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=6, message=f"{exc}"), text_data="", result_id=-1)


@app.post("/append_text", response_model=GenerateResultModel)
def append_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Добавляет несколько слов или предложений к тексту запроса и возвращает эти добавленные слова

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст, к концу которого нужно добавить еще текст
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return OperationResult(code=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}")
        return OperationResult(code=3, message=f"{exc}")

    texts = data.context_data
    hint = data.hint
    logging.info(f"/append_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.append_context_path)
        api.prepare_query(texts, hint)
        logging.info(
            f"Ready to send request to ChatGPT with token={api.token}; query={api.query}")
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result)
        logging.info(f"/append_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResultModel(status=OperationResult(code=0, message="Text appended"), text_data=result, result_id=result_id)
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=2, message=f"{exc}"), text_data="", result_id=-1)
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=6, message=f"{exc}"), text_data="", result_id=-1)


@app.post("/rephrase_text", response_model=GenerateResultModel)
def rephrase_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Перефразирует поданный текст, возвращает текст примерно той же длины, но более складный по содержанию

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст, который надо перефразировать
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return OperationResult(code=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}")
        return OperationResult(code=3, message=f"{exc}")

    texts = data.context_data
    hint = data.hint
    logging.info(f"/rephrase_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.rephrase_context_path)
        api.prepare_query(texts, hint)
        logging.info(
            f"Ready to send request to ChatGPT with token={api.token}; query={api.query}")
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result)
        logging.info(
            f"/rephrase_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResultModel(status=OperationResult(code=0, message="Text rephrased"), text_data=result, result_id=result_id)
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=2, message=f"{exc}"), text_data="", result_id=-1)
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=6, message=f"{exc}"), text_data="", result_id=-1)


@app.post("/summarize_text", response_model=GenerateResultModel)
def summarize_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Резюмирует поданный текст. Возвращает главную мысль текста в запросе в одно предложение

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст (лучше длинный), который надо сжать
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return OperationResult(code=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}")
        return OperationResult(code=3, message=f"{exc}")

    texts = data.context_data
    hint = data.hint
    logging.info(f"/summarize_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.summarize_context_path)
        api.prepare_query(texts, hint)
        logging.info(
            f"Ready to send request to ChatGPT with token={api.token}; query={api.query}")
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result)
        logging.info(
            f"/summarize_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResultModel(status=OperationResult(code=0, message="Text summarized"), text_data=result, result_id=result_id)
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=2, message=f"{exc}"), text_data="", result_id=-1)
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=6, message=f"{exc}"), text_data="", result_id=-1)


@app.post("/extend_text", response_model=GenerateResultModel)
def extend_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Удлиняет поданный текст, работает как перефразирование, но еще и удлиняет

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст, который надо удлинить
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return OperationResult(code=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}")
        return OperationResult(code=3, message=f"{exc}")

    texts = data.context_data
    hint = data.hint
    logging.info(f"/extend_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.extend_context_path)
        api.prepare_query(texts, hint)
        logging.info(
            f"Ready to send request to ChatGPT with token={api.token}; query={api.query}")
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result)
        logging.info(f"/extend_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResultModel(status=OperationResult(code=0, message="Text extended"), text_data=result, result_id=result_id)
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=2, message=f"{exc}"), text_data="", result_id=-1)
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=6, message=f"{exc}"), text_data="", result_id=-1)


@app.post("/unmask_text", response_model=GenerateResultModel)
def unmask_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Заменяет `<MASK>` на наиболее подходящие слова или предложения. Возвращает целый текст с замененным `<MASK>`

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Строка, в которой есть ключевое слово `<MASK>`
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return OperationResult(code=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}")
        return OperationResult(code=3, message=f"{exc}")

    texts = data.context_data
    hint = data.hint
    logging.info(f"/unmask_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.unmask_context_path)
        api.prepare_query(texts, hint)
        logging.info(
            f"Ready to send request to ChatGPT with token={api.token}; query={api.query}")
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result)
        logging.info(f"/unmask_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResultModel(status=OperationResult(code=0, message="Text unmasked"), text_data=result, result_id=result_id)
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=2, message=f"{exc}"), text_data="", result_id=-1)
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResultModel(status=OperationResult(code=6, message=f"{exc}"), text_data="", result_id=-1)
