import os
import json
import hashlib
import hmac
import base64
import requests
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
from coach_brain import CoachResponder, chunk_text

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Google Sheets設定
def setup_google_sheets():
    try:
        credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)
        gc = gspread.authorize(credentials)
        return gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        print(f"Google Sheets設定エラー: {e}")
        return None

# LINE署名検証
def verify_line_signature(body, signature):
    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    return hmac.compare_digest(
        signature,
        base64.b64encode(hash).decode('utf-8')
    )

# LINEメッセージ送信
def send_line_message(reply_token, message):
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    # メッセージが長い場合は分割
    message_chunks = chunk_text(message, 2000)
    messages = []
    
    for chunk in message_chunks:
        messages.append({
            'type': 'text',
            'text': chunk
        })
    
    data = {
        'replyToken': reply_token,
        'messages': messages[:5]  # LINEの制限：最大5つまで
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200

# ユーザーデータ管理
def get_user_data(user_id, sheet):
    try:
        records = sheet.get_all_records()
        for row_num, record in enumerate(records, start=2):
            if record.get('user_id') == user_id:
                return record, row_num
        return None, None
    except:
        return None, None

def save_user_data(user_id, data, sheet):
    try:
        user_data, row_num = get_user_data(user_id, sheet)
        if user_data:
            # 既存ユーザー更新
            col = 2  # B列から開始
            for key, value in data.items():
                if key != 'user_id':
                    sheet.update_cell(row_num, col, str(value))
                    col += 1
        else:
            # 新規ユーザー追加
            row_data = [user_id] + list(data.values())[1:]  # user_id除く
            sheet.append_row(row_data)
        return True
    except Exception as e:
        print(f"データ保存エラー: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def callback():
    # 署名検証
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    
    if not verify_line_signature(body.encode('utf-8'), signature):
        return jsonify({'error': 'Invalid signature'}), 400
    
    try:
        events = json.loads(body)['events']
        sheet = setup_google_sheets()
        if not sheet:
            return jsonify({'error': 'Sheet connection failed'}), 500
        
        worksheet = sheet.worksheet('ユーザーデータ')
        coach = CoachResponder()  # CoachResponderクラスを使用
        
        for event in events:
            if event['type'] != 'message' or event['message']['type'] != 'text':
                continue
                
            user_id = event['source']['userId']
            user_message = event['message']['text']
            reply_token = event['replyToken']
            
            # ユーザーデータ取得
            user_data, _ = get_user_data(user_id, worksheet)
            if not user_data:
                user_data = {
                    'user_id': user_id,
                    'level': 'beginner',
                    'goal': '',
                    'progress': 0,
                    'last_interaction': '',
                    'graduation_ready': False
                }
            
            # AI応答生成（CoachResponder.respondメソッド使用）
            response = coach.respond(user_message, user_data)
            
            # ユーザーデータ更新（簡単な進捗管理）
            user_data['progress'] = user_data.get('progress', 0) + 1
            user_data['last_interaction'] = str(datetime.now())
            
            # データ保存
            save_user_data(user_id, user_data, worksheet)
            
            # 応答送信
            send_line_message(reply_token, response)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook処理エラー: {e}")
        return jsonify({'error': 'Processing failed'}), 500

@app.route('/')
def home():
    return "AI Coach System - Running"

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
