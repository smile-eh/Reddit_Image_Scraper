import praw
import configparser
import urllib.request
import re
from time import sleep

from prawcore.exceptions import Redirect
from prawcore.exceptions import ResponseException
from urllib.error import HTTPError


class ClientInfo:
    id = ''
    secret = ''
    user_agent = 'Reddit_Image_Scraper'


def get_client_info():
    config = configparser.ConfigParser()
    config.read("config.ini")
    id = config["ALPHA"]["client_id"]
    secret = config["ALPHA"]["client_secret"]

    return id, secret


def save_list(img_url_list):
    for img_url in img_url_list:
        file = open('img_links.txt', 'a')
        file.write('{} \n'.format(img_url))
        file.close()


def delete_img_list():
    f = open('img_links.txt', 'r+')
    f.truncate()


def is_img_link(img_link):
    regex = '([.][\w]+)$'
    re.compile(regex)
    print(img_link)
    t = re.search(regex, img_link)
    ext = img_link[-4:]
    if t:
        ext = t.group()
        print(ext)

    if ext in ('.webm', '.gif', '.avi', '.mp4', '.gifv', '.jpg', '.png', '.mov'):
        return True
    else:
        return False


def get_img_urls(sub, li):
    try:
        r = praw.Reddit(client_id=ClientInfo.id, client_secret=ClientInfo.secret, user_agent=ClientInfo.user_agent)
        submissions = r.subreddit(sub).top(time_filter='all', limit=li)
        return [submission.url for submission in submissions]

    except Redirect:
        print("Invalid Subreddit!")
        return 0

    except HTTPError:
        print("Too many Requests. Try again later!")
        sleep(10)
        return 0

    except ResponseException:
        print("Client info is wrong. Check again.")
        return 0


def download_img(img_url, img_title, filename):
    print(img_url + ' ' + img_title + ' ' + filename)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        print('Downloading ' + img_title + '....')
        urllib.request.urlretrieve(img_url, filename)
        sleep(2)  # this is necessary so you can download the whole sub
        return 1

    except HTTPError:
        print("Too many Requests. Try again later!")
        sleep(10)
        return -1

    except urllib.error.URLError:
        print("URLError!")
        sleep(2)
        return 1


def read_img_links():
    with open('img_links.txt') as f:
        links = f.readlines()

    links = [x.strip() for x in links]
    download_count = 0

    for link in links:
        if not is_img_link(link):
            continue

        file_name = link.split('/')[-1]
        file_loc = 'result/{}'.format(file_name)

        if not file_name:
            print(file_name + ' cannot download')
            continue

        download_status = download_img(link, file_name, file_loc)
        download_count += 1

        if download_status == 0:
            return download_count, 0

    return download_count, 1


if __name__ == '__main__':
    delete_img_list()

    ClientInfo.id, ClientInfo.secret = get_client_info()

    subreddit = input('Enter Subreddit: ')
    query_lookup_limit = int(input('Enter the max amount of queries: '))
    print()
    url_list = get_img_urls(subreddit, query_lookup_limit)
    file_no = 1

    if url_list:

        save_list(url_list)
        count, status = read_img_links()

        if status == 1:
            print('\nDownload Complete\n{} - Images Downloaded\n{} - Posts Not found, or ignored'.format(count,
                                                                                                         query_lookup_limit - count))
        elif status == 0:
            print('\nDownload Incomplete\n{} - Images Downloaded'.format(count))
    delete_img_list()
