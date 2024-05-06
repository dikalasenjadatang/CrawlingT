from flask import Flask, render_template, request, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import instaloader
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_code_here'

def scrape_comments(username, password, target_post_url):
    L = instaloader.Instaloader()
    L.login(username, password)
    post_id = instaloader.Post.from_shortcode(L.context, target_post_url.split('/')[-2]).shortcode
    post = instaloader.Post.from_shortcode(L.context, post_id)
    comments = post.get_comments()
    result = []
    for comment in comments:
        profile_pic_url = comment.owner.profile_pic_url  # URL foto profil
        likes_count = comment.likes_count  # Jumlah like pada komentar
        created_at_utc = comment.created_at_utc  # Waktu komentar dalam UTC
        result.append({
            'username': comment.owner.username,
            'text': comment.text,
            'profile_pic_url': profile_pic_url,
            'likes_count': likes_count,
            'created_at_utc': created_at_utc.isoformat()  # Format waktu ke ISO 8601
        })
    return result

def RateController(max_requests_per_minute):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            if elapsed_time < 60.0 / max_requests_per_minute:
                time.sleep((60.0 / max_requests_per_minute) - elapsed_time)
            return result
        return wrapper
    return decorator

class CommentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    post_url = StringField('Post URL', validators=[DataRequired()])
    submit = SubmitField('Scrape Comments')

def load_session():
    if 'username' in session:
        return session['username'], session['password']
    return None, None

def save_session(username, password):
    session['username'] = username
    session['password'] = password

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CommentForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        target_post_url = form.post_url.data
        save_session(username, password)  # Save session data
        scraped_comments = scrape_comments(username, password, target_post_url)
        return render_template('comments.html', comments=scraped_comments)
    # Load session data
    username, password = load_session()
    form.username.data = username
    form.password.data = password
    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
