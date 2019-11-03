from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
from konlpy.tag import Okt
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
from IPython.core.display import display, HTML
from collections import Counter
import fire
matplotlib.rc("savefig", dpi=300)
# fm._rebuild()

# font_location = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
# font_name = fm.FontProperties(fname = font_location).get_name()
# matplotlib.rc('font', family = font_name)
# plt.rcParams['font.family'] = font_name

okt = Okt()
client = MongoClient('mongodb://ybigta:ybigta123@ds147181.mlab.com:47181/sandbox_mongodb?retryWrites=false')
db = client.sandbox_mongodb

searchword_lists = db['searchword_lists']
word_counts = db['word_counts']

class mod:
    def hi():
        print('hi')

def single_searchword(searchword):
    tokens = okt.morphs(searchword)
    ret = dict()
    for token in tokens:
        total_count = 0
        ret.setdefault(token, dict())
        for find in word_counts.find({'word': token}):
            ret[token][find['category']] = find['count']
            total_count += find['count']
        ret[token]['total_count'] = total_count
    return ret

def searchword_list_summary(searchword_list):
    summary = dict()
    all_counts = dict()
    for searchword in searchword_list['searchwords']:
        counts = single_searchword(searchword)
        total_cnt = 0
        cate_cnt = dict()
        category_percent = dict()
        for word, categories in counts.items():
            if categories['total_count'] == 0:
                continue
            total_cnt += categories['total_count']
            for cate, cnt in [(cate, cnt) for (cate, cnt) in categories.items() if cate != 'total_count']:
                cate_cnt.setdefault(cate, 0)
                cate_cnt[cate] += cnt
                all_counts.setdefault(cate, 0)
                all_counts[cate] += cnt
        for cate in cate_cnt.keys():
            category_percent[cate] = cate_cnt[cate] / total_cnt
        summary[searchword] = category_percent
    summary['all_counts'] = all_counts
    return summary

# Pie Chart
def show_pie(result, title, save=False):
    labels = [k for k in result.keys() if k != 'total_count']
    sizes = [result[lab] for lab in labels]
    colors_preset = {
        '스포츠': '#ff9999',
        '연예': '#66b3ff',
        '세계': '#99ff99',
        'IT/과학': '#ffcc99', 
        '정치': '#ffe78f', 
        '경제': '#e299ff', 
        '사회': '#c2c2c2', 
        '문화': '#93fad4'
    }
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, colors=[colors_preset[lab] for lab in labels], autopct='%1.1f%%', shadow=False, startangle=90)
    ax1.axis('equal')
    plt.title(title, bbox={'facecolor':'0.8', 'pad':5}, pad=20)
    plt.tight_layout()
    if save:
        plt.savefig('./fig.png')
    plt.show()
    
def searchword_analysis(datetime_obj, age_group):
    '''
    datetime_obj in the form of datetime(2018, 4, 25, 0, 0, 0, 0)
    age_group: ('all', '10', '20', '30', '40', '50')
    '''
#     datetime_obj = datetime(year, month, day, hour, 0, 0, 0)
    searchword_list = searchword_lists.find_one({'dt': datetime_obj, 'age_group': age_group})
    summary = searchword_list_summary(searchword_list)
    display(HTML(f'<h2>{year}년 {month}월 {day}일 {hour}시 검색어</h2>'))
    list_html = ''
    for word in searchword_list['searchwords']:
        list_html += f'<li>{word}</li>'
    display(HTML(f'<ol>{list_html}</ol>'))
    # Total
    title = 'all_counts'
    show_pie(summary[title], title=title, save=True)
    # Individual searchwords
    searchwords = [s for s in summary.keys() if s != 'all_counts']
    for s in searchwords:
        show_pie(summary[s], title=s, save=True)

        
def searchword_cate_cnts(searchword_list):
    all_counts = dict()
    main_category = dict()
    for searchword in searchword_list['searchwords']:
        counts = single_searchword(searchword)
        total_cnt = 0
        cate_cnt = dict()
        category_percent = dict()
        for word, categories in counts.items():
            if categories['total_count'] == 0:
                continue
            total_cnt += categories['total_count']
            for cate, cnt in [(cate, cnt) for (cate, cnt) in categories.items() if cate != 'total_count']:
                cate_cnt.setdefault(cate, 0)
                cate_cnt[cate] += cnt
                all_counts.setdefault(cate, 0)
                all_counts[cate] += cnt
        for cate in cate_cnt.keys():
            category_percent[cate] = cate_cnt[cate] / total_cnt
        if bool(category_percent) == False:
            continue
        main_category[searchword] = max(category_percent, key=lambda k: category_percent[k])
    return Counter(main_category.values())


def collect_data(age_group):
    start_date = datetime(2018, 10, 10, 6, 0, 0, 0)
    end_date = datetime(2019, 9, 30, 21, 0, 0, 0)
    cur_date = start_date
    
    cate_list = ['정치', '경제', '사회', '세계', '문화', 'IT/과학', '연예', '스포츠']
    # To run only 4 times per month
    days_to_run = [4, 11, 19, 26]
    result_list = []
    
    while cur_date <= end_date:
        if cur_date.day not in days_to_run:
            print(f'<SKIP> {cur_date} 스킵', flush=True)
            cur_date += timedelta(hours=3)
            continue
        print(f'<START> {cur_date} 검색어 시작', flush=True)
        searchword_list = searchword_lists.find_one({'dt': cur_date, 'age_group': age_group})
        if searchword_list is None:
            print(f'<MISSING> {cur_date} 검색어 리스트 DB에 없음!', flush=True)
            cur_date += timedelta(hours=3)
            continue
        cate_cnts = searchword_cate_cnts(searchword_list)
        cur_entry = [cur_date, 20]
        for cate in cate_list:
            if cate in cate_cnts:
                cur_entry.append(cate_cnts[cate])
            else:
                cur_entry.append(0)
        result_list.append(cur_entry)
        print(f'<OK> {cur_date} 검색어 리스트 정상 처리', flush=True)
        cur_date += timedelta(hours=3)

    result_df = pd.DataFrame(result_list, columns=['datetime', 'all', 'politics', 'economy', 'society', 'world', 'culture', 'it', 'entertainment', 'sports'])
    result_df.to_csv(f'./{age_group}.csv')

if __name__ == '__main__':
    fire.Fire(collect_data)
