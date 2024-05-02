from flask import Flask, render_template, request
from twikit import Client
from bs4 import BeautifulSoup
import json
import csv
import requests

app = Flask(__name__)

# Load Twitter credentials from JSON file
with open('creds.json', 'r') as file:
    data = json.load(file)

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        keyword = request.form['keyword']
        client = Client('en-US')
        client.login(auth_info_1=data['username'], password=data['password'])
        
        twit = []
        tweets = client.search_tweet(query=keyword, product='Latest')[:200]
        
        for tweet in tweets:
            _media = []
            _link = []
            content = tweet.full_text
            _id = tweet.id
            url = tweet.urls
            
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
    
            _temp = [_id, content, url, _media]
            twit.append(_temp)
        
        csv_file_path = 'data.csv'
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['ID', 'Text', 'URL', 'Media'])
            writer.writerows(twit)
        
        client.logout()
        return render_template('index.html', twit=twit)
    else:
        return render_template('index.html', twit=None)

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

if __name__ == '__main__':
    app.run(debug=True)