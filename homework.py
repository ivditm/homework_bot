import logging
import os
import requests
import sys
import telegram
import time
import http


from dotenv import load_dotenv


from exceptions import my_exception

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

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)


def check_tokens():
    """проверка доступности токенов."""
    for key in [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]:
        if key is None:
            logging.critical('бедааа с токенами')
            sys.exit('Все полетело, ошибка токенов')


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('сообщение отправлено')
    except telegram.error.TelegramError as error:
        logging.error(f'проблема с отправкой сообщения: {error}')


def get_api_answer(timestamp):
    """делает запрос к единственному эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != http.HTTPStatus.OK:
            logging.error('проблемы с сайтом')
            raise my_exception('проблемы с сайтом')
    except requests.exceptions.RequestException as error:
        logging.error(f'Ошибка при запросе к основному API {error}')
    return response.json()


def check_response(response):
    """проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error('вернул не словарь!')
        raise TypeError
    if not isinstance(response.get('homeworks'), list):
        logging.error('а в словаре не список')
        raise TypeError
    if len(response.get('homeworks')) != EMPTY:
        for element in response.get('homeworks'):
            if not isinstance(element, dict):
                logging.error('а в списке не словари')
                raise TypeError


def parse_status(homework):
    """извлекает из информации о конкретной домашней работе статус."""
    if homework.get("homework_name") is not None:
        homework_name = homework.get("homework_name")
    else:
        raise my_exception('Такоко дз я не припомню, отстань!')
    hw_status = homework.get("status")
    if HOMEWORK_VERDICTS.get(hw_status) is not None:
        verdict = HOMEWORK_VERDICTS.get(hw_status)
    else:
        raise my_exception('такого статуса еще не было, пипяо!')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.info('Погнали!')
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
                    logging.debug('сообщение улетело и я с ним')
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
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = int(time.time())


if __name__ == '__main__':
    main()
