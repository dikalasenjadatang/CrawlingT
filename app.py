from flask import Flask, render_template, request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from textblob import TextBlob
from flask import jsonify
import time
from twikit import Client
from bs4 import BeautifulSoup
import json
import csv
import requests

app = Flask(__name__)

# Load Twitter credentials from JSON file
with open('creds.json', 'r') as file:
    data = json.load(file)

# YouTube API
youtube = build('youtube', 'v3', developerKey='developer_api_youtube')

# Function to get free proxies
def get_free_proxies():
    url = 'https://www.proxysite.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    proxies = []
    for row in soup.find_all('tr')[1:]:
        data = row.find_all('td')
        proxy = {
            'ip': data[0].text,
            'port': data[1].text,
            'country': data[3].text,
            'https': data[6].text
        }
        proxies.append(proxy)
    return proxies

@app.route('/api/youtube/comments', methods=['POST'])
def youtube_comments():
    data = request.get_json()  # Mengambil data JSON dari request
    if 'hashtag' in data:
        hashtag = data['hashtag']
        search_response = youtube.search().list(
            q=hashtag,
            part='snippet',
            type='video',
            maxResults=60  # You can adjust the number of results
        ).execute()

        videos = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            video_title = item['snippet']['title']
            videos.append({'video_id': video_id, 'title': video_title})

        comments = []
        for video in videos:
            request_comments = youtube.commentThreads().list(
                part='snippet',
                videoId=video['video_id'],
                textFormat='plainText'
            ).execute()

            for item in request_comments.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                author_profile_image = comment['authorProfileImageUrl']
                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'published_at': comment['publishedAt'],
                    'likes': comment['likeCount'],
                    'profile_image': author_profile_image,
                    'video_title': video['title']
                })
        return jsonify(comments)
    else:
        return jsonify({'error': 'Hashtag is required'}), 400

# Route for handling different requests
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'hashtag' in request.form:  # YouTube Comments by Hashtag
            hashtag = request.form['hashtag']
            search_response = youtube.search().list(
                q=hashtag,
                part='snippet',
                type='video',
                maxResults=10  # You can adjust the number of results
            ).execute()

            videos = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                videos.append({'video_id': video_id, 'title': video_title})

            comments = []
            for video in videos:
                request_comments = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video['video_id'],
                    textFormat='plainText'
                ).execute()

                for item in request_comments.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    author_profile_image = comment['authorProfileImageUrl']
                    comments.append({
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'published_at': comment['publishedAt'],
                        'likes': comment['likeCount'],
                        'profile_image': author_profile_image,
                        'video_title': video['title']
                    })
            return render_template('youtube_results.html', video_info=comments)

        elif 'keyword' in request.form:  # Twitter Scraper
            keyword = request.form['keyword']
            client = Client('en-US')
            client.login(auth_info_1=data['username'], password=data['password'])
            
            twit = []
            tweets = client.search_tweet(query=keyword, product='Latest')[:200]
            
            for tweet in tweets:
                if tweet.user.followers_count < 5:  # Check if followers less than 5
                    continue  # Skip this tweet
                
                _media = []
                _link = []
                content = tweet.full_text
                _id = tweet.id
                url = tweet.urls
                created_at = tweet.created_at
                
                if tweet.urls:
                    for link in tweet.urls:
                        _link.append(link)
                
                if tweet.media:
                    for i, media in enumerate(tweet.media):
                        media_url = media.get('media_url_https')
                        extension = media_url.rsplit('.', 1)[-1]
                        
                        response = client.get_media(media_url)
                        with open(f'media_download/media{tweet.id}_{i}.{extension}', 'wb') as fs:
                            fs.write(response)
                        
                        _media.append(media_url)
            
                _temp = [_id, content, url, _media, created_at]
                twit.append(_temp)
            
            csv_file_path = 'twitter_data.csv'
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['ID', 'Text', 'URL', 'Media', 'Created At'])
                writer.writerows(twit)
            
            client.logout()
            return render_template('twitter_results.html', twit=twit)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
