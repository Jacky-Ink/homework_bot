class SendMessageFailure(Exception):
    """Исключение отправки сообщения."""

    pass


class APIResponseStatusCodeException(Exception):
    """Исключение сбоя запроса к API."""

    pass


class MissingRequiredTokenException(Exception):
    """Исключение отсутствия необходимых переменных среды."""

    pass


class IncorrectAPIResponseException(Exception):
    """Исключение некорректного ответа API."""

    pass
