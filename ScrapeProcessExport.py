#!/usr/bin/env python2.7

# Don't forget to install all these libraries on the server
import json
import time
import threading
import pandas as pd
import numpy as np
import math
import sys

from datetime import datetime
from twython import Twython

# Imports the keys from the python file
# You must have your own twitter API keys for this to work
from twitter_key import t_key, t_secret
APP_KEY = t_key
APP_SECRET = t_secret

twitter = Twython(APP_KEY, APP_SECRET)

# Now we import the location and category files
category_list = pd.read_csv('/home/mamap_source/tweet_categories.csv')
location_list = pd.read_csv('/home/mamap_source/landmark_locations.csv')


# clear out any NaNs, and any extra whitespace
location_list.fillna('no_data', inplace=True)
category_list.fillna('no_data', inplace=True)
space_remover = lambda x: x.strip()
location_list['Landmark'].apply(space_remover)
category_list['Word'].apply(space_remover)

# This looks up the previously grabbed file, to get the ID of the last collected tweet
def get_last_tweet():
    last_batch = pd.read_csv('/home/mamap_source/scraped_tweets.csv')
    id_list = last_batch['tweet_id'].tolist()
    result = max(id_list)
    return long(result)

last_grabbed_tweet = get_last_tweet()

def grab_tweets():
    results = twitter.get_user_timeline(screen_name='@ma3route', since_id=last_grabbed_tweet, count=200)
    return results

def grab_many_tweets():
    all_tweets = {}
    total_time = 60
    remaining_seconds = total_time
    interval = 30
    
    while remaining_seconds > 0:
        added = 0
        new_tweets = grab_tweets()
        for tweet in new_tweets:
            tid = tweet['id_str']
            if tid not in all_tweets:
                properties = {}
                try:
                    properties['lat'] = tweet['coordinates']['coordinates'][0]
                    properties['lon'] = tweet['coordinates']['coordinates'][1]
                except TypeError:
                    properties['lat'] = 0
                    properties['lon'] = 0
                properties['tweet_id'] = tid
                properties['content'] = tweet['text']
                properties['user'] = tweet['user']['id']
                properties['user_location'] = tweet['user']['location']
                properties['time'] = tweet['created_at']
                all_tweets[ tid ] = properties
                added += 1
        print "At %d seconds, added %d new tweets, for a total of %d" % ( total_time - remaining_seconds, added, len( all_tweets ) )
        time.sleep(interval)
        remaining_seconds -= interval
        # if no new tweets, don't bother following through with the rest of the code
        return all_tweets



def scrape_to_dataframe():
    g = grab_many_tweets()
    df = pd.DataFrame.from_dict(g, orient='index')
    df.reset_index(inplace=True, drop=True)
    return df

# These functions change the date to a format required by the database. Note the default timezone is GMT
# Customize this depending on your DB's needs
def time_converter(input_string):
    orig_date = input_string[:-10] + input_string[-4:]
    convert = time.strptime(orig_date, '%a %b %d %H:%M:%S %Y')
    new_date = time.strftime("%Y-%m-%d %H:%M:%S",convert)
    return new_date

def fix_times(df):
    df['timestamp']=''
    for row in df.itertuples():
        idx = int(row[0])
        new_time = time_converter(df.loc[idx,'time'])
        df.loc[idx,'timestamp'] = new_time
    df.drop('time',axis=1, inplace=True)

# This function goes through each entry in location_list and looks for it in the passed string
# When it finds a match, it returns the associated lat-long. It ignores case.

def check_landmark(test_string):
    result = {'lat':'0','lon':'0'}
    for landmark in location_list.itertuples():
        if str(landmark[1]).lower() in test_string.lower():
            result = {'lat':landmark[4],'lon':landmark[5]}
#             print str(i) + "_" + str(landmark[1]) + "_" + str(landmark[0])
    return result


def fill_in_locations(df):
    for row in df.itertuples():
        idx = row[0]
        location = check_landmark(df.loc[idx,'content'])
        latitude = location['lat']
        longitude = location['lon']
        if (df.loc[idx,'lat']==0 or df.loc[idx,'lon']==0):
            df.loc[idx,'lat'] = latitude
            df.loc[idx,'lon'] = longitude

# This function goes through each entry in category_list and looks for it in the passed string
# When it finds a match, it returns the associated category name. It ignores case.

def check_category(test_string):
    result = 'NONE'
    for keyword in category_list.itertuples():
        if str(keyword[1]).lower() in test_string.lower():
            result = keyword[2]
    return result


def fill_in_categories(df):
    for row in df.itertuples():
        idx = row[0]
        category = check_category(row[3])
        if df.loc[idx,'category']=='NONE':
            df.loc[idx,'category'] = category

# This adds a column required by the geodatabase
def insert_geom(df):
    df.insert(0,'geom',"")
    for row in df.itertuples():
        idx = row[0]
        df.loc[idx,'geom'] = "SRID=4326;POINT(" + str(df.loc[idx,'lon']) + " " + str(df.loc[idx,'lat']) + ")"

# This function takes all the other functions and runs them in order.
def make_it_happen():
    # API occasionally returns an error, killing the script, so use try/except to make it keep trying
    counter = 1
    while counter > 0:
        try:
            tweet_list = scrape_to_dataframe()
        except:
            pass
        else:
            if len(tweet_list)==0:
                sys.exit("no new tweets, goodbye")
            else: 
                fix_times(tweet_list)
                tweet_list = tweet_list[['tweet_id', 'timestamp', 'content', 'lat', 'lon']]
                tweet_list['category'] = 'NONE'
                fill_in_locations(tweet_list)
                fill_in_categories(tweet_list)
                insert_geom(tweet_list)
                tweet_list.to_csv('/home/mamap_source/scraped_tweets.csv', index=False, encoding='utf-8')
                counter -= 1

make_it_happen()

#Insert Tweets

import psycopg2

tweet_file = open ("/home/mamap_source/scraped_tweets.csv") ##to put into proper place

SQL_STATEMENT = """
    COPY %s FROM STDIN WITH
        CSV
        HEADER
        DELIMITER AS ','
    """

def process_file(conn, table_name, file_object):
    cursor = conn.cursor()
    cursor.copy_expert(sql=SQL_STATEMENT % table_name, file=file_object)
    conn.commit()
    cursor.close()
  
from postgresqlkey import pgsqlhost, pgsqldatabase, pgsqluser, pgsqlpassword 

host = pgsqlhost
database = pgsqldatabase 
user = pgsqluser 
password = pgsqlpassword

db = psycopg2.connect(host=host,
                      database=database,
                      user=user,
                      password=password)  
cursor = db.cursor()
try:
    process_file(db, 'database_name', tweet_file)
finally:
    db.close()    