import os
import json
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from calendar_service import add_event 

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/callback", method=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_token = event.reply_token
    user_text = event.message.text
    
    try:
        lines = user_text.split('\n')
        data = {}
        for line in lines:
            if '標題：' in line:
                data['title'] = line.replace('標題：', '').strip()
            if '開始：' in line:
                data['start'] = line.replace('開始：', '').strip()
            if '結束：' in line:
                data['end'] = line.replace('結束：', '').strip()
                
        if not all(key in data for key in ['title', 'start', 'end']):
            return

        add_event(data)
        
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f"✅ 已成功加入日曆：\n{data['title']}")
        )

    except Exception as e:
        error_msg = f"❌ 發生錯誤：{str(e)}"
        print(error_msg) 
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=error_msg)
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
