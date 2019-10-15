from selenium import webdriver
import fire
import time
import pprint
from konlpy.tag import Okt
from pymongo import MongoClient
from datetime import datetime
import pytz

options = webdriver.ChromeOptions()
options.add_argument('window-size=1920x1080')
options.add_argument('--disable-extensions')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver_path = "/usr/bin/chromedriver"
driver = webdriver.Chrome(driver_path, options=options)

client = MongoClient(
    'mongodb://ybigta:ybigta123@ds147181.mlab.com:47181/sandbox_mongodb?retryWrites=false')
db = client.sandbox_mongodb

word_counts = db['word_counts']
aids = db['article_ids']


class Entertain:
    def __init__(self):
        self.time_mark = {7: 0, 12: 0, 16: 0, 21: 0}
        self.tz = pytz.timezone('Asia/Seoul')

    def crawl(self):
        today = datetime.today()
        datestr = '%d-%s-%s' % (today.year, str(today.month).zfill(2), str(today.day).zfill(2))

        news_link = []

        num_lastpage = 31
        driver.get("https://entertain.naver.com/home")

        for i in range(6):
            driver.find_element_by_xpath(
                '//*[@id="left_cont"]/div[15]/div[2]/a/span').click()

        print('현재 페이지: ', 1)

        boxItems = driver.find_elements_by_css_selector('#newsWrp > ul>li')

        # 기사들중 링크 저장
        for li in boxItems:
            print('링크 : ', li.find_element_by_css_selector('a').get_attribute('href'))
            news_link.append(li.find_element_by_css_selector(
                'a').get_attribute('href'))

        for page in range(2, num_lastpage):
            driver.get(
                "https://entertain.naver.com/now#sid=106&date=%s&page=%s" % (datestr, page))
            time.sleep(2)
            print('현재 페이지: ', page)

            # 각 페이지의 기사들 크롤링(이 예제의 경우 page 2-11까지)
            boxItems = driver.find_elements_by_css_selector('#newsWrp > ul>li')
            # 기사들중 링크 저장
            for li in boxItems:
                link = li.find_element_by_css_selector(
                    'a').get_attribute('href')

                if aids.find_one({'aid': link[-10:]}):
                    continue
                else:
                    print('링크 : ',link)
                    news_link.append(link)
                    aids.update_one(
                        {'aid': link[-10:]}, {'$setOnInsert': {'title': ' '}}, upsert=True)

        noun_list = []
        for li in news_link:
            driver.get(li)
            try:
                elem = driver.find_element_by_xpath('//*[@id="articleBody"]')
                okt = Okt()
                noun_list.extend(okt.nouns(elem.text))
                
            except Exception as e:
                continue
        
        category = '연예'
        for word in noun_list:
            print(word)
            entry = word_counts.find_one({'category': category, 'word': word})
            # 카테고리-단어가 존재하면 count+=1, 없으면 새로 집어넣고 count=1
            if entry is not None:
                word_counts.update_one({'_id': entry['_id']}, {'$inc': {'count': 1}})
            else:
                word_counts.insert_one({'category': category, 'word': word, 'count': 1})

    def run(self):
        while True:
            cur_hour = datetime.now(self.tz).hour
            if cur_hour in self.time_mark and self.time_mark[cur_hour] == 0:
                # Mark that the current time has been run
                self.time_mark[cur_hour] = 1
                self.crawl()
            elif cur_hour not in self.time_mark:
                # Reset time marks
                for hour in self.time_mark.keys():
                    self.time_mark[hour] = 0
            time.sleep(120)


if __name__ == '__main__':
    fire.Fire(Entertain)

