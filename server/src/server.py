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
from utils import (
    is_valid,
    parse_query_string,
    filter_stop_words,
    UtilsException,
)
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
    config.db_user,
    config.db_password,
    config.db_name,
    config.db_port,
    config.db_host,
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
Выпускной проект ОЦ VK в МГТУ команды Team Rattlesnake. Сервис, генерирующий
контент для социальной сети ВКонтакте. Посты генерируются сами с помощью
нейросетей, также можно сократить, удлинить, продолжить, перефразировать
текст и заменить часть текста. Представляет собой VK MiniAPP, который удобно
использовать и с компьютера, и со смартфона. Станьте популярным в сети с помощью
Strawberry!

* Коленков Андрей - Team Lead, Backend Python Dev 🍓
* Роман Медников - Frontend React Dev, ChatGPT Enthusiast 🍓
* Василий Ермаков - Data Scientist 🍓

Наш паблик: [Strawberry - Помощник в ведении сообщества](https://vk.com/strawberry_ai)

Приложение работает: [Strawberry](https://vk.com/app51575840_226476923)
"""


def custom_openapi():
    """
    Это нужно для кастомной страницы с документацией
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry🍓",
        version="1.0.0 - Clean Slate",
        description=DESCRIPTION,
        routes=app.routes,
        contact={
            "name": "Team Rattlesnake GitHub",
            "url": "https://github.com/TeamRattlesnake",
        },
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
def startup():
    """
    При старте сервера проверить, нужна ли миграция
    и сделать ее, если нужна
    """
    logging.info("Server started")
    try:
        if db.need_migration():
            logging.info("Creating tables...")
            db.migrate()
            logging.info("Creating tables...\tOK")
    except DBException as exc:
        logging.error(f"Error while checking tables: {exc}")
        raise Exception("Error! Shutting down...") from exc


@app.post("/send_feedback", response_model=SendFeedbackResult)
def send_feedback(data: FeedbackModel, Authorization=Header()):
    """
    Метод для отправки фидбека по результату работы сервиса.

    result_id - int, номер результата работы сервиса.

    score - int, оценка, -1 или 1.
    """

    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return SendFeedbackResult(status=1, message="Authorization error")
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
        return SendFeedbackResult(
            status=3,
            message="Error in utils, probably the request was not correct",
        )

    result_id = data.result_id
    score = int(data.score)
    logging.info(f"/send_feedback\tresult_id={result_id}; score={score}")

    try:
        db.change_rating(result_id, score)
        logging.info(
            f"/send_feedback\tresult_id={result_id}; score={score}\tOK"
        )
        return SendFeedbackResult(status=0, message="Score updated")
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return SendFeedbackResult(status=6, message="Error in database")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return SendFeedbackResult(status=4, message="Unknown error")


@app.get("/get_user_results", response_model=UserResults)
def get_user_results(
    group_id=None, offset=None, limit=None, Authorization=Header()
):
    """
    Метод для получения списка всех сгенерированных юзером текстов

    group_id - int, необязательное, если указать его, то вернет все
    записи для данного сообщества от данного юзера. Если не указать,
    то все записи от данного юзера

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
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
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

    logging.info(
        f"/get_user_results\tvk_user_id={user_id}; group_id={group_id}; offset={offset}; limit={limit}"
    )

    try:
        generated_results = db.get_users_texts(group_id, user_id, offset, limit)
        logging.info(
            f"/get_user_results\tvk_user_id={user_id}; group_id={group_id}; offset={offset}; limit={limit}\tOK"
        )
        return UserResults(
            status=0,
            message="Results returned",
            data=generated_results,
        )

    except DBException as exc:
        logging.error(
            f"Error in database while fetching user results text: {exc}"
        )
        return UserResults(
            status=6,
            message="Error in database while fetching user results text",
            data=[],
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return UserResults(
            status=4,
            message="Unknown error",
            data=[],
        )


def process_query(
    method: str, data: GenerateQueryModel, Authorization=Header()
) -> GenerateResultData:
    """
    Общий метод для вызова функций работы с ChatGPT
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
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message="Unknown error",
            data=GenerateResultData(text_data="", result_id=-1),
        )

    texts = data.context_data
    hint = data.hint
    user_id = auth_data["vk_user_id"]
    group_id = data.group_id
    gen_method = method

    logging.info(f"/{gen_method}\tlen(texts)={len(texts)}; hint={hint}")

    try:
        api = NNApi(config.next_token())

        if gen_method == "generate_text":
            api.load_context(config.gen_context_path)
        elif gen_method == "append_text":
            api.load_context(config.append_context_path)
        elif gen_method == "rephrase_text":
            api.load_context(config.rephrase_context_path)
        elif gen_method == "summarize_text":
            api.load_context(config.summarize_context_path)
        elif gen_method == "extend_text":
            api.load_context(config.extend_context_path)
        elif gen_method == "unmask_text":
            api.load_context(config.unmask_context_path)

        texts = [filter_stop_words(text) for text in texts]
        hint = filter_stop_words(hint)

        api.prepare_query(texts, hint)

        api.send_request()

        result = api.get_result()
        if gen_method == "append_text":
            result = result.replace(hint, "")
            result = f"{hint} {result}"

        result_id = db.add_generated_data(
            hint, result, user_id, gen_method, group_id
        )

        logging.info(f"/{gen_method}\tlen(texts)={len(texts)}; hint={hint}\tOK")
        return GenerateResult(
            status=0,
            message="OK",
            data=GenerateResultData(text_data=result, result_id=result_id),
        )
    except NNException as exc:
        logging.error(f"Error in NN API while generating text: {exc}")
        return GenerateResult(
            status=2,
            message="Error in NN API while generating text",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except DBException as exc:
        logging.error(f"Error in database while generating text: {exc}")
        return GenerateResult(
            status=6,
            message="Error in database while generating text",
            data=GenerateResultData(text_data="", result_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message="Unknown error",
            data=GenerateResultData(text_data="", result_id=-1),
        )


@app.post("/generate_text", response_model=GenerateResult)
def generate_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Метод для получения текста на тему, заданную в запросе.
    Текст генерируется с нуля

    context_data - list[str], список текстов существующих постов
    в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит максимально
    краткую мысль, о чем писать текст

    group_id - int, айди группы, для которой генерируется пост. Нужно
    чтобы связать генерацию с группой и потом выдавать статистику для группы по этому айди
    """
    return process_query("generate_text", data, Authorization)


@app.post("/append_text", response_model=GenerateResult)
def append_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Добавляет несколько слов или предложений к тексту запроса и
    возвращает только эти добавленные слова

    context_data - list[str], список текстов существующих постов
    в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст, к
    концу которого нужно добавить еще текст

    group_id - int, айди группы, для которой генерируется пост.
    Нужно чтобы связать генерацию с группой и потом выдавать статистику
    для группы по этому айди
    """
    return process_query("append_text", data, Authorization)


@app.post("/rephrase_text", response_model=GenerateResult)
def rephrase_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Перефразирует поданный текст, возвращает текст примерно той же
    длины, но более складный по содержанию

    context_data - list[str], список текстов существующих постов в
    паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст, который
    надо перефразировать

    group_id - int, айди группы, для которой генерируется пост. Нужно
    чтобы связать генерацию с группой и потом выдавать статистику для
    группы по этому айди
    """
    return process_query("rephrase_text", data, Authorization)


@app.post("/summarize_text", response_model=GenerateResult)
def summarize_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Резюмирует поданный текст. Возвращает главную мысль текста в
    запросе в одно предложение

    context_data - list[str], список текстов существующих постов в
    паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст (лучше
    длинный), который надо сжать

    group_id - int, айди группы, для которой генерируется пост. Нужно
    чтобы связать генерацию с группой и потом выдавать статистику для
    группы по этому айди
    """
    return process_query("summarize_text", data, Authorization)


@app.post("/extend_text", response_model=GenerateResult)
def extend_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Расширяет поданный текст. Предполагается, что на вход идет уже
    большой осмысленный текст и он становится еще более красочным и большим

    context_data - list[str], список текстов существующих постов
    в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит текст (лучше короткий),
    который надо удлинить

    group_id - int, айди группы, для которой генерируется пост. Нужно чтобы
    связать генерацию с группой и потом выдавать статистику для группы по
    этому айди
    """
    return process_query("extend_text", data, Authorization)


@app.post("/unmask_text", response_model=GenerateResult)
def unmask_text(data: GenerateQueryModel, Authorization=Header()):
    """
    Заменяет '<MASK>' на наиболее подходящие слова или предложения.
    Возвращает текст, в котором все маски заменены на слова

    context_data - list[str], список текстов существующих постов в
    паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Строка, в которой есть
    хотя бы одно ключевое слово '<MASK>'

    group_id - int, айди группы, для которой генерируется пост. Нужно
    чтобы связать генерацию с группой и потом выдавать статистику для
    группы по этому айди
    """
    return process_query("unmask_text", data, Authorization)
