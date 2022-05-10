import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

import exceptions
from settings import ENDPOINT, HEADERS, HOMEWORK_VERDICTS, RETRY_TIME

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение в Telegram-бот."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение в чат отправлено')
    except exceptions.SendMessageFailure:
        logger.error('Сбой при отправке сообщения в чат, иди чини))')


def get_api_answer(current_timestamp):
    """Делает запрос к API."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except exceptions.APIResponseStatusCodeException:
        logger.error('Сбой при запросе к API, иди чини))')
    if response.status_code != HTTPStatus.OK:
        msg = 'Сбой при запросе к API, иди чини))'
        logger.error(msg)
        raise exceptions.APIResponseStatusCodeException(msg)
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    assert len(response) != 0, False
    if not isinstance(response, dict):
        message = 'Ответ API не является словарем'
        raise TypeError(message)
    if response.__contains__('homework_name'):
        message = 'Ключ homework_name отсутсвует в словаре'
        raise KeyError(message)
    if not isinstance(response['homeworks'], list):
        message = 'Ответ API не является списком'
        raise TypeError(message)
    return response['homeworks']


def parse_status(homework):
    """Извлекает из информации о домашней работе ее статус."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if (homework_status or homework_name) is None:
        message = ('''Ошибочка с ключем (не получилось достать'''
                   '''имя или статус работы)''')
        logging.error(message)
        raise KeyError(message)
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
    else:
        message = 'Неожиданный статус'
        logging.error(message)
        raise KeyError(message)
    return (f'Изменился статус проверки работы "'
            f'{homework_name}". {verdict}')


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        msg = 'Отсутствует необходимая переменная в Telegram-боте, иди чини))'
        logger.critical(msg)
        raise exceptions.MissingRequiredTokenException(msg)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_status = None
    previous_error = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
        except exceptions.IncorrectAPIResponseException as e:
            if str(e) != previous_error:
                previous_error = str(e)
                send_message(bot, e)
            logger.error(e)
            time.sleep(RETRY_TIME)
            continue
        try:
            homeworks = check_response(response)
            hw_status = homeworks[0].get('status')
            if hw_status != previous_status:
                previous_status = hw_status
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.debug('Статус не обновлен')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if previous_error != str(error):
                previous_error = str(error)
                send_message(bot, message)
            logger.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
