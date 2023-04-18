"""
Модуль с утилитами
"""

from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from urllib.parse import urlencode
from hmac import HMAC


class UtilsException(Exception):
    """
    Класс исключения, связанного с работой утилит
    """

    pass


def is_valid(*, query: dict, secret: str) -> bool:
    """Проверяет подпись у запроса из Миниаппа"""
    try:
        vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
        hash_code = b64encode(
            HMAC(
                secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256
            ).digest()
        )
        decoded_hash_code = (
            hash_code.decode("utf-8")[:-1].replace("+", "-").replace("/", "_")
        )
        return query["sign"] == decoded_hash_code
    except Exception as exc:
        raise UtilsException(f"Error in is_valid: {exc}") from exc


def parse_query_string(query_string: str) -> dict:
    """Парсит query строку"""
    try:
        res = dict([pair.split("=") for pair in query_string.split("&")])
        res["vk_user_id"] = int(res["vk_user_id"])
        return res
    except Exception as exc:
        raise UtilsException(f"Error in parse_query_string: {exc}") from exc


def filter_stop_words(string: str = None, strings: list[str] = None) -> str:
    """Убирает стоп-слова из поданной строки или списка строк"""
    replacements = {
        "забудь все": "",
    }

    if bool(strings is not None) != bool(string is not None):
        raise UtilsException(
            "Error in filter_stop_words: use either on string, or on list of strings, not both, not none"
        )

    if string is not None:
        for phrase, replacement in replacements.items():
            string = string.replace(phrase, replacement)
        return string

    if strings is not None:
        for i, _ in enumerate(strings):
            for phrase, replacement in replacements.items():
                strings[i] = strings[i].replace(phrase, replacement)
        return strings

    raise UtilsException("Error in filter_stop_words: unknown error")
