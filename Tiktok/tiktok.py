import os
import asyncio
from flask import Flask, render_template, request
from TikTokApi import TikTokApi, exceptions as TikTokExceptions

app = Flask(__name__)
ms_token = os.environ.get("ms_token", None)

@app.route('/', methods=['GET', 'POST'])
async def get_comments():
    comments = []
    hashtag = request.args.get('hashtag', '')  # Mengambil hashtag dari query parameter

    async def fetch_comments(hashtag, comments):
        try:
            async with TikTokApi() as api:
                await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, headless=False)
                videos = api.hashtag(name=hashtag).videos(count=1)
                video = await videos.__anext__()
                count = 0
                async for comment in video.comments(count=30):
                    comments.append(comment.as_dict)
                    count += 1
                    if count == 30:
                        break
        except TikTokExceptions.EmptyResponseException:
            print("TikTok returned an empty response. Please check the hashtag or try again later.")
            # Optionally, return some default data or handle the situation as needed

    # Menjalankan fungsi async menggunakan event loop
    await fetch_comments(hashtag, comments)

    return render_template('comments.html', comments=comments)

if __name__ == '__main__':
    app.run(debug=True)
