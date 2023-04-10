"""
Главный модуль с сервером FastAPI
"""

import logging
import time

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from models import (
    FeedbackModel,
    GenerateQueryModel,
    SendFeedbackResult,
    GenerateResultData,
    GenerateResult,
    UserResults,
)
from config import Config
from database import Database, DBException
from utils import is_valid, parse_query_string, UtilsException
from nn_api import NNException, NNApi

logging.basicConfig(
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(
            f"/home/logs/log_{time.ctime().replace(' ', '_')}.txt",
            mode="w",
            encoding="UTF-8",
        )
    ],
    datefmt="%H:%M:%S UTC",
    level=logging.INFO,
)

app = FastAPI()
config = Config("config.json")
db = Database(
    config.db_user, config.db_password, config.db_name, config.db_port, config.db_host
)

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
Выпускной проект ОЦ VK в МГТУ команды Team Rattlesnake. Сервис, генерирующий контент для социальной сети ВКонтакте. Посты генерируются сами с помощью нейросетей, также можно сократить, удлинить, продолжить, перефразировать текст и заменить часть текста. Станьте популярным в сети с помощью Strawberry!

* Коленков Андрей - Team Lead, Backend Python Dev 🍓
* Роман Медников - Frontend React Dev, ChatGPT Enthusiast 🍓
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
        version="0.8.0 Хакатон - Clean Slate",
        description=DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
def startup():
    """
    При старте сервера проверить, нужна ли миграция и сделать ее, если нужна
    """
    logging.info("Server started")
    try:
        if db.need_migration():
            logging.info("Creating tables...")
            db.migrate()
            logging.info("Creating tables...\tOK")
    except DBException as exc:
        logging.error(f"Error while checking tables: {exc}")
        raise Exception(f"Error! {exc} Shutting down...") from exc


@app.post("/send_feedback", response_model=SendFeedbackResult)
def send_feedback(data: FeedbackModel, Authorization=Header()):
    """
    Метод для отправки фидбека по результату работы сервиса.

    result_id - int, номер результата работы сервиса.

    score - int, оценка, теперь это не изменение, а само значение
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return SendFeedbackResult(status=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return SendFeedbackResult(status=3, message=f"{exc}")

    result_id = data.result_id
    score = data.score
    logging.info(f"/send_feedback\tresult_id={result_id}; score={score}")

    try:
        db.change_rating(result_id, score)
        logging.info(f"/send_feedback\tresult_id={result_id}; score={score}\tOK")
        return SendFeedbackResult(status=0, message="Score updated")
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return SendFeedbackResult(status=6, message=f"{exc}")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return SendFeedbackResult(status=4, message=f"{exc}")


@app.get("/get_user_results", response_model=UserResults)
def get_user_results(offset=None, limit=None, Authorization=Header()):
    """
    Метод для получения списка всех сгенерированных юзером текстов

    limit - int, необязательное, максимальное количество результатов

    offest - int, необязательное, смещение
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return UserResults(
                status=1,
                message="Authorization error",
                data=[],
            )
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return UserResults(
            status=3,
            message="Authorization error",
            data=[],
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return UserResults(
            status=1,
            message="Authorization error",
            data=[],
        )

    user_id = auth_data["vk_user_id"]

    logging.info(f"/generate_text\tvk_user_id={user_id}")

    try:
        generated_results = db.get_users_texts(user_id, offest, limit)
        return UserResults(
            status=0,
            message="Results returned",
            data=generated_results,
        )

    except DBException as exc:
        logging.error(f"Error in database while fetching user results text: {exc}")
        return UserResults(
            status=6,
            message=f"{exc}",
            data=[],
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return UserResults(
            status=4,
            message=f"{exc}",
            data=[],
        )


@app.post("/generate_text", response_model=GenerateResult)
def generate_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Метод для получения текста на тему, заданную в запросе. Текст генерируется с нуля

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит максимально краткую мысль, о чем писать текст
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateResult(
                status=1,
                message="Authorization error",
                data=GenerateResultData(text_data="", result_id=-1),
            )
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )

    texts = data.context_data
    hint = data.hint
    user_id = auth_data["vk_user_id"]
    gen_method = "generate_text"
    logging.info(f"/generate_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.gen_context_path)
        api.prepare_query(texts, hint)
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result, user_id, gen_method)
        logging.info(f"/generate_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResult(
            status=0,
            message="Text generated",
            data=GenerateResultData(text_data=result, result_id=result_id),
        )
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResult(
            status=2,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResult(
            status=6,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )


@app.post("/append_text", response_model=GenerateResult)
def append_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Добавляет несколько слов или предложений к тексту запроса и возвращает только эти добавленные слова

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст, к концу которого нужно добавить еще текст
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateResult(
                status=1,
                message="Authorization error",
                data=GenerateResultData(text_data="", result_id=-1),
            )
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )

    texts = data.context_data
    hint = data.hint
    user_id = auth_data["vk_user_id"]
    gen_method = "append_text"
    logging.info(f"/append_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.append_context_path)
        api.prepare_query(texts, hint)
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result, user_id, gen_method)
        logging.info(f"/append_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResult(
            status=0,
            message="Text generated",
            data=GenerateResultData(
                text_data=f"{hint.strip()} {result.strip()}", result_id=result_id
            ),
        )
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResult(
            status=2,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResult(
            status=6,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )


@app.post("/rephrase_text", response_model=GenerateResult)
def rephrase_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Перефразирует поданный текст, возвращает текст примерно той же длины, но более складный по содержанию

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст, который надо перефразировать
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateResult(
                status=1,
                message="Authorization error",
                data=GenerateResultData(text_data="", result_id=-1),
            )
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )

    texts = data.context_data
    hint = data.hint
    user_id = auth_data["vk_user_id"]
    gen_method = "rephrase_text"
    logging.info(f"/rephrase_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.rephrase_context_path)
        api.prepare_query(texts, hint)
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result, user_id, gen_method)
        logging.info(f"/rephrase_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResult(
            status=0,
            message="Text generated",
            data=GenerateResultData(text_data=result, result_id=result_id),
        )
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResult(
            status=2,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResult(
            status=6,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )


@app.post("/summarize_text", response_model=GenerateResult)
def summarize_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Резюмирует поданный текст. Возвращает главную мысль текста в запросе в одно предложение

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст (лучше длинный), который надо сжать
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateResult(
                status=1,
                message="Authorization error",
                data=GenerateResultData(text_data="", result_id=-1),
            )
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )

    texts = data.context_data
    hint = data.hint
    user_id = auth_data["vk_user_id"]
    gen_method = "summarize_text"
    logging.info(f"/summarize_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.summarize_context_path)
        api.prepare_query(texts, hint)
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result, user_id, gen_method)
        logging.info(f"/summarize_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResult(
            status=0,
            message="Text generated",
            data=GenerateResultData(text_data=result, result_id=result_id),
        )
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResult(
            status=2,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResult(
            status=6,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )


@app.post("/extend_text", response_model=GenerateResult)
def extend_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Расширяет поданный текст. Предполагается, что на вход идет уже большой осмысленный текст
    и он становится еще более красочным и большим

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст (лучше длинный), который надо сжать
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateResult(
                status=1,
                message="Authorization error",
                data=GenerateResultData(text_data="", result_id=-1),
            )
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )

    texts = data.context_data
    hint = data.hint
    user_id = auth_data["vk_user_id"]
    gen_method = "extend_text"
    logging.info(f"/extend_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.extend_context_path)
        api.prepare_query(texts, hint)
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result, user_id, gen_method)
        logging.info(f"/extend_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResult(
            status=0,
            message="Text generated",
            data=GenerateResultData(text_data=result, result_id=result_id),
        )
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResult(
            status=2,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResult(
            status=6,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )


@app.post("/unmask_text", response_model=GenerateResult)
def unmask_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Заменяет '<MASK>' на наиболее подходящие слова или предложения. Возвращает текст, в котором все маски заменены на слова

    context_data - list[str], список текстов существующих постов в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Строка, в которой есть хотя бы одно ключевое слово '<MASK>'
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateResult(
                status=1,
                message="Authorization error",
                data=GenerateResultData(text_data="", result_id=-1),
            )
    except UtilsException as exc:
        logging.error(f"Error in utils, probably the request was not correct: {exc}")
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )

    texts = data.context_data
    hint = data.hint
    user_id = auth_data["vk_user_id"]
    gen_method = "unmask_text"
    logging.info(f"/unmask_text\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())
        api.load_context(config.unmask_context_path)
        api.prepare_query(texts, hint)
        api.send_request()
        result = api.get_result()
        result_id = db.add_generated_data(hint, result, user_id, gen_method)
        logging.info(f"/unmask_text\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResult(
            status=0,
            message="Text generated",
            data=GenerateResultData(text_data=result, result_id=result_id),
        )
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResult(
            status=2,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResult(
            status=6,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message=f"{exc}",
            data=GenerateResultData(text_data="", result_id=-1),
        )
