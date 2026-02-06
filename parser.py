import re

def parse_event(text):
    try:
        summary = re.search(r"標題[:：]\s*(.*)", text)
        start_time = re.search(r"開始[:：]\s*(.*)", text)
        end_time = re.search(r"結束[:：]\s*(.*)", text)

        if summary and start_time and end_time:
            event_data = {
                'summary': summary.group(1).strip(),
                'start_time': start_time.group(1).strip(),
                'end_time': end_time.group(1).strip()
            }
            return event_data
        return None
    except Exception as e:
        print(f"解析錯誤: {e}")
        return None
