# Reddit Image Sync
# 2021 Colin Burke
# Scrapes all subreddits defined in subs.txt for (default) 20k max queries each.
# reminder, this is not meant to be a fast operation. Each download takes 2 sec to avoid rate limiting / premature D/C.
# Set it and forget it overnight.

# install "praw" on pip
import praw
import configparser
import urllib.request
import re
import os

from prawcore.exceptions import Redirect
from prawcore.exceptions import ResponseException
from urllib.error import HTTPError
import http.client
import time
from time import sleep
from datetime import datetime

now = datetime.now()
logfile_date = now.strftime("%d-%m-%Y-%H.%M.%S")
dt_name = now.strftime("%d-%m-%Y-%H.%M.%S")

if not os.path.exists('./logs'):
    print('log directory created. Is this your first time running?')
    os.mkdir('./logs')


def log(text):
    print(text)
    now = datetime.now()
    logfile = open('./logs/{}.txt'.format(logfile_date), 'a')
    event_time = now.strftime("%d-%m-%Y-%H.%M.%S")
    logfile.write('{}: {}\n'.format(event_time, text))


class ClientInfo:
    id = ''
    secret = ''
    user_agent = 'Reddit_Image_Scraper'


def badlist_cleanup(minimum_file_size_kb):
    """removes small files, cleans and de-dupes the badlist"""

    # crawl all directories recursively, find files lower than 15kb, add them to the badlist, then delete them.
    for root, subdirs, files in os.walk('./result'):
        for file in files:
            fullpath = os.path.join(root, file)
            filesize = os.path.getsize(fullpath) / 1000
            if 'gitignore' in fullpath:
                continue
            if filesize < minimum_file_size_kb:
                add_to_badlist(file)
                print(str(fullpath) + " \t" + str(filesize) + "KB")
                os.remove(fullpath)

    # create badlist if it's not there
    if not os.path.exists('badlist.txt'):
        with open('badlist.txt', 'w') as f:
            log('badlist.txt created. Is this your first time running?')
            f.write('')

    # de-duplicate the badlist.
    with open('badlist.txt', 'r') as f:
        in_list = set(f.readlines())

    # we-write the badlist back to itself.
    with open('badlist.txt', 'w') as f:
        f.writelines(in_list)


def add_to_badlist(filename):
    with open('badlist.txt', 'a') as f:
        f.writelines(filename + '\n')
        log("added {} to badlist".format(filename))


def get_client_info():
    s = os.path.exists('config.ini')
    if not s:
        with open('config.ini', 'w') as f:
            log('config.ini template created. Please paste in your client secret. (And RTM)')
            f.write("""[ALPHA]
client_id=PASTE ID HERE
client_secret=PASTE SECRET HERE
query_limit=2000
ratelimit_sleep=2
failure_sleep=10
minimum_file_size_kb=12.0""")
    config = configparser.ConfigParser()
    config.read("config.ini")
    id = config["ALPHA"]["client_id"]
    secret = config["ALPHA"]["client_secret"]
    query_limit = config["ALPHA"]["query_limit"]
    ratelimit_sleep = config["ALPHA"]["ratelimit_sleep"]
    failure_sleep = config["ALPHA"]["failure_sleep"]
    minimum_file_size_kb = config["ALPHA"]["minimum_file_size_kb"]
    return id, secret, int(query_limit), int(ratelimit_sleep), int(failure_sleep), float(minimum_file_size_kb)


def is_media_file(uri):
    # print('Original Link:' + img_link) # enable this if you want to log the literal URLs it sees
    regex = '([.][\w]+)$'
    re.compile(regex)
    t = re.search(regex, uri)

    # extension is in the last 4 characters, unless it matches the regex.
    ext = uri[-4:]
    if t:
        ext = t.group()
    if ext in ('.webm', '.gif', '.avi', '.mp4', '.jpg', '.png', '.mov', '.ogg', '.wmv', '.mp2', '.mp3', '.mkv'):
        return True
    else:
        return False


def get_img_urls(sub, limit):
    # TODO how do I automate these generators?
    time_filters = ['hour', 'month', 'all', 'week', 'year', 'day']
    try:
        all_start = time.time()
        if ClientInfo.id == 'PASTE ID HERE' or ClientInfo.secret == 'PASTE SECRET HERE':
            log('Error: Please enter your "Client Info" and "Secret" into config.ini')
        r = praw.Reddit(client_id=ClientInfo.id, client_secret=ClientInfo.secret, user_agent=ClientInfo.user_agent)
        start = time.time()
        submissions = [submission.url for submission in r.subreddit(sub).top(time_filter='all', limit=limit)]
        end = time.time()
        log('Query return time for ALL:{},\nTotal Found: {}'.format(str(end - start), len(submissions)))

        start = time.time()
        submissions2 = [submission.url for submission in r.subreddit(sub).top(time_filter='year', limit=limit)]
        end = time.time()
        log('Query return time for year:{},\nTotal Found: {}'.format(str(end - start), len(submissions2)))

        start = time.time()
        submissions3 = [submission.url for submission in r.subreddit(sub).top(time_filter='month', limit=limit)]
        end = time.time()
        log('Query return time for month:{},\nTotal Found: {}'.format(str(end - start), len(submissions3)))

        start = time.time()
        submissions4 = [submission.url for submission in r.subreddit(sub).top(time_filter='week', limit=limit)]
        end = time.time()
        log('Query return time for week:{},\nTotal Found: {}'.format(str(end - start), len(submissions4)))

        start = time.time()
        submissions5 = [submission.url for submission in r.subreddit(sub).top(time_filter='hour', limit=limit)]
        end = time.time()
        log('Query return time for hour:{},\nTotal Found: {}'.format(str(end - start), len(submissions5)))

        start = time.time()
        submissions6 = [submission.url for submission in r.subreddit(sub).top(time_filter='day', limit=limit)]
        end = time.time()
        log('Query return time for day:{},\nTotal Found: {}'.format(str(end - start), len(submissions6)))

        start = time.time()
        submissions7 = [submission.url for submission in r.subreddit(sub).hot(limit=limit)]
        end = time.time()
        log('Query return time for HOT:{},\nTotal Found: {}'.format(str(end - start), len(submissions7)))

        start = time.time()
        submissions8 = [submission.url for submission in r.subreddit(sub).new(limit=limit)]
        end = time.time()
        log('Query return time for NEW:{},\nTotal Found: {}'.format(str(end - start), len(submissions8)))

        start = time.time()
        submissions9 = [submission.url for submission in r.subreddit(sub).rising(limit=limit)]
        end = time.time()
        log('Query return time for RISING:{},\nTotal Found: {}'.format(str(end - start), len(submissions9)))

        # combine them all, and de-duplicate them
        submissions = list(set(
            submissions + submissions2 + submissions3 + submissions4 + submissions5 + submissions6 + submissions7 + submissions8 + submissions9))

        log('total unique submissions: {}'.format(len(submissions)))

        all_end = time.time()
        log('Query return time for :{}: {}'.format(str(sub), str(all_end - all_start)))
        return submissions

    except Redirect:
        log("get_img_urls() Redirect. Invalid Subreddit?")
        return 0

    except HTTPError:
        log("get_img_urls() HTTPError in last query")
        sleep(10)
        return 0

    except ResponseException:
        log("get_img_urls() ResponseException.")
        return 0


def download_img(img_url, img_title, file_loc, sub, ratelimit_sleep: int, failure_sleep: int):
    # print(img_url + ' ' + img_title + ' ' + file_loc)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        log('Subreddit: /r/{} - Full URL: {}'.format(sub, img_title, img_url))
        u = urllib.request.urlopen(img_url)
        u_metadata = u.info()
        # size = int(u_metadata.getheaders("Content-Length")[0])
        # print(size)

        urllib.request.urlretrieve(img_url, file_loc)
        sleep(ratelimit_sleep)  # remove this at your own risk. This is necessary so you can download the whole sub!
        return 0

    except HTTPError as e:
        log("download_img() HTTPError in last query (file might not exist anymore, or malformed URL)")
        with open('badlist.txt', 'a') as f:
            f.writelines(img_title + '\n')
            log("added to badlist")
        log(e)
        sleep(failure_sleep)
        return 1

    except urllib.error.URLError as e:
        log("download_img() URLError! Site might be offline")
        log(e)
        with open('badlist.txt', 'a') as f:
            f.writelines(img_title + '\n')
            log("added to badlist")
        sleep(ratelimit_sleep)
        return 1

    except http.client.InvalidURL as e:
        log('Crappy URL')
        log(e)
        add_to_badlist(img_title)
        return 1


def read_img_links(sub, url_list):
    if not os.path.exists('./result'):
        os.mkdir('./result')
    if not os.path.exists('./result/{}'.format(sub)):
        os.mkdir('./result/{}'.format(sub))

    url_list = [x.strip() for x in url_list]
    url_list.sort()
    download_count = 0
    exist_count = 0
    download_status = 0

    with open('badlist.txt', 'r') as f:
        badlist = f.readlines()
        badlist = [x.strip() for x in set(badlist)]

    for link in url_list:
        if 'gfycat.com' in link and '.gif' not in link[-4:] and '.webm' not in link[-4:]:
            # print(link[-4:])
            # print('gfycat found:{}'.format(link))
            link = link + '.gif'
        if not is_media_file(link):
            continue

        file_name = link.split('/')[-1]
        if file_name in badlist:
            # print('{} found in badlist, skipping'.format(file_name))
            continue
        file_loc = 'result/{}/{}'.format(sub, file_name)
        if os.path.exists(file_loc):
            # print(file_name + ' already exists')
            exist_count += 1
            continue

        if not file_name:
            log(file_name + ' cannot download')
            continue

        download_status = download_img(link, file_name, file_loc, sub, ratelimit_sleep, failure_sleep)

        download_count += 1
    return download_count, download_status, exist_count


if __name__ == '__main__':
    ClientInfo.id, ClientInfo.secret, query_lookup_limit, ratelimit_sleep, failure_sleep, minimum_file_size_kb = get_client_info()
    # if exited unexpectedly, clean up the image list file.
    badlist_cleanup(minimum_file_size_kb)

    going = True
    if not os.path.exists('./subs.txt'):
        with open('./subs.txt', 'w') as f:
            log('subs.txt created. You need to add subreddits to it now.')
            f.write(
                '# add your subs here. you can comment out subs like this line, as well, if you\'d prefer to not download some subs.')
    f = open('./subs.txt', 'r')

    for subreddit in f.readlines():
        if '#' in subreddit:
            continue
        subreddit = subreddit.strip('\n')
        log('Starting Retrieval from: /r/' + subreddit)

        # subreddit = input('Enter Subreddit: ')
        # query_lookup_limit = int(input('Enter the max amount of queries: '))
        url_list = []
        url_list = get_img_urls(subreddit, query_lookup_limit)
        file_no = 1

        if url_list:
            try:
                log('{} images found on {}'.format(len(url_list), subreddit))
                count, status, already_here = read_img_links(subreddit, url_list)

                if status == 1:
                    log(
                        'Download Complete from {}\n{} - Images Downloaded\nQuery limit: {} \nAlready downloaded: {} \n'.format(
                            subreddit, count, query_lookup_limit, already_here))
                elif status == 0:
                    log(
                        'Download Complete from {}\n{} - Images Downloaded\nQuery limit: {} \nAlready downloaded: {} \n'.format(
                            subreddit, count, query_lookup_limit, already_here))
            except UnicodeEncodeError:
                log('UnicodeEncodeError:{}\n'.format(subreddit))
            except OSError as e:

                log('OSError:{}\nVerbose:{}'.format(subreddit, e))
        # confirm = input('confirm next sub? CTRL+C to cancel.')
