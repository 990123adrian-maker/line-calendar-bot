from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from parser import parse_event
from calendar_service import add_event

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "4mIAFJbMr129dIk1kbwLT/qY3bQJmgH9j3ihzYy/MWs5lb+Q00IQzqJzibckwOfxrKXC6V1br1YmhbBnEIx58Xrk2fUTy0uo0Jaf9SZdcWdRqjHvNIuQRjeLudF3OLWmdjNfK87apJd3ylEHYmtesQdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "88dbb9da634f6828029c7bf2db5188fd"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    if not text.startswith("標題:"):
        return

    try:
        event_data = parse_event(text)
        add_event(event_data)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("✅ 活動已加入 Google Calendar")
        )
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(f"❌ 失敗：{e}")
        )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)