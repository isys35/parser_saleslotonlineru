import requests
import csv
from requests import Session
import time
from bs4 import BeautifulSoup
from urllib.parse import quote

HOST = 'https://sales.lot-online.ru/'
URL = 'https://sales.lot-online.ru/e-auction/lots.xhtml'
POST_URL = 'https://sales.lot-online.ru/e-auction/lots.xhtml'
HEADERS = {
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
    "Content-Length": "828",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Faces-Request": "partial/ajax",
    "Host": "sales.lot-online.ru",
    "Origin": "https://sales.lot-online.ru",
    "Referer": "https://sales.lot-online.ru/e-auction/lots.xhtml",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
    "X-Requested-With": "XMLHttpRequest"
}

DATA_FILE = 'data.csv'


def save_page(response_str, file_name='page.html'):
    with open(file_name, 'w', encoding='utf8') as html_file:
        html_file.write(response_str)


def parse_javax_faces_viewstate(soup):
    input = soup.find("input", id="j_id1:javax.faces.ViewState:0")
    return input['value']


def save_data(data):
    try:
        with open(DATA_FILE, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=';')
            saved_urls = [el[0] for el in reader]
        data_for_write = [el for el in data if el[0] not in saved_urls]
    except FileNotFoundError:
        data_for_write = data
    with open(DATA_FILE, "a", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerows(data_for_write)


def parse_data(soup):
    data = []
    for el in soup.select('a.filed.filed-title'):
        url = 'https://sales.lot-online.ru/e-auction/' + el['href']
        unit_time = int(time.time())
        data.append([url, unit_time])
    return data


def parse_key(soup, page):
    items = soup.select('.item')
    pages = []
    for item in items:
        url_page = item.select_one('a')
        if url_page:
            try:
                p = int(url_page.text)
            except ValueError:
                p = None
        else:
            p = None
        pages.append(p)
    if page in pages:
        return items[pages.index(page)].select_one('a')['id']
    else:
        return False


if __name__ == '__main__':
    session = Session()
    response = session.get('https://sales.lot-online.ru/e-auction/lots.xhtml')
    soup = BeautifulSoup(response.text, 'lxml')
    javax_faces_viewstate = parse_javax_faces_viewstate(soup)
    data = parse_data(soup)
    save_data(data)
    page = 2
    while True:
        print('Страница {}'.format(page))
        key = parse_key(soup, page)
        if not key:
            break
        pre_json_data = "javax.faces.partial.ajax=true&javax.faces.source={}&javax.faces.partial.execute={" \
                        "}&javax.faces.partial.render=formMain%3ApanelList+formMain%3ALotListPaginatorID&{}={" \
                        "}&formMain=formMain&formMain%3AinputServerTime=00%3A09%3A42&formMain%3AcommonSearchCriteriaStr" \
                        "=&formMain%3Aj_idt82=&formMain%3AscmTypeAuctionId_focus=&formMain%3AscmSubjectRFId_focus" \
                        "=&formMain%3AitKeyWords=&formMain%3AitTradeOrganizer=&formMain%3AauctionDatePlanBID_input" \
                        "=&formMain%3AauctionDatePlanEID_input=&formMain%3AcostBValueB=0&formMain%3AcostBValueE=0" \
                        "&formMain%3AitLotNoticeNum=&formMain%3AitAuctionRegNum=&formMain%3AselectIndRightEnsure=2" \
                        "&formMain%3AselectIndPublish=1&javax.faces.ViewState={}"
        json_data = pre_json_data.format(quote(key), quote(key), quote(key), quote(key), javax_faces_viewstate)
        response = session.post(POST_URL, data=json_data, headers=HEADERS)
        save_page(response.text)
        soup = BeautifulSoup(response.text, 'lxml')
        data = parse_data(soup)
        save_data(data)
        page += 1
