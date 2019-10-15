import fire
import time
from datetime import datetime
import pytz

from crawler import category_crawling, get_noun_list, db_update


class News:
	def __init__(self):
		self.time_mark = {7: 0, 12: 0, 16: 0, 21: 0}
		self.tz = pytz.timezone('Asia/Seoul')

	def crawl(self, sid):
		if sid == 100:
			#정치 sid = 100
			news_link = category_crawling(100, 170)
			noun_list_politics = get_noun_list(news_link)
			db_update(noun_list_politics, '정치')
		elif sid == 101:
			#경제 sid = 101
			news_link = category_crawling(101, 30)
			noun_list_econ = get_noun_list(news_link)
			db_update(noun_list_econ, '경제')
		elif sid == 102:
			#사회 sid = 102
			news_link = category_crawling(102, 30)
			noun_list_social = get_noun_list(news_link)
			db_update(noun_list_social, '사회')	
		elif sid == 103:
			#문화 sid = 103
			news_link = category_crawling(103, 70)
			noun_list_culture = get_noun_list(news_link)
			db_update(noun_list_culture, '문화')
		elif sid == 104:
			#세계 sid = 104
			news_link = category_crawling(104, 86)
			noun_list_world = get_noun_list(news_link)
			db_update(noun_list_world, '세계')
		elif sid == 105:
			#IT/과학 sid = 105
			news_link = category_crawling(105, 55)
			noun_list_IT = get_noun_list(news_link)
			db_update(noun_list_IT, 'IT/과학')


	def run(self, sid):
		while True:
			cur_hour = datetime.now(self.tz).hour
			if cur_hour in self.time_mark and self.time_mark[cur_hour] == 0:
				# Mark that the current time has been run
				self.time_mark[cur_hour] = 1
				self.crawl(sid)
			elif cur_hour not in self.time_mark:
				# Reset time marks
				for hour in self.time_mark.keys():
					self.time_mark[hour] = 0
			time.sleep(120)


if __name__ == '__main__':
	fire.Fire(News)

