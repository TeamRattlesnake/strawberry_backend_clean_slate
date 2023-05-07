"""
Модуль с реализацией общения с апи нейросетей, работа с API: @Jellybe
"""

import json
import requests
import socketio

NN_URL = "https://www.perplexity.ai/socket.io/"
MAX_WORDS_LEN = 2800
NO_SOURCE_TEXTS_REPLACEMENT = (
    "Старых постов в сообществе нет, так что придумай что-то креативное"
)
OLD_TEXTS_PLACEHOLDER = "[OLD_TEXTS]"
HINT_PLACEHOLDER = "[HINT]"


class NNException(Exception):
    """
    Класс исключения, связанного с подготовкой данных и
    отправкой запроса на апи нейросетей
    """

    pass


class NNApi:
    """
    Класс для подготовки запросов и общения с API нейросети
    """

    def __init__(self, proxies):
        self.headers = {
            "authority": "www.perplexity.ai",
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        }
        if proxies:
            session = requests.Session()
            session.proxies.update(proxies)
        else:
            session = None
        self.sio = socketio.Client(http_session=session)
        self.sio.connect(NN_URL, self.headers, wait_timeout=10)
        self.context = ""
        self.query = ""
        self.result = ""

    def load_context(self, path: str):
        """
        Загружает шаблон контекста из файлика
        """
        try:
            with open(path, "r", encoding="UTF-8") as ctx_file:
                self.context = ctx_file.read()
        except Exception as exc:
            raise NNException(f"Error in load_context: {exc}") from exc

    def prepare_query(self, context_data: list[str], hint: str):
        """
        Расставляет данные по шаблону контекста
        """
        try:

            if len(hint) == 0:
                raise NNException(
                    "Error in prepare_query: the hint is empty, cannot generate without hint (or can I?)"
                )

            if len(hint) >= MAX_WORDS_LEN:
                raise NNException(
                    "Error in prepare_query: the request is too long (hint alone is larger than allowed input in model)"
                )

            source_texts_string = ""

            i = 1
            for text in context_data:
                # Собираем строку с постами чтобы она была не длиннее, чем нужно.
                # Считаю не количество слов, а количество букв потому что
                # токенизатор не любит русский
                if (
                    len(source_texts_string)
                    + len(text)
                    + len(hint)
                    + len(self.context)
                ) >= MAX_WORDS_LEN:
                    continue
                source_texts_string += f"{i}. {text}\n\n"
                i += 1

            if (
                len(source_texts_string) > 3
            ):  # Минимальная проверка на валидность контекста
                self.query = self.context.replace(
                    OLD_TEXTS_PLACEHOLDER,
                    source_texts_string,
                )
            else:
                # Если контекст слишком маленький,
                # то надо просто сказать нейросети быть креативной
                self.query = self.context.replace(
                    OLD_TEXTS_PLACEHOLDER,
                    NO_SOURCE_TEXTS_REPLACEMENT,
                )

            self.query = self.query.replace(HINT_PLACEHOLDER, hint)
            self.query = self.query.strip()
        except Exception as exc:
            raise NNException(f"Error in prepare_query: {exc}") from exc

    def send_request(self):
        """
        Отправляет запрос к API нейросети
        """
        try:
            res = self.sio.call(
                "perplexity_ask",
                (
                    self.query,
                    {
                        "source": "default",
                        "token": "f864657",
                        "last_backend_uuid": None,
                        "read_write_token": None,
                        "conversational_enabled": True,
                        "frontend_session_id": "7a3cf0f5-45eb-47a9-b87a-a666c5c3e826",
                        "language": "ru-RU",
                        "timezone": "Europe/Moscow",
                        "search_focus": "internet",
                        "frontend_uuid": "2615be01-fd68-4238-b1cc-02ad601f55ee",
                        "web_search_images": False,
                        "gpt4": False,
                    },
                ),
            )
            if not res:
                res = {}
            text_str = res.get("text", "")
            if text_str == "Query rate limit exceeded. Please try again later.":
                raise NNException("Rate limit exceeded")
            self.result = json.loads(text_str).get("answer", None)
        except Exception as exc:
            raise NNException(f"Error in send_request: {exc}") from exc

    def get_result(self) -> str:
        """
        Возвращает ответ нейросети
        """
        self.sio.disconnect()
        return self.result
