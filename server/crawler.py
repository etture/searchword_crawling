from selenium import webdriver
import datetime
import time
import pprint
from konlpy.tag import Okt
from pymongo import MongoClient
from datetime import datetime

options = webdriver.ChromeOptions()
options.add_argument('window-size=1920x1080')
options.add_argument('--disable-extensions')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver_path = "/usr/bin/chromedriver"
driver = webdriver.Chrome(driver_path, options=options)

client = MongoClient('mongodb://ybigta:ybigta123@ds147181.mlab.com:47181/sandbox_mongodb?retryWrites=false')
db = client.sandbox_mongodb

word_counts = db['word_counts']
aids = db['article_ids']

def category_crawling(sid, num_lastpage):
    news_link = []
    title_list = []

    driver.get("https://news.naver.com/main/main.nhn?mode=LSD&mid=shm&sid1=%s" %sid)

    print('현재 페이지: ', 1)

    boxItems = driver.find_elements_by_css_selector('#section_body > ul.type06_headline>li')
    boxItems.extend(driver.find_elements_by_css_selector('#section_body > ul:nth-child(2)>li'))
    boxItems.extend(driver.find_elements_by_css_selector('#section_body > ul:nth-child(3)>li'))
    boxItems.extend(driver.find_elements_by_css_selector('#section_body > ul:nth-child(4)>li'))

    for li in boxItems:
        print('링크 : ', li.find_element_by_css_selector('a').get_attribute('href'), flush=True)
        news_link.append(li.find_element_by_css_selector('a').get_attribute('href'))

    for page in range(130,num_lastpage):
        driver.get("https://news.naver.com/main/main.nhn?mode=LSD&mid=shm&sid1=%s#&date=%%000:00:00&page=%s" %(sid,page))
        time.sleep(2)
        print('현재 페이지: ', page)

        boxItems = driver.find_elements_by_css_selector('#section_body > ul.type06_headline>li')
        boxItems.extend(driver.find_elements_by_css_selector('#section_body > ul:nth-child(2)>li'))
        boxItems.extend(driver.find_elements_by_css_selector('#section_body > ul:nth-child(3)>li'))
        boxItems.extend(driver.find_elements_by_css_selector('#section_body > ul:nth-child(4)>li'))

        for li in boxItems:
            link = li.find_element_by_css_selector('a').get_attribute('href')

            if aids.find_one({'aid': link[-10:]}):
                continue
            else:
                print('링크 : ', li.find_element_by_css_selector('a').get_attribute('href'), flush=True)
                news_link.append(li.find_element_by_css_selector('a').get_attribute('href'))
                aids.update({'aid': link[-10:]}, {'$setOnInsert': {'title': ' '}}, upsert=True)

    print(news_link, flush=True)

    return news_link


def get_noun_list(news_link):
    noun_list = []
    for li in news_link:
        driver.get(li)
        try:
            elem = driver.find_element_by_xpath('//*[@id="articleBodyContents"]')

            print(elem.text)

            okt = Okt()
            print(okt.nouns(elem.text))
            noun_list.extend(okt.nouns(elem.text))
            print('------------------------------------------------------------------------------------------------------------')
        except Exception as e:
            continue
    return noun_list


def db_update(noun_list, category):
    for word in noun_list:
        print(word, flush=True)
        entry = word_counts.find_one({'category': category, 'word': word})
        if entry is not None:
            word_counts.update_one({'_id': entry['_id']}, {'$inc': {'count': 1}})
        else:
            word_counts.insert_one({'category': category, 'word': word, 'count': 1})
