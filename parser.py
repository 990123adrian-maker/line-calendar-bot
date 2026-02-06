import re
from datetime import datetime


def parse_event(text):
    title = re.search(r"標題：(.*)", text)
    start = re.search(r"開始：(.*)", text)
    end = re.search(r"結束：(.*)", text)

    if not (title and start and end):
        raise ValueError("活動格式錯誤")

    return {
        "title": title.group(1).strip(),
        "start": datetime.strptime(start.group(1).strip(), "%Y-%m-%d %H:%M"),
        "end": datetime.strptime(end.group(1).strip(), "%Y-%m-%d %H:%M"),
    }
