from dotenv import load_dotenv
import http
import logging
import os
import requests
import sys
import telegram
import time

from exceptions import MyException, MyTypeError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('YP_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

NUM_OF_HW_IN_LIST = 1
LIST_OF_HW = []
EMPTY = 0

# сообщения о сложности жизни :(
TOKEN_TROUBLES = 'нет токена: {token}'
DEBUG_TEXT = 'сообщение об изменении статуса отправлено успешно'
FUCK_UP_SEND_MESSAGE = 'проблема с отправкой сообщения: {error}'
TROUBLES_API = 'Ошибка при запросе к основному API {error}'
CODE_STATUS_TRUOBLE = 'проблемы с сайтом'
NOT_DICT = 'вернул не словарь!'
NOT_DICT_LIST = 'а в словаре не список'
NOT_DICT_LIST_DICT = 'а в списке не словари'
UNKNOWN_NAME = 'Такоко дз я не припомню, отстань!'
UNKNOWN_STATUS = 'такого статуса еще не было, пипяо!'
JSON_TROUBLES = 'проблемы с форматом json {error}'
INFO_TEXT = 'Погнали!'

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)


def check_tokens():
    """проверка доступности токенов."""
    for key in ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']:
        if globals().get(key) is None:
            logging.critical(TOKEN_TROUBLES.format(token=key))
            raise (MyException(TOKEN_TROUBLES.format(token=key)) and sys.exit(
            ))


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(DEBUG_TEXT)
    except telegram.error.TelegramError as error:
        logging.error(FUCK_UP_SEND_MESSAGE.format(error=error))
        raise MyException(FUCK_UP_SEND_MESSAGE.format(error=error))


def get_api_answer(timestamp):
    """делает запрос к единственному эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
    except requests.exceptions.RequestException as error:
        raise MyException(TROUBLES_API.format(error=error))
    if response.status_code != http.HTTPStatus.OK:
        raise MyException(CODE_STATUS_TRUOBLE)
    response_json = response.json()
    for key in ('error', 'code'):
        if key in response_json:
            raise MyException(
                JSON_TROUBLES.format(
                    error=response_json[key])
            )
    return response_json


def check_response(response):
    """проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise MyTypeError(NOT_DICT)
    if not isinstance(response.get('homeworks'), list):
        raise MyTypeError(NOT_DICT_LIST)
    if len(response.get('homeworks')) != EMPTY:
        for element in response.get('homeworks'):
            if not isinstance(element, dict):
                raise MyTypeError(NOT_DICT_LIST_DICT)


def parse_status(homework):
    """извлекает из информации о конкретной домашней работе статус."""
    parse_name = homework.get("homework_name")
    if parse_name is not None:
        homework_name = parse_name
    else:
        raise MyException(UNKNOWN_NAME)
    hw_status = homework.get("status")
    if HOMEWORK_VERDICTS.get(hw_status) is not None:
        verdict = HOMEWORK_VERDICTS.get(hw_status)
    else:
        raise MyException(UNKNOWN_STATUS)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.info(INFO_TEXT)
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if len(response.get('homeworks')) != EMPTY:
                text = parse_status(response.get('homeworks')[0])
                if ((len(LIST_OF_HW) != EMPTY) and (
                        text.split(' ')[-1] != LIST_OF_HW[-1])):
                    send_message(bot, text)
                    timestamp = int(time.time())
                    logging.debug(DEBUG_TEXT)
                    time.sleep(RETRY_PERIOD)
                    LIST_OF_HW.append(text.split(' ')[-1])
                    if len(LIST_OF_HW) > NUM_OF_HW_IN_LIST:
                        del LIST_OF_HW[:-1]
                else:
                    send_message(bot, text)
                    time.sleep(RETRY_PERIOD)
                    timestamp = int(time.time())
            else:
                time.sleep(RETRY_PERIOD)
                timestamp = int(time.time())
        except (MyException, MyTypeError) as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = int(time.time())


if __name__ == '__main__':
    main()
