"""
Главный модуль с сервером FastAPI
"""

import logging
import time

from fastapi import BackgroundTasks, FastAPI, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

import requests

from models import (
    GenerateQueryModel,
    SendFeedbackResult,
    GenerateResultID,
    GenerateResultStatus,
    GenerateResultData,
    GenerateID,
    GenerateStatus,
    GenerateResult,
    UserResults,
    UploadFileModel,
    UploadFileResult,
)
from config import Config
from database import Database, DBException
from utils import (
    is_valid,
    parse_query_string,
    replace_stop_words,
    prepare_string,
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
* Роман Медников - Frontend React Dev, ChatGPT Enthusiast, Perplexity Enthusiast 🍓
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
        version="1.6.0 - Clean Slate",
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
        raise Exception("DB Error! Shutting down...") from exc
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        raise Exception("Unknown error! Shutting down...") from exc


@app.post(
    "/api/v1/post/{post_id}/like",
    response_model=SendFeedbackResult,
    tags=["Действия с готовым постом"],
)
def send_like(post_id: int, Authorization=Header()):
    """
    Метод для отправки лайка на пост

    post_id - айди генерации, полученный из generate

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

    result_id = int(post_id)

    logging.info(f"/like\tid={result_id}")

    try:
        if not db.user_owns_post(auth_data["vk_user_id"], result_id):
            return SendFeedbackResult(status=1, message="Post is not yours")

        db.write_feedback(result_id, 1)
        logging.info(logging.info(f"/like\tid={result_id}\tOK"))
        return SendFeedbackResult(status=0, message="Post is liked")
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return SendFeedbackResult(status=6, message="Error in database")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return SendFeedbackResult(status=4, message="Unknown error")


@app.post(
    "/api/v1/post/{post_id}/dislike",
    response_model=SendFeedbackResult,
    tags=["Действия с готовым постом"],
)
def send_dislike(post_id: int, Authorization=Header()):
    """
    Метод для отправки дизлайка на пост

    post_id - айди генерации, полученный из generate

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

    result_id = int(post_id)

    logging.info(f"/dislike\tid={result_id}")

    try:
        if not db.user_owns_post(auth_data["vk_user_id"], result_id):
            return SendFeedbackResult(status=1, message="Post is not yours")

        db.write_feedback(result_id, -1)
        logging.info(logging.info(f"/dislike\tid={result_id}\tOK"))
        return SendFeedbackResult(status=0, message="Post is disliked")
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return SendFeedbackResult(status=6, message="Error in database")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return SendFeedbackResult(status=4, message="Unknown error")


@app.delete(
    "/api/v1/post/{post_id}",
    response_model=SendFeedbackResult,
    tags=["Действия с готовым постом"],
)
def send_hidden(post_id: int, Authorization=Header()):
    """
    Метод для скрытия поста

    post_id - айди генерации, полученный из generate

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

    result_id = int(post_id)

    logging.info(f"/delete\tid={result_id}")

    try:
        if not db.user_owns_post(auth_data["vk_user_id"], result_id):
            return SendFeedbackResult(status=1, message="Post is not yours")

        db.hide_generation(result_id, 1)
        logging.info(logging.info(f"/delete\tid={result_id}\tOK"))
        return SendFeedbackResult(status=0, message="Post is hidden")
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return SendFeedbackResult(status=6, message="Error in database")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return SendFeedbackResult(status=4, message="Unknown error")


@app.post(
    "/api/v1/post/{post_id}/recover",
    response_model=SendFeedbackResult,
    tags=["Действия с готовым постом"],
)
def send_recovered(post_id: int, Authorization=Header()):
    """
    Метод для восстановления поста

    post_id - айди генерации, полученный из generate

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

    result_id = int(post_id)

    logging.info(f"/recover\tid={result_id}")

    try:
        if not db.user_owns_post(auth_data["vk_user_id"], result_id):
            return SendFeedbackResult(status=1, message="Post is not yours")

        db.hide_generation(result_id, 0)
        logging.info(logging.info(f"/recover\tid={result_id}\tOK"))
        return SendFeedbackResult(status=0, message="Post is recovered")
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return SendFeedbackResult(status=6, message="Error in database")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return SendFeedbackResult(status=4, message="Unknown error")


@app.post(
    "/api/v1/post/{post_id}/publish",
    response_model=SendFeedbackResult,
    tags=["Действия с готовым постом"],
)
def send_published(post_id: int, Authorization=Header()):
    """
    Метод для отправки а=факта о публикации на пост

    post_id - айди генерации, полученный из generate

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

    result_id = int(post_id)

    logging.info(f"/publish\tid={result_id}")

    try:
        if not db.user_owns_post(auth_data["vk_user_id"], result_id):
            return SendFeedbackResult(status=1, message="Post is not yours")

        db.write_published(result_id)
        logging.info(logging.info(f"/publish\tid={result_id}\tOK"))
        return SendFeedbackResult(
            status=0, message="Post is marked as published"
        )
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return SendFeedbackResult(status=6, message="Error in database")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return SendFeedbackResult(status=4, message="Unknown error")


@app.get(
    "/api/v1/posts",
    response_model=UserResults,
    tags=["Статистика"],
)
def get_history(
    group_id: int = None,
    offset: int = None,
    limit: int = None,
    Authorization=Header(),
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
                count=0,
            )
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
        return UserResults(
            status=3,
            message="Authorization error",
            data=[],
            count=0,
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return UserResults(
            status=1,
            message="Unknown error",
            data=[],
            count=0,
        )

    user_id = auth_data["vk_user_id"]

    logging.info(
        f"/posts\tvk_user_id={user_id}; group_id={group_id}; offset={offset}; limit={limit}"
    )

    try:
        generated_results = db.get_users_texts(group_id, user_id)
        total_len = len(generated_results)
        if offset:
            generated_results = generated_results[offset:]
        if limit:
            generated_results = generated_results[:limit]
        logging.info(
            f"/posts\tvk_user_id={user_id}; group_id={group_id}; offset={offset}; limit={limit}\tOK"
        )
        return UserResults(
            status=0,
            message="Results returned",
            data=generated_results,
            count=total_len,
        )

    except DBException as exc:
        logging.error(
            f"Error in database while fetching user results text: {exc}"
        )
        return UserResults(
            status=6,
            message="Error in database while fetching user results text",
            data=[],
            count=0,
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return UserResults(
            status=4,
            message="Unknown error",
            data=[],
            count=0,
        )


def ask_nn(
    gen_method: str,
    texts: list[str],
    hint: str,
    gen_id: int,
):
    """
    Общий метод для вызова функций работы с нейросетью
    """

    time_start = int(time.time())

    logging.info(
        f"/{gen_method}\tlen(texts)={len(texts)}; hint[:20]={hint[:20]}; gen_id={gen_id}"
    )

    token = None

    try:
        token = config.next_token()

        logging.info(f"Got token[:10]: {token[:10]}")

        api = NNApi(token=token)

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
        elif gen_method == "gen_from_scratch":
            api.load_context(config.gen_from_scratch_context_path)

        if (gen_method != "gen_from_scratch") and (hint == ""):
            raise NNException(
                "Hint cannot be empty (unless it is gen_from_scratch)"
            )

        texts = [prepare_string(replace_stop_words(text)) for text in texts]
        hint = prepare_string(replace_stop_words(hint))

        api.prepare_query(texts, hint)

        api.send_request()

        result = prepare_string(api.get_result())

        if gen_method == "append_text":
            result = result.replace(hint, "")
            result = prepare_string(f"{hint} {result}")

        time_elapsed = int(time.time() - time_start)

        db.add_record_result(gen_id, result, time_elapsed)

        logging.info(
            f"/{gen_method}\tlen(texts)={len(texts)}; hint[:20]={hint[:20]}; gen_id={gen_id}\tOK"
        )

    except NNException as exc:
        logging.error(f"Error in NN API: {exc}\n")
        db.add_record_result(gen_id, "", 0, False)
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        db.add_record_result(gen_id, "", 0, False)
    finally:
        config.free()


def process_method(
    method: str,
    data: GenerateQueryModel,
    background_tasks: BackgroundTasks,
    Authorization=Header(),
):
    """
    Общий метод для обработки запроса на генерацию
    """
    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateID(
                status=1,
                message="Authorization error",
                data=GenerateResultID(text_id=-1),
            )
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
        return GenerateID(
            status=3,
            message="Authorization error",
            data=GenerateResultID(text_id=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateID(
            status=4,
            message="Unknown error",
            data=GenerateResultID(text_id=-1),
        )

    try:
        texts = data.context_data
        hint = data.hint
        user_id = auth_data["vk_user_id"]
        platform = auth_data["vk_platform"]
        group_id = data.group_id
        time_now = int(time.time())
    except KeyError as exc:
        logging.error(f"Key error. Check the header: {exc}")
        return GenerateID(
            status=4,
            message="Key error. Check the header",
            data=GenerateResultID(text_id=-1),
        )

    try:
        gen_id = db.add_record(
            hint,
            user_id,
            method,
            group_id,
            time_now,
            platform,
        )
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return GenerateID(
            status=6,
            message="Error in database",
            data=GenerateResultID(text_id=-1),
        )

    if not config.ready():
        logging.error("Service is not ready. Not enough tokens")
        db.add_record_result(gen_id, "", 0, False)
        return GenerateID(
            status=7,
            message="Server is not ready",
            data=GenerateResultID(text_id=-1),
        )

    background_tasks.add_task(ask_nn, method, texts, hint, gen_id)

    return GenerateID(
        status=0,
        message="OK",
        data=GenerateResultID(text_id=gen_id),
    )


@app.post(
    "/api/v1/generation/generate",
    response_model=GenerateID,
    tags=["Генерация"],
)
def generate(
    data: GenerateQueryModel,
    background_tasks: BackgroundTasks,
    Authorization=Header(),
):
    """
    Метод для генерации текстового контета нейросетью выбранным способом

    method - GenerationMethod, строка с описанием метода генерации.
    Доступные значения: "generate_text", "append_text", "rephrase_text",
    "summarize_text", "extend_text", "unmask_text", gen_from_scratch

    context_data - list[str], список текстов существующих постов
    в паблике (лучше не менее 3-5 непустых текстов )

    hint - str, запрос на генерацию контента. Содержит максимально
    краткую мысль, о чем писать текст (для gen_from_scratch
    можно оставить эту строку пустой)

    group_id - int, айди группы, для которой генерируется пост. Нужно
    чтобы связать генерацию с группой и потом выдавать статистику для группы по этому айди
    """
    return process_method(
        data.method,
        data,
        background_tasks,
        Authorization,
    )


@app.get(
    "/api/v1/generation/status",
    response_model=GenerateStatus,
    tags=["Генерация"],
)
def get_status(text_id, Authorization=Header()):
    """
    Возвращает статус генерации, 0 - не готово, 1 - готово,
    2 - ошибка

    text_id - айди текста, выданный методом генерации
    """
    logging.info(f"/get_gen_status\ttext_id={text_id}")
    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateStatus(
                status=1,
                message="Authorization error",
                data=GenerateResultStatus(text_status=-1),
            )
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
        return GenerateStatus(
            status=3,
            message="Authorization error",
            data=GenerateResultStatus(text_status=-1),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateStatus(
            status=4,
            message="Unknown error",
            data=GenerateResultStatus(text_status=-1),
        )

    try:
        if not db.user_owns_post(auth_data["vk_user_id"], text_id):
            return GenerateResultStatus(
                status=1,
                message="Post is not yours",
                data=GenerateResultStatus(text_status=-1),
            )

        status = db.get_status(text_id)
        logging.info(f"/get_gen_status\ttext_id={text_id}\tOK")
        return GenerateStatus(
            status=0,
            message="OK",
            data=GenerateResultStatus(text_status=status),
        )

    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return GenerateStatus(
            status=6,
            message="Error in database",
            data=GenerateResultStatus(text_status=-1),
        )


@app.get(
    "/api/v1/generation/result",
    response_model=GenerateResult,
    tags=["Генерация"],
)
def get_result(text_id, Authorization=Header()):
    """
    Возвращает результат генерации по айди

    text_id - айди текста, выданный методом генерации
    """
    logging.info(f"/get_gen_result\ttext_id={text_id}")
    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return GenerateResult(
                status=1,
                message="Authorization error",
                data=GenerateResultStatus(text_status=-1),
            )
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
        return GenerateResult(
            status=3,
            message="Authorization error",
            data=GenerateResultData(text_data=""),
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return GenerateResult(
            status=4,
            message="Unknown error",
            data=GenerateResultData(text_data=""),
        )

    try:
        if not db.user_owns_post(auth_data["vk_user_id"], text_id):
            return GenerateResult(
                status=1,
                message="Post is not yours",
                data=GenerateResultData(text_data=""),
            )

        result = db.get_value(text_id)
        logging.info(f"/get_gen_result\ttext_id={text_id}\tOK")
        return GenerateResult(
            status=0,
            message="OK",
            data=GenerateResultData(text_data=result),
        )
    except DBException as exc:
        logging.error(f"Error in database: {exc}")
        return GenerateResult(
            status=6,
            message="Error in database",
            data=GenerateResultData(text_data=""),
        )


@app.post(
    "/api/v1/files/upload",
    response_model=UploadFileResult,
    tags=["Файлы"],
)
def upload_file(
    file: UploadFile,
    data: UploadFileModel,
    Authorization=Header(),
):
    """
    Метод для загрузки файла на сервер ВКонтакте

    token - str, токен
    group_id - int, айди группы
    """
    logging.info("/upload")
    try:
        auth_data = parse_query_string(Authorization)
        if not is_valid(query=auth_data, secret=config.client_secret):
            return UploadFileResult(
                status=1,
                message="Authorization error",
                file_url="",
            )
    except UtilsException as exc:
        logging.error(
            f"Error in utils, probably the request was not correct: {exc}"
        )
        return UploadFileResult(
            status=3,
            message="Authorization error",
            file_url="",
        )
    except Exception as exc:
        logging.error(f"Unknown error: {exc}")
        return UploadFileResult(
            status=4,
            message="Unknown error",
            file_url="",
        )

    file_data = file.file
    content_type = file.content_type
    filename = file.filename
    token = data.token
    group_id = data.group_id

    logging.info(f"{content_type}, {filename}, {token}, {group_id}")

    try:
        if content_type in ["image/png", "image/jpeg", "image/gif"]:
            response = requests.get(
                "https://api.vk.com/method/photos.getWallUploadServer",
                params={"group_id": group_id, "access_token": token},
                timeout=5,
            )
            logging.info(f"GET SERVER\n{response.json()}")
            upload_url = response.json()["upload_url"]
            response = requests.post(
                upload_url, files={"photo": file_data}, timeout=5
            )
            logging.info(f"UPLOAD\n{response.json()}")
            server = response.json()["server"]
            photo = response.json()["photo"]
            hash_ = response.json()["hash"]
            response = requests.post(
                "https://api.vk.com/method/photos.saveWallPhoto",
                params={"access_token": token, "server": server, "hash": hash_},
                files={"photo": photo},
                timeout=5,
            )
            logging.info(f"SAVE\n{response.json()}")
            sizes = response.json()["response"][0]["sizes"]
            needed_size_ind = 0
            for i, _ in enumerate(sizes):
                if sizes[i]["height"] > sizes[needed_size_ind]["height"]:
                    needed_size_ind = i
            url = sizes[needed_size_ind]["url"]
            return UploadFileResult(
                status=0,
                message="Photo is uploaded",
                file_url=url,
            )

        response = requests.get(
            "https://api.vk.com/method/docs.getWallUploadServer",
            params={"group_id": group_id, "access_token": token},
            timeout=5,
        )
        logging.info(f"GET SERVER\n{response.json()}")
        upload_url = response.json()["upload_url"]
        response = requests.post(
            upload_url, files={"file": file_data}, timeout=5
        )
        logging.info(f"UPLOAD\n{response.json()}")
        file_response = response.json()["file"]
        response = requests.post(
            "https://api.vk.com/method/docs.save",
            params={"access_token": token},
            files={"file": file_response},
            timeout=5,
        )
        logging.info(f"SAVE\n{response.json()}")
        url = response.json()["response"]["doc"]["url"]
        return UploadFileResult(
            status=0,
            message="File is uploaded",
            file_url=url,
        )

    except Exception as exc:
        logging.info(f"Error in /upload: {exc}")
        return UploadFileResult(
            status=4,
            message="Unknown error",
            file_url="",
        )
