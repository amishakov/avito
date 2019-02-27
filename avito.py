import csv
import random
import re
from time import sleep

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import KEYWORDS


def get_html(url):
    '''
    :param url:
    :return: html page code
    '''

    header = {
        'authority': 'www.avito.ru',
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'referer': url,
        'upgrade-insecure-requests': '1',
        'user-agent': UserAgent().random,
    }

    sleep(random.randint(1, 3))

    try:
        return requests.get(url, headers=header).text
    except:
        print(f'Error get html code of the page: {url}')
        sleep(60)


def get_mobile_html(url):
    '''
    :param url:
    :return: html code of the mobile version of the page (to retrieve the phone number
    '''

    header = {
        'authority': 'm.avito.ru',
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'referer': url,
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
    }

    sleep(random.randint(1, 3))
    try:
        return requests.get(url, headers=header).text
    except:
        print(f'Error get html code of the mobile version of the page: {url}')
        sleep(60)


def get_soup(html):
    '''
    :param html:
    :return: returns the BeautifulSoup object for the given html
    '''
    try:
        return BeautifulSoup(html, 'lxml')
    except:
        return None


def has_next_page(soup):
    '''
    :param soup:
    :return: logical expression, is there the next page
    '''

    try:
        if soup.find('a', {'class': 'pagination-page js-pagination-next'}):
            return True
    except:
        return False


def get_links_list(soup):
    '''
    :param soup:
    :return: list of links to products from the page
    '''

    try:
        return list(map(lambda soup: 'https://www.avito.ru/' + soup.get('href'),
                        soup.find_all('a', {'class': 'item-description-title-link'})))
    except:
        pass


def get_price(price):
    '''
    :param price:
    :return: formatted price of goods
    '''

    try:
        return ''.join(re.findall(r'\d+', price))
    except:
        raise Exception


def get_address(soup):
    '''
    :param soup:
    :return: formatted seller address
    '''

    address_1 = soup.find('span', {'itemprop': 'name'}).text.strip()
    address_2 = soup.find('span', {'class': 'item-map-address'}).text.strip()

    return ', '.join((address_1, address_2))


def get_phone_number(soup):
    '''
    :param soup:
    :return: formatted phone number of the seller
    '''

    try:
        return ''.join(re.findall(r'\d+', soup.find('a', {'href': re.compile('tel:')}).get('href')))
    except:
        return None


def get_data_from_link(soup):
    '''
    :param soup:
    :return: announcement data
    '''

    try:
        name = soup.find('span', {'class': 'title-info-title-text'}).text.strip()
    except:
        return None

    try:
        price = get_price(soup.find('span', {'class': 'js-item-price'}).text.strip())
    except:
        price = ''

    try:
        seller = soup.find('div', {'class': 'seller-info-name js-seller-info-name'}).find('a').text.strip()
    except:
        seller = ''

    try:
        address = get_address(soup.find('div', {'class': 'item-map-location'}))
    except:
        address = ''

    try:
        description = soup.find('div', {'class': 'item-description-text'}).find('p').text.strip()
    except:
        description = ''

    return {
        'name': name,
        'price': price,
        'seller': seller,
        'address': address,
        'description': description,
    }


def get_visited_links_from_csv_file(file):
    '''
    :param file:
    :return: list of processed links
    '''

    data = list()

    columns = (
        'name',
        'price',
        'seller',
        'phone_number',
        'link',
        'address',
        'description',
    )
    try:
        with open(file) as file:
            try:
                reader = csv.DictReader(file, fieldnames=columns)
                for row in reader:
                    data.append(row.get('link'))
            finally:
                return data
    except:
        return data


def write_data_to_csv_file(file, data):
    '''
    saves the announcement data to csv file
    :param file:
    :param data:
    '''

    columns = (
        'name',
        'price',
        'seller',
        'phone_number',
        'link',
        'address',
        'description',
    )

    with open(file, 'a') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writerow(data)


def main():
    file = 'avito.csv'

    url = f'https://www.avito.ru/' \
        f'{KEYWORDS.get("location")}?' \
        f'p={KEYWORDS.get("page")}&bt=1&' \
        f'q={KEYWORDS.get("search_query")}'

    visited_links_list = get_visited_links_from_csv_file(file)

    while has_next_page(get_soup(get_html(url))):
        url = f'https://www.avito.ru/' \
            f'{KEYWORDS.get("location")}?' \
            f'p={KEYWORDS.get("page")}&bt=1&' \
            f'q={KEYWORDS.get("search_query")}'

        KEYWORDS['page'] += 1

        links_list = get_links_list(get_soup(get_html(url)))

        if links_list:
            for link in links_list:
                if link not in visited_links_list:
                    data = dict()
                    try:
                        data.update(get_data_from_link(get_soup(get_html(link))))
                        data['link'] = link
                        data['phone_number'] = get_phone_number(get_soup(get_mobile_html(link)))
                    except:
                        continue

                    if data['phone_number']:
                        print(f'{len(visited_links_list) + 1}: {data.get("name")}\t{data.get("link")}')
                        write_data_to_csv_file(file, data)
                        visited_links_list.append(link)


if __name__ == '__main__':
    main()
