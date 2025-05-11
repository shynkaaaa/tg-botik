# schedule_parser.py
import requests
from bs4 import BeautifulSoup

def parse_schedule():
    url = "https://metroalmaty.kz/ru/schedule"
    response = requests.get(url)

    if response.status_code != 200:
        return "Ошибка при получения данных"

    soup = BeautifulSoup(response.text, features="html.parser")

    schedule = []

    for row in soup.select('.schedule__table-body'):
        station = row.select_one('.schedule__table-body--cell-1 a').text.strip()
        time_to = row.select('.schedule__table-body--cell-2')[0].text.strip()
        time_from = row.select('.schedule__table-body--cell-2')[1].text.strip()
        schedule.append({
            'station': station,
            'time_to': time_to,
            'time_from': time_from
        })

    return schedule