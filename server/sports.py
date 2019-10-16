from selenium import webdriver
import fire
import time
from time import sleep
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
from datetime import date, timedelta
import random
from konlpy.tag import Okt
import pytz

okt = Okt()

client = MongoClient(
    'mongodb://ybigta:ybigta123@ds147181.mlab.com:47181/sandbox_mongodb?retryWrites=false')
db = client.sandbox_mongodb

word_counts = db['word_counts']
aids = db['article_ids']

options = webdriver.ChromeOptions()
options.add_argument('window-size=1920x1080')
options.add_argument('--disable-extensions')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver_path = "/usr/bin/chromedriver"

driver = webdriver.Chrome(driver_path, options=options)

games = ['kbaseball', 'wbaseball', 'kfootball', 'wfootball',
         'basketball', 'volleyball', 'golf', 'general', 'esports']


class Sports:
    def __init__(self):
        self.time_mark = {7: 0}
        self.tz = pytz.timezone('Asia/Seoul')

    def recruit_knights(self, game, day):
        driver.get('https://sports.news.naver.com/'+game +
                   '/news/index.nhn?isphoto=N&date='+str(day)+'&page=1')
        time.sleep(2)
        for i in range(1, 21):
            try:
                a = '//*[@id="_newsList"]/ul/li['+str(i)+']/div/a/span'
                driver.find_element_by_xpath(a).click()
                title = driver.find_element_by_xpath(
                    '//*[@id="content"]/div/div[1]/div/div[1]/h4').text
                body = driver.find_element_by_xpath(
                    '//*[@id="newsEndContents"]').text
                result = '<<<' + title + '>>>' + '\n' + body
                my_aid = driver.current_url[-10:]
                if aids.find_one({'aid': my_aid}):
                    print(str(i)+"th news we already have_")
                    driver.execute_script("window.history.go(-1)")
                    time.sleep(2)
                    continue
                else:
                    aids.update({'aid': my_aid}, {'$setOnInsert': {
                                'title': title}}, upsert=True)
                    one_article = okt.nouns(result)
                    for word in one_article:
                        entry = word_counts.find_one(
                            {'category': '스포츠', 'word': word})
                        entry = word_counts.find_one(
                            {'category': '스포츠', 'word': word})
                        if entry is not None:
                            word_counts.update_one({'_id': entry['_id']}, {
                                                   '$inc': {'count': 1}})
                        else:
                            word_counts.insert_one(
                                {'category': '스포츠', 'word': word, 'count': 1, 'sports_type': game})
                    print(str(i)+'th article done')
                    driver.execute_script("window.history.go(-1)")
                    time.sleep(2)

            except Exception as e:
                print(e)

        print('<< one page done >>')

    def one_sports(self, game):
        for date in self.dates:
            print(game, 'on', date, '--> start')
            self.recruit_knights(game, date)
            print('*', date, '--> done', '\n')

        print("\n", "<<<<", self.today, game, ": All done >>>>")

    def sports_all(self):
        self.today = date.today()
        print("It is", self.today, "\n")

        self.dates = []
        for i in random.sample(range(1, 366), 4):
            x = date.today() - timedelta(i)
            xday = x.strftime('%Y%m%d')
            self.dates.append(xday)

        print(self.dates)
        for game in games:
            self.one_sports(game)
        print("\n", self.today, "Sports Crawling is done")

    def run(self):
        while True:
            cur_hour = datetime.now(self.tz).hour
            if cur_hour in self.time_mark and self.time_mark[cur_hour] == 0:
                # Mark that the current time has been run
                self.time_mark[cur_hour] = 1
                self.sports_all()
            elif cur_hour not in self.time_mark:
                # Reset time marks
                for hour in self.time_mark.keys():
                    self.time_mark[hour] = 0
            time.sleep(120)


if __name__ == '__main__':
    fire.Fire(Sports)

