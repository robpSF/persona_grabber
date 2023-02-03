#  No changes made yet :) Same as the first version of file with similar name
# This program imports a list of Twitter handles and returns a CSV with all their details
# INPUT: CSV file with simple list of twitter handlesinstalinstal
# OUTPUT: Three Excel files
# - the normal sheet of friends, followers, GPS etc.
# - a table of "_FOLLOWERS" which is all the followers
# - a table of "_MENTIONED" which are the
# https://www.geeksforgeeks.org/python-user-object-in-tweepy/

# 16 Aug 2022
# Added image capture on historic tweet


# importing libraries
# SL_GET_TwitterProfileDetails_XLSV2.py
import tweepy
import time
import pandas as pd
import streamlit as sl
import requests
import numpy as np
# import datetime
import re
import re
from io import BytesIO
#import pyxlsb
#from pyxlsb import open_workbook as open_xlsb
import streamlit as st

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data

import datetime
from datetime import timezone
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="robsapp")

import sys


def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


# this is for Tweepy. It's not needed for GoT3-----------------


# paste in your keys from your Twitter Dev account
consumer_key = sl.secrets["consumer_key"]
consumer_secret = sl.secrets["consumer_secret"]
access_token = sl.secrets["access_token"]
access_token_secret = sl.secrets["access_token_secret"]
password = sl.secrets["password"]
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)
# ----- ok that's Tweepy all setup --------------------------

if password != sl.text_input("Enter password"): exit(600)

def open_csv_file(filename):
    with open(filename, encoding='utf-8') as fp:
        writer = csv.writer(fp)
        reader = csv.DictReader(fp)
        data = [r for r in reader]
    return data

def search_for_tweet(search):
    tweets = api.search(q=search, lang="en")
    sl.write(tweets)
    return


def get_followers(user_name):
    """
    get a list of all followers of a twitter account
    :param user_name: twitter username without '@' symbol
    :return: list of usernames without '@' symbol
    """
    followers = []
    for page in tweepy.Cursor(api.followers, screen_name=user_name, wait_on_rate_limit=True, count=200).pages():
        try:
            followers.extend(page)
        except tweepy.TweepError as e:
            print("Going to sleep:", e)
            time.sleep(60)
    return followers


def get_following(user_name):
    """
    get a list of all following of a twitter account
    :param user_name: twitter username without '@' symbol
    :return: list of usernames without '@' symbol
    """
    following = []
    page_count = 0
    for page in tweepy.Cursor(api.friends, screen_name=user_name, wait_on_rate_limit=True, count=200).pages():
        # add some arbitary limit to number of friends we're getting.
        try:
            following.extend(page)
            page_count = page_count + 1
        except tweepy.TweepError as e:
            sl.write("Going to sleep:", e)
            time.sleep(60)

            friends_list = []
            for friend in following:
                friends_list.append(friend.screen_name)
            return following, friends_list


def get_friends(user_name):
    following = []
    page = api.friends(user_name, count=200)
    following.extend(page)

    friends_list = []
    for friend in following:
        friends_list.append(friend.screen_name)
    return following, friends_list


def reject_outliers(data, m):
    # one approach
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / mdev if mdev else 0.
    data_return = data[s < m]
    return data_return


def reject_outliers2(data):
    # convert list to dataframe
    df = pd.DataFrame({"data": data})
    Q1 = df.quantile(0.15)
    Q3 = df.quantile(0.98)
    IQR = Q3 - Q1
    df = df[~((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).any(axis=1)]

    # convert dataframe to array for numpy
    return_data = df.to_numpy()
    return return_data


def get_mentions(tweet):
    mentions = []
    # sl.write(tweet)
    i = tweet.find(" @", 0)
    while i > 0:
        space = tweet.find(" ", i + 1)
        # sl.write("space,i :"+str(space)+","+str(i))
        mention = tweet[i + 2:space]
        if mention[-1:] == ":":
            mention = mention[:-1]
        elif mention[-1:] == ".":
            mention = mention[:-1]
        elif mention[-1:] == ",":
            mention = mention[:-1]
        elif mention[-1:] == "…":
            mention = mention[:-1]
        elif mention[-2:] == "'s":
            mention = mention[:-2]
        # sl.write(mention)
        mentions.append(mention)
        i = tweet.find(" @", space)
    # sl.write(mentions)
    return mentions


def get_range(my_list):
    # reject outliers
    # version 1: rt_array = reject_outliers(np.array(my_list),50)
    rt_array = reject_outliers2(my_list)
    # sl.write(rt_array)
    low = np.min(rt_array)
    high = np.max(rt_array)
    rt_avg = np.average(rt_array)
    rt_std = np.std(rt_array)
    # sl.write(rt_avg,rt_std)
    # rt_std = rt_std*1.5
    low = round((rt_std * 1.5) - rt_avg)
    # high = round(rt_avg+rt_std)
    return low, high


def chart_mentions(other_users_mentioned):
    # sl.write(other_users_mentioned)
    mentions_as_array = np.array(other_users_mentioned)
    unique, count = np.unique(mentions_as_array, return_counts=True)
    # sl.write(unique)
    # sl.write(count)
    mentions_df = pd.DataFrame({"mentions": unique, "count": count}).set_index("mentions")
    mentions_df = mentions_df.sort_values(by=["count"], ascending=False)
    # sl.table(mentions_df)
    sl.bar_chart(mentions_df)
    return mentions_df


def get_likes_and_retweets(screen_name):
    tweets = api.user_timeline(screen_name=screen_name, count=100)
    retweets = []
    likes = []
    other_users_mentioned = []
    # sl.write("Retweets")
    for tweet in tweets:
        other_users_mentioned = other_users_mentioned + get_mentions(tweet.text)
        # sl.write(tweet.retweet_count)
        retweets.append(tweet.retweet_count)
    # sl.write("Likes")
    for tweet in tweets:
        # sl.write(tweet.favorite_count)
        likes.append(tweet.favorite_count)

    # chart_mentions(other_users_mentioned)

    # sl.write(retweets)
    # sl.write(likes)
    sl.sidebar.text(screen_name)
    sl.sidebar.text("getting likes")
    TwLikeLo, TwLikeHi = get_range(likes)
    sl.sidebar.text("getting retweets")
    TwShareLo, TwShareHi = get_range(retweets)
    return TwLikeLo, TwLikeHi, TwShareLo, TwShareHi, other_users_mentioned


# sl.write(profiles)
other_users_mentioned = []
massive_friends_list = []
verbose = False
basic_table = sl.sidebar.checkbox("Basic table", value=True)
grab_url = sl.sidebar.checkbox("Grab URL", value=False)

highest_num = 0
tweet_list = {}


def historical(username):  # get historical retweets and tweets
    hold_string = ""
    limit = 10
    tweets = tweepy.Cursor(api.user_timeline, screen_name=username, limit=limit, tweet_mode='extended', ).items(limit)
    for tweet in tweets:

        #------------------------
        try:
            sl.write(tweet.entities)
            if 'media' in tweet.entities:
                file_location = str(tweet.entities['media'][0]['media_url'])
                sl.subheader("Insider!")
                sl.write(file_location)
                sl.image(file_location)
                #if show_results: sl.image(file_location)
                #video_info = tweet.entities["media"][0]["expanded_url"]

                #this is a horrible workaround to get the video url into the tweet somehow.
                #it's added as a Subject
                #if video_info.find("video") > 0:
                #    sl.write(video_info)
                #    subject = video_info

            else:
                file_location = ""
        except:
            file_location=""

        if file_location!="":
            sl.subheader("Outsider!")
            sl.write(file_location)
            sl.image(file_location)

        #--------------------


        if hasattr(tweet, "retweeted_status"):
            tweetStr = '"RT @' + tweet.retweeted_status.user.screen_name + '  : ' + tweet.retweeted_status.full_text + '","'+file_location +'","' + tweet.created_at.strftime("%Y-%m-%d %H:%M:%S") + '"' + chr(10) # comment this out and fix the indentation to get rid of retweets
        else:
            tweetStr = '"' + tweet.full_text + '","'+file_location +'","' + tweet.created_at.strftime("%Y-%m-%d %H:%M:%S") + '"' + chr(10)
            sl.write(tweetStr)
        tweetStr = re.sub(r'https://t.co/\w{10}', '', tweetStr, flags=re.MULTILINE)
        hold_string = hold_string + tweetStr
    return hold_string


data = []

# This opens the Excel file and fills in the blanks

#path = sl.text_input(label="Path", value="C:/Users/rober_vsah/downloads/")
#filename = sl.text_input(label="CSV filename", value="input") + ".csv"
filename = sl.file_uploader("drop CSV with twitter handles here")

if filename!=None:
    # Read the excel file into a pandas DataFrame
    df = pd.read_excel(filename)

    # Convert the "username" column to a list
    profiles = df["username"].tolist()



    # big loop

    for username in profiles:
        sl.write("checkin' " + username)

        if not basic_table:
            following, new_friends = get_friends(username)
            if not verbose:
                sl.write(new_friends)
                massive_friends_list = massive_friends_list + new_friends

        try:
            # user = api.get_user(username)
            user = api.get_user(screen_name=username)
            # created = user.created_at.tz_localize(None)
            # created = user.created_at.tz_localize(None)
            # dt = user.created_at.tz.replace(tzinfo=None)

            date_created = user.created_at
            created = date_created.replace(tzinfo=None)
            # dt = user.created_at.tz.replace(tzinfo=None)
            # df['Created'].dt.tz_localize(None)
            if user.url != None:
                sl.write(username + "  " + user.url)
            try:
                if grab_url:
                    sl.sidebar.text("grabbing URL")
                    r = requests.get(user.url)
                    display_url = """%s""" % r.url
                else:
                    display_url = ""
                # display_url = ""
                # print("""%s""" % r.url)
            except:
                display_url = ""
                sl.write("issue 5")
            try:
                sl.sidebar.text("grabbing location")
                location = geolocator.geocode(user.location)
                gps = str(location.latitude) + "," + str(location.longitude)
            except:
                gps = ""
                sl.write("issue 4")

            try:
                profile_url = user.profile_image_url.replace("_normal", "")
            except:
                profile_url = ""
                sl.write("issue 3")
            # try:
            # except Exception as e:
            #     sl.write(e)
            try:
                banner_url = user.profile_banner_url
            except:
                banner_url = ""
                sl.write("issue 2")
            try:
                TwLikeLo, TwLikeHi, TwShareLo, TwShareHi, these_mentions = get_likes_and_retweets(username)
                other_users_mentioned = other_users_mentioned + these_mentions
            except:
                sl.write("Problem getting timeline for " + username)
                do_nothing = True
                sl.write("issue 1")

            row = [user.name, username, "", 0, "", 0, "", user.description, "", profile_url, user.name, username,
                   user.verified, created, user.description, profile_url, banner_url,
                   user.followers_count, user.friends_count, user.statuses_count, historical(username), "",
                   "", "", TwLikeLo,
                   TwLikeHi, TwShareLo, TwShareHi, user.location, gps, display_url]
            data.append(row)

        except Exception as e:
            do_nothing = True
            sl.write(e)

    columns = ["Name", "Handle", "Faction", "Disposition", "Tags", "RP", "Email", "Bio", "Goals", "Image", "TwName",
               "TwHandle", "TwVerified", "TwCreated", "TwBio", "TwProfileImg", "TwBgImg", "TwFollowers",
               "TwFollowing", "TwPosts", "TwHistory", "TwWebsite", "TwCmtLo", "TwCmtHi", "TwLikeLo", "TwLikeHi",
               "TwShareLo", "TwShareHi", "Location", "GPS", "URL"]





    sl.write("ava's function running")
    sl.write("getting tweets from last 7 days")
    sl.write(data)

    sl.write(highest_num)
    sl.write(columns)

    # write the twitter details
    df = pd.DataFrame(data, columns=columns)

    sl.text(df)
    # df.to_excel(path+savetofilename+".xlsx")
    #df.to_excel(path+"new.xlsx", index=False)
    df_xlsx = to_excel(df)
    st.download_button(label='📥 Download PERSONAS Result',
                       data=df_xlsx,
                       file_name='personas.xlsx')

    sl.write("Twitter persona details XLS file saved, open your new excel sheet to see the results.")

    if not basic_table:
        sl.header("Next level analysis")
        sl.write("This analysis looks at who the imported accounts are mentioning and who they are following")
        sl.write("This is a count of other Twitter accounts MENTIONED by the imported account list ")
        new_personas_df = chart_mentions(other_users_mentioned)
        sl.write("These are all the accounts being FOLLOWED by our imported list")
        loadsa_friends_df = chart_mentions(massive_friends_list)

        # now write the additional twitter accounts
      
        df_xlsx = to_excel(new_personas_df)
        st.download_button(label='📥 Download MENTIONED Result',
                       data=df_xlsx,
                       file_name='MENTIONED.xlsx')
        
        df_xlsx = to_excel(loadsa_friends_df)
        st.download_button(label='📥 Download FRIENDS Result',
                       data=df_xlsx,
                       file_name='FRIENDS.xlsx')
