#!/usr/bin/env python3
import os
import sqlite3
from bs4 import BeautifulSoup
from requests import get
from slacker import Slacker


class UseSqlite3:
    def __init__(self, mode=None):
        db_file_path = os.environ.get('SQLITE3_FOR_CHOCO')
        self.conn = sqlite3.connect(db_file_path)
        self.c = self.conn.cursor()

        self.c.execute('''
        CREATE TABLE IF NOT EXISTS sent_msg_rasp (
        "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "url" text,
        "update_time" datetime
        )''')

    def already_sent_check(self, url):
        if url is None:
            return False  # ignore

        query = 'SELECT * FROM sent_msg_rasp WHERE url="%s"' % url
        self.c.execute(query)
        data = self.c.fetchone()
        if data is None:
            return False
        else:
            return True

    def insert_rasp(self, url):
        query = '''INSERT INTO sent_msg_rasp VALUES
        (NULL, "%s", CURRENT_TIMESTAMP)''' % url
        self.c.execute(query)
        self.conn.commit()


def check_duplicate(url):
    s = UseSqlite3()

    url = url.replace('\"', '\'')  # for query failed
    ret = s.already_sent_check(url)
    if ret:
        print('Already exist: ', url)
        return True

    s.insert_rasp(url)
    return False


def match_soup_class(target, mode='class'):
    def do_match(tag):
        classes = tag.get(mode, [])
        return all(c in classes for c in target)
    return do_match


def get_life_hacker():

    url = 'http://lifehacker.com/tag/raspberry-pi'
    r = get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    rb_news_msg = []
    for l in soup.find_all(match_soup_class(['postlist__item'])):
        if len(l.a.text) == 0:
            continue
        rb_title = l.a.text
        rb_url = l.a['href']

        if (check_duplicate(rb_url)):
            continue
        rb_news = '[Raspberry pi news]\n%s\n%s\n\n' % (rb_title, rb_url)
        rb_news_msg.append(rb_news)

    return rb_news_msg


def get_alphr():
    url = 'http://www.alphr.com/raspberry-pi'
    r = get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    alphr = []
    # print(soup)
    for l in soup.find_all(match_soup_class(['page-main-area'])):
        for g in l.find_all(match_soup_class(['field-group-format'])):
            msg = '%s\nhttp://www.alphr.com%s' % (g.a.text, g.a['href'])
            alphr.append(msg)
    return alphr


def main():
    token = os.environ.get('CHOCOPY_SLACK_BOT')
    s = Slacker(token)

    news = get_life_hacker()
    for i in range(len(news)):
        # print(rb_news[i])
        s.chat.post_message('raspberrypi', news[i])

    del news[:]
    news = get_alphr()
    for i in range(len(news)):
        # print(rb_news[i])
        s.chat.post_message('raspberrypi', news[i])


if __name__ == '__main__':
    main()
