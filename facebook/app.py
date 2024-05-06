from flask import Flask, render_template, request
import instaloader
import os
import re
import time

app = Flask(__name__)

def save_instagram_session(username, password):
    L = instaloader.Instaloader()
    L.login(username, password)  # Login to Instagram
    L.save_session_to_file(f'{username}_session')  # Save the session file

def load_instagram_session(username):
    session_file = f'{username}_session'
    if os.path.exists(session_file):
        return session_file
    return None

def scrape_comments(username, post_url, password):
    loader = instaloader.Instaloader()
    session_file = load_instagram_session(username)

    if session_file:
        loader.load_session_from_file(username, session_file)
    else:
        save_instagram_session(username, password)
        session_file = load_instagram_session(username)
        if not session_file:
            return "Error: Unable to create or load session."

    post_shortcode = extract_shortcode(post_url)
    if not post_shortcode:
        return "Invalid URL or shortcode."

    try:
        post = instaloader.Post.from_shortcode(loader.context, post_shortcode)
        comments = post.get_comments()
        comment_list = [comment.text for comment in comments]
        return comment_list
    except instaloader.exceptions.InstaloaderException as e:
        if "401" in str(e):
            os.remove(session_file)
            return "Session expired. Please try again."
        elif "429" in str(e):
            time.sleep(60)  # Sleep for a minute and retry
            return scrape_comments(username, post_url, password)
        else:
            return f"Error fetching post data: {e}"

def extract_shortcode(url):
    match = re.search(r'/p/([^/]+)/', url)
    return match.group(1) if match else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    if 'username' not in request.form or 'password' not in request.form or 'post_url' not in request.form:
        return "Missing form data: username, password, or post URL.", 400
    username = request.form['username']
    password = request.form['password']
    post_url = request.form['post_url']
    comments = scrape_comments(username, post_url, password)
    return render_template('result.html', comments=comments)

if __name__ == '__main__':
    app.run(debug=True)
