import praw
import configparser
import urllib.request
import re
import os
import hashlib
from time import sleep

from prawcore.exceptions import Redirect
from prawcore.exceptions import ResponseException
from urllib.error import HTTPError


# Reddit Image Sync
# 2020 Colin Burke
# Scrapes all subreddits defined in subs.txt for (default) 20k max queries each.
# reminder, this is not meant to be a fast operation. Each download takes 2 sec to avoid rate limiting / premature D/C.
# Set it and forget it overnight.
# todo logging in each folder
# todo restrict file size so no error messages are downloaded

class ClientInfo:
    id = ''
    secret = ''
    user_agent = 'Reddit_Image_Scraper'


def delete_img_list():
    f = open('img_links.txt', 'r+')
    f.truncate()


def get_client_info():
    config = configparser.ConfigParser()
    config.read("config.ini")
    id = config["ALPHA"]["client_id"]
    secret = config["ALPHA"]["client_secret"]
    query_limit = config["ALPHA"]["query_limit"]
    ratelimit_sleep = config["ALPHA"]["ratelimit_sleep"]
    failure_sleep = config["ALPHA"]["failure_sleep"]
    minimum_file_size_kb = config["ALPHA"]["minimum_file_size_kb"]  # not implemented yet

    return id, secret, int(query_limit), int(ratelimit_sleep), int(failure_sleep), int(minimum_file_size_kb * 1024)


def save_list(img_url_list):
    for img_url in img_url_list:
        file = open('img_links.txt', 'a')
        file.write('{} \n'.format(img_url))
        file.close()


def clean_sub_files(sub):
    """

    :param sub:str
    :return:
    """
    if os.path.exists('result/{}'.format(sub)):
        os.walk('result/{}'.format(sub))
        pass


def is_media_file(uri):
    # print('Original Link:' + img_link) # enable this if you want to log the literal URLs it sees
    regex = '([.][\w]+)$'
    re.compile(regex)
    t = re.search(regex, uri)

    # extension is the last 3 characters, unless it matches the regex.
    ext = uri[-4:]
    if t:
        ext = t.group()
    if ext in ('.webm', '.gif', '.avi', '.mp4', '.jpg', '.png', '.mov', '.ogg', '.wmv', 'mp2', 'mp3', 'mkv'):
        return True
    else:
        return False


def get_img_urls(sub, lim):
    try:
        r = praw.Reddit(client_id=ClientInfo.id, client_secret=ClientInfo.secret, user_agent=ClientInfo.user_agent)
        submissions1 = r.subreddit(sub).top(time_filter='all', limit=lim)
        submissions2 = r.subreddit(sub).hot(limit=lim)
        submissions3 = r.subreddit(sub).new(limit=lim)
        return [submission.url for submission in list(submissions1) + list(submissions2) + list(submissions3)]
    except Redirect:
        print("get_img_urls() Redirect. Invalid Subreddit?")
        return 0

    except HTTPError:
        print("get_img_urls() HTTPError in last query".format(failure_sleep))
        sleep(10)
        return 0

    except ResponseException:
        print("get_img_urls() ResponseException.")
        return 0


def download_img(img_url, img_title, file_loc, sub, ratelimit_sleep: int, failure_sleep: int):
    # print(img_url + ' ' + img_title + ' ' + file_loc)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        print('Subreddit: /r/{} Filename: {}\nFull URL: {}'.format(sub, img_title, img_url))
        # u = urllib.request.urlopen(img_url)
        # u_metadata = u.info()
        # size = int(u_metadata.getheaders("Content-Length")[0])
        # print(size)

        urllib.request.urlretrieve(img_url, file_loc)
        sleep(ratelimit_sleep)  # this is necessary so you can download the whole sub
        return 1

    except HTTPError:
        print("download_img() HTTPError in last query {} sec wait".format(failure_sleep))
        sleep(failure_sleep)
        return 1

    except urllib.error.URLError:
        print("download_img() URLError! {} sec wait for rate limiting".format(ratelimit_sleep))
        sleep(ratelimit_sleep)
        return 1


def read_img_links(sub):
    with open('img_links.txt') as f:
        links = f.readlines()

    links = [x.strip() for x in links]
    download_count = 0
    download_status = 0

    for link in links:

        if 'gfycat.com' in link and '.gif' not in link[-4:]:
            # print(link[-4:])
            # print('gfycat found:{}'.format(link))
            link = link + '.gif'
        if not is_media_file(link):
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

        download_status = download_img(link, file_name, file_loc, sub, ratelimit_sleep, failure_sleep)

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

        ClientInfo.id, ClientInfo.secret, query_lookup_limit, ratelimit_sleep, failure_sleep, minimum_file_size_kb = get_client_info()

        # subreddit = input('Enter Subreddit: ')
        # query_lookup_limit = int(input('Enter the max amount of queries: '))
        url_list = get_img_urls(subreddit, query_lookup_limit)
        file_no = 1

        if url_list:
            try:
                save_list(url_list)
                count, status = read_img_links(subreddit)

                if status == 1:
                    print('Download Complete from {}\n{} - Images Downloaded\nQuery limit: {} \n'.format(
                        subreddit, count, query_lookup_limit))
                elif status == 0:
                    print('Download Incomplete\n{} - Images Downloaded\n'.format(count))
            except UnicodeEncodeError:
                print('UnicodeEncodeError:{}\n'.format(subreddit))
            except OSError:
                print('OSError:{}\n'.format(subreddit))
        delete_img_list()
