import praw
import configparser
import urllib.request
import re
import os
from time import sleep

from prawcore.exceptions import Redirect
from prawcore.exceptions import ResponseException
from urllib.error import HTTPError

# Reddit Image Sync
# 2020 Colin Burke
# Scrapes all subreddits defined in subs.txt for (default) 20k max queries each.
# reminder, this is not meant to be a fast operation. Each download takes 2 sec to avoid rate limiting / premature D/C.
# Set it and forget it overnight.


class ClientInfo:
    id = ''
    secret = ''
    user_agent = 'Reddit_Image_Scraper'


def get_client_info():
    config = configparser.ConfigParser()
    config.read("config.ini")
    id = config["ALPHA"]["client_id"]
    secret = config["ALPHA"]["client_secret"]
    query_limit = config["ALPHA"]["query_limit"]

    return id, secret, query_limit


def save_list(img_url_list):
    for img_url in img_url_list:
        file = open('img_links.txt', 'a')
        file.write('{} \n'.format(img_url))
        file.close()


def delete_img_list():
    f = open('img_links.txt', 'r+')
    f.truncate()


def is_img_link(img_link):
    # print('Original Link:' + img_link) # enable this if you want to log the literal URLs it sees
    regex = '([.][\w]+)$'
    re.compile(regex)
    t = re.search(regex, img_link)

    # extension is the last 3 characters, unless it matches the regex.
    ext = img_link[-4:]
    if t:
        ext = t.group()

    if ext in ('.webm', '.gif', '.avi', '.mp4', '.jpg', '.png', '.mov', '.ogg', '.wmv', 'mp2', 'mp3', 'mkv'):
        return True
    else:
        return False


def get_img_urls(sub, li):
    try:
        r = praw.Reddit(client_id=ClientInfo.id, client_secret=ClientInfo.secret, user_agent=ClientInfo.user_agent)
        submissions = r.subreddit(sub).top(time_filter='all', limit=li)
        return [submission.url for submission in submissions]

    except Redirect:
        print("get_img_urls() Redirect. Invalid Subreddit?")
        return 0

    except HTTPError:
        print("get_img_urls() HTTPError in last query")
        sleep(10)
        return 0

    except ResponseException:
        print("get_img_urls() ResponseException.")
        return 0


def download_img(img_url, img_title, file_loc, sub):
    # print(img_url + ' ' + img_title + ' ' + file_loc)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        print('Sub:{} Filename:{}'.format(sub, img_title))
        urllib.request.urlretrieve(img_url, file_loc)
        sleep(2)  # this is necessary so you can download the whole sub
        return 1

    except HTTPError:
        print("download_img() HTTPError in last query")
        sleep(10)
        return 1

    except urllib.error.URLError:
        print("download_img() URLError!")
        sleep(2)
        return 1


def read_img_links(sub):
    with open('img_links.txt') as f:
        links = f.readlines()

    links = [x.strip() for x in links]
    download_count = 0
    download_status = 0

    for link in links:
        if not is_img_link(link):
            continue

        file_name = link.split('/')[-1]
        if not os.path.exists('result/{}'.format(sub)):
            os.mkdir('result/{}'.format(sub))
        file_loc = 'result/{}/{}'.format(sub, file_name)
        if os.path.exists(file_loc):
            print(file_name + ' already exists')
            continue

        if not file_name:
            print(file_name + ' cannot download')
            continue

        download_status = download_img(link, file_name, file_loc, sub)

        download_count += 1

    return download_count, download_status


if __name__ == '__main__':
    going = True
    f = open('./subs.txt', 'r')

    for subreddit in f.readlines():
        if '#' in subreddit:
            continue
        subreddit = subreddit.strip('\n')
        print('Starting Retrieval from: /r/' + subreddit)
        delete_img_list()

        ClientInfo.id, ClientInfo.secret, query_lookup_limit = get_client_info()

        # subreddit = input('Enter Subreddit: ')
        # query_lookup_limit = int(input('Enter the max amount of queries: '))
        url_list = get_img_urls(subreddit, query_lookup_limit)
        file_no = 1

        if url_list:
            try:
                save_list(url_list)
                count, status = read_img_links(subreddit)

                if status == 1:
                    print('\nDownload Complete\n{} - Images Downloaded\nQuery limit: {} '.format(count,
                                                                                                 query_lookup_limit))
                elif status == 0:
                    print('\nDownload Incomplete\n{} - Images Downloaded'.format(count))
            except UnicodeEncodeError:
                print('unicode error')
        delete_img_list()
