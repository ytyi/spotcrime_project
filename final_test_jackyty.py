##name: Yang Tianyi
##unique name: jackyty

import requests
from bs4 import BeautifulSoup
import numpy as np
import sys, os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json
from pandas import DataFrame
import sqlite3
from flask import Flask, render_template

app = Flask(__name__,static_url_path='',static_folder='static')
CACHE_FILE_NAME = 'SI507_Final_Project.json'

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache,headers='none',params='none'):
    if (url in cache.keys()): 
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        response = requests.get(url,headers=headers,params=params)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

CACHE_DICT = load_cache()

base_url = 'https://spotcrime.com/'
cities = [
    'mi/ann+arbor/',
    'mi/detroit/',
    'mo/st.+louis/',
    'md/baltimore/',
    'oh/toledo/',
    'ga/albany/',
    'mi/flint/',
    'tn/memphis/',
    'pa/philadelphia/',
]

def get_daily(city):
    headers = { 'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'}
    res = make_url_request_using_cache('https://spotcrime.com/' + city + 'daily-archive',CACHE_DICT,headers)
    soup = BeautifulSoup(res, 'html.parser')
    crime_daily_url_dict={}
    crime_report_daily = soup.find('div', class_='default-page-container')
    crime_report_daily_urls = crime_report_daily.find_all('a',recursive=False)
    for crime_report_daily_url in crime_report_daily_urls:
        #print(crime_report_daily_url)
        #print(crime_report_daily_url.text.strip().lower())
        #print(crime_report_daily_url['href'])
        crime_daily_url_dict[crime_report_daily_url.text.strip().lower()]=base_url+crime_report_daily_url['href']
    return crime_daily_url_dict
    #for state_listing_ul in state_listing_uls:
        #state_url_dict[state_listing_ul.text.strip().lower()]=BASE_URL+state_listing_ul.find('a')['href']
    #return state_url_dict

def specific_daily(dict):
    headers = { 'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'}
    crime_dict=[]
    for i in dict.keys():
        crime_dict=crime_dict+helper(dict[i])
    #map_dict={'01':'Jan','02':'Feb','03':'Mar','04':'Apr' ,'05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}
    df = pd.DataFrame(crime_dict, columns=['Type', 'Time', 'Location'])
    df['Month']=df['Time'].map(lambda x: x.split()[0].split('/')[0])
    df['Date']=df['Time'].map(lambda x: x.split()[0])
    return df

def helper(url):
    headers = { 'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'}
    res=make_url_request_using_cache(url,CACHE_DICT,headers)
    soup = BeautifulSoup(res, 'html.parser')
    crime_daily_url_dict={}
    crime_report_daily = soup.find('div', class_='city-page__crimes-container')
    crime_report_daily_urls = crime_report_daily.find_all('a',recursive=False)
    map_dict=a={'01':'Jan','02':'Feb','03':'Mar','04':'Apr' ,'05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}
    a=[]
    for crime_report_daily_url in crime_report_daily_urls:
        a.append([crime_report_daily_url.find('span',class_="city-page__crime-card-title").text.strip(),crime_report_daily_url.find('span',class_="city-page__crime-card-date").text.strip(),crime_report_daily_url.find('span',class_="city-page__crime-card-address").text.strip()])
        
    #df = pd.DataFrame(a, columns=['one', 'two', 'three']) 
    return a

def database_create(database,table):

    conn = sqlite3.connect('database/'+database)
    cur = conn.cursor()
    drop_crime = '''
    DROP TABLE IF EXISTS "crime";
'''
    drop_crime_info = '''
    DROP TABLE IF EXISTS "crime_info";
'''

    create_crime = '''
    create table crime
(
	crime_id int not null
		constraint crime_pk
			primary key,
	type text,
	time text
);
  
'''

   
    create_crime_info='''
   create table crime_info
(
	crime_id int not null
		constraint crime_info_pk
			primary key
		constraint crime_info_crime_crime_id_fk
			references crime
				on delete cascade,
	month int,
	date date
);
'''
    
    cur.execute(drop_crime)
    cur.execute(drop_crime_info)
    
    cur.execute(create_crime)
    cur.execute(create_crime_info)
    table1=table.copy()
    table1.reset_index(inplace=True)
    table1.rename(columns={'index':'id'},inplace=True)
    for i in range(table1.shape[0]):
        a=f"INSERT INTO crime VALUES ({int(table1.iloc[i].id)}, '{table1.iloc[i].Type}', '{table1.iloc[i].Time}')"
        
        cur.execute(a)
        #print(float(i/table1.shape[0]*100))
    for i in range(table1.shape[0]):
        a=f"INSERT INTO crime_info VALUES ({int(table1.iloc[i].id)}, {table1.iloc[i].Month}, '{table1.iloc[i].Date}')"
        #print(a)
        cur.execute(a)

    conn.commit()


def interface():
    for number in range(7):
        # print('Choose a city of which you are interested in its crime condition?')
        # print('1. Ann Arbor   2. Detroit  3. St Louis  4. Baltimore  5. Toledo  6. Albany  7. Exit /n')
        # number=input()
        if number == '7':
            break
        city = cities[int(number) - 1]
        city_urls = get_daily(city)
        city_df = specific_daily(city_urls)

        plt.figure()
        city_df.Type.value_counts().head(10).plot(kind='bar')
        plt.title("Bar Chart of Crime Type Counts")
        plt.xticks(rotation=45)
        plt.savefig(f'static/Type_bar_{number}.jpg')

        #plt.show()
        pie_df = city_df.Type.value_counts().reset_index()
        pie_col = ['type', 'num']
        pie_df.columns = pie_col
        plt.figure(figsize=[20, 15])
        explode = [0.1]
        for i in range(len(pie_df.type) - 1):
            explode.append(0)
        plt.pie(pie_df.num, labels=pie_df.type, explode=explode, shadow=True, autopct='%1.2f%%')
        plt.legend(loc="upper right", fontsize=10, bbox_to_anchor=(1.1, 1.05), borderaxespad=0.3)
        plt.title("Pie Chart of Crime Type Ratio")
        plt.savefig(f'static/pie_{number}.jpg')

        #plt.show()
        plt.figure(figsize=[18, 16])
        city_df.Location.value_counts().head(10).plot(kind='bar')
        plt.title("Bar Chart of Crime Location Counts")
        plt.xticks(rotation=45)
        plt.savefig(f'static/location_bar_{number}.jpg')

        #plt.show()
        plt.figure(figsize=[18, 16])
        city_df.groupby('Date').Time.count().plot(kind='line')
        plt.title("Line Chart of Crime Number Trend")
        plt.xticks(rotation=45)
        plt.savefig(f'static/date_trend_{number}.jpg')

        plt.close("all")
        #plt.show()
    # print('Thanks. Bye.')
    return

@app.route('/')
def home():
    return render_template('city.html')



@app.route('/city_1')
def city1():
    city=cities[0]
    city_urls=get_daily(city)
    city_df=specific_daily(city_urls)
    database_create('city_1'+'.sqlite',city_df)
    a=city_df.to_html(escape=False)
    return render_template('city_1.html', a=a)

@app.route('/city_2')
def city2():
    city=cities[1]
    city_urls=get_daily(city)
    city_df=specific_daily(city_urls)
    database_create('city_2'+'.sqlite',city_df)
    a=city_df.to_html(escape=False)
    return render_template('city_2.html', a=a)

@app.route('/city_3')
def city3():
    city=cities[2]
    city_urls=get_daily(city)
    city_df=specific_daily(city_urls)
    database_create('city_3'+'.sqlite',city_df)
    a=city_df.to_html(escape=False)
    return render_template('city_3.html', a=a)

@app.route('/city_4')
def city4():
    city=cities[3]
    city_urls=get_daily(city)
    city_df=specific_daily(city_urls)
    database_create('city_4'+'.sqlite',city_df)
    a=city_df.to_html(escape=False)
    return render_template('city_4.html', a=a)

@app.route('/city_5')
def city5():
    city=cities[4]

    city_urls=get_daily(city)
    city_df=specific_daily(city_urls)
    database_create('city_5'+'.sqlite',city_df)
    print('city 5 finish')

    a=city_df.to_html(escape=False)
    return render_template('city_5.html', a=a)

@app.route('/city_6')
def city6():
    city=cities[5]
    city_urls=get_daily(city)
    city_df=specific_daily(city_urls)
    database_create('city_6'+'.sqlite',city_df)
    a=city_df.to_html(escape=False)
    return render_template('city_6.html', a=a)



if __name__ == '__main__':
    print('starting Flask app', app.name)
    if os.path.exists('static'):
        print('ok')
        pass
    else:
        pwd = os.getcwd()
        os.mkdir(pwd + '\static')
    if os.path.exists('database'):
        print('ok')
        pass
    else:
        pwd = os.getcwd()
        os.mkdir(pwd + '\database')
    interface()
    app.run(debug=True)