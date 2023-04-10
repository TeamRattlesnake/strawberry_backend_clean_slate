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


def parse_query_string(query_string):
    """Парсит query строку"""
    try:
        res = dict([pair.split("=") for pair in query_string.split("&")])
        res["vk_user_id"] = int(res["vk_user_id"])
        return res
    except Exception as exc:
        raise UtilsException(f"Error in parse_query_string: {exc}") from exc
