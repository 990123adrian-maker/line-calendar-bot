import os
import json
import datetime
from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

app = Flask(__name__)
app.secret_key = os.urandom(24)

db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class UserToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    line_userid = db.Column(db.String(100), unique=True, nullable=False)
    token_json = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))
SCOPES = ['https://www.googleapis.com/auth/calendar']

@app.route("/login")
def login():
    line_id = request.args.get('uid')
    flow = Flow.from_client_secrets_file(
        'client_secret.json', scopes=SCOPES,
        redirect_uri=request.host_url.strip('/') + '/google/callback'
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    session['temp_line_id'] = line_id
    return redirect(auth_url)

@app.route("/google/callback")
def google_callback():
    flow = Flow.from_client_secrets_file('client_secret.json', scopes=SCOPES, 
                                         redirect_uri=request.host_url.strip('/') + '/google/callback')
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    
    line_id = session.get('temp_line_id')
    if line_id:
        user = UserToken.query.filter_by(line_userid=line_id).first()
        if user:
            user.token_json = creds.to_json()
        else:
            new_user = UserToken(line_userid=line_id, token_json=creds.to_json())
            db.session.add(new_user)
        db.session.commit()
        return "<h1>✅ 綁定成功！</h1><p>現在可以回到 LINE 傳送行程了。</p>"
    return "❌ 錯誤：找不到您的 LINE ID，請重新從 LINE 點擊連結。"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    msg = event.message.text
    
    user = UserToken.query.filter_by(line_userid=user_id).first()
    if not user:
        login_url = f"{request.host_url.strip('/')}/login?uid={user_id}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"請先點我登入 Google 帳號以啟用日曆功能：\n{login_url}"))
        return

    if "標題：" in msg:
        try:
            lines = msg.split('\n')
            data = {}
            for line in lines:
                if '標題：' in line: data['title'] = line.replace('標題：', '').strip()
                if '開始：' in line: data['start'] = line.replace('開始：', '').strip()
                if '結束：' in line: data['end'] = line.replace('結束：', '').strip()

            creds = Credentials.from_authorized_user_info(json.loads(user.token_json), SCOPES)
            service = build("calendar", "v3", credentials=creds)

            event_body = {
                'summary': data.get('title', '無標題'),
                'start': {'dateTime': data.get('start'), 'timeZone': 'Asia/Taipei'},
                'end': {'dateTime': data.get('end'), 'timeZone': 'Asia/Taipei'},
            }
            service.events().insert(calendarId='primary', body=event_body).execute()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已成功加入您的 Google 日曆！"))
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"❌ 發生錯誤：{e}"))

if __name__ == "__main__":
    app.run()
