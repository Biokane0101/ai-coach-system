import os
import json
import hashlib
import hmac
import base64
import requests
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from coach_brain import CoachResponder, chunk_text

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# アプリパスワード
APP_PASSWORD = "bio2025"

# 有効な学校コード
VALID_SCHOOL_CODES = {
    'TEST2025': 'テスト校',  # テスト用
    # 実際の契約校を追加する場合は以下の形式で追記
    # 'ABC123': '○○中学校',
}

# 学年リスト
GRADE_OPTIONS = ['中1', '中2', '中3', '高1', '高2', '高3', '大1', '大2', '大3', '大4', '社会人']

# 初回アンケートURL（実際のURLに置き換えてください）
INITIAL_SURVEY_URL = "https://forms.gle/r5DFKM79aQrdDuZm9"

# 学年を正規化する関数
def normalize_grade(input_text):
    """様々な学年表記を標準形式に変換"""
    # 全角→半角変換
    text = input_text.replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4')
    text = text.strip()
    
    # パターンマッチング
    grade_patterns = {
        '中1': ['中1', '中１', '中学1年', '中学１年', '中学1年生', '中学１年生', '中学一年', '中一'],
        '中2': ['中2', '中２', '中学2年', '中学２年', '中学2年生', '中学２年生', '中学二年', '中二'],
        '中3': ['中3', '中３', '中学3年', '中学３年', '中学3年生', '中学３年生', '中学三年', '中三'],
        '高1': ['高1', '高１', '高校1年', '高校１年', '高校1年生', '高校１年生', '高校一年', '高一'],
        '高2': ['高2', '高２', '高校2年', '高校２年', '高校2年生', '高校２年生', '高校二年', '高二'],
        '高3': ['高3', '高３', '高校3年', '高校３年', '高校3年生', '高校３年生', '高校三年', '高三'],
        '大1': ['大1', '大１', '大学1年', '大学１年', '大学1年生', '大学１年生', '大学一年', '大一'],
        '大2': ['大2', '大２', '大学2年', '大学２年', '大学2年生', '大学２年生', '大学二年', '大二'],
        '大3': ['大3', '大３', '大学3年', '大学３年', '大学3年生', '大学３年生', '大学三年', '大三'],
        '大4': ['大4', '大４', '大学4年', '大学４年', '大学4年生', '大学４年生', '大学四年', '大四'],
        '社会人': ['社会人', '社会人1年目', '社会人2年目', '社会人3年目', '社会人4年目', '社会人5年目']
    }
    
    # マッチング
    for standard, patterns in grade_patterns.items():
        if text in patterns:
            return standard
    
    return None  # マッチしなかった場合

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
            sheet.update(f'A{row_num}:J{row_num}', [[
                data.get('user_id', ''),
                data.get('school_code', ''),
                data.get('school_name', ''),
                data.get('grade', ''),
                data.get('name', ''),
                data.get('enrollment_year', ''),
                data.get('graduation_year', ''),
                data.get('status', 'active'),
                data.get('progress', 0),
                data.get('last_interaction', '')
            ]])
        else:
            # 新規ユーザー追加
            sheet.append_row([
                data.get('user_id', ''),
                data.get('school_code', ''),
                data.get('school_name', ''),
                data.get('grade', ''),
                data.get('name', ''),
                data.get('enrollment_year', ''),
                data.get('graduation_year', ''),
                data.get('status', 'active'),
                data.get('progress', 0),
                data.get('last_interaction', '')
            ])
        return True
    except Exception as e:
        print(f"データ保存エラー: {e}")
        return False

# 卒業年度計算
def calculate_graduation_year(grade, current_year):
    grade_map = {
        '中1': 3, '中2': 2, '中3': 1,
        '高1': 3, '高2': 2, '高3': 1,
        '大1': 4, '大2': 3, '大3': 2, '大4': 1,
        '社会人': 999  # 卒業なし
    }
    years_left = grade_map.get(grade, 999)
    if years_left == 999:
        return 9999  # 社会人は卒業なし
    return current_year + years_left

# 登録状態の確認
def check_registration_status(user_data):
    if not user_data:
        return 'not_registered'
    if user_data.get('status') == 'graduated':
        return 'graduated'
    if not user_data.get('school_code'):
        return 'incomplete'
    return 'active'

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
        coach = CoachResponder(APP_PASSWORD)
        
        for event in events:
            # 友だち追加イベント
            if event['type'] == 'follow':
                reply_token = event['replyToken']
                user_id = event['source']['userId']
                
                welcome_message = """ご登録ありがとうございます！

まず、学校から配布された登録コードを入力してください。"""
                
                send_line_message(reply_token, welcome_message)
                
                # 仮登録
                save_user_data(user_id, {
                    'user_id': user_id,
                    'status': 'registering',
                    'progress': 0,
                    'last_interaction': str(datetime.now())
                }, worksheet)
                continue
            
            # メッセージイベント
            if event['type'] != 'message' or event['message']['type'] != 'text':
                continue
                
            user_id = event['source']['userId']
            user_message = event['message']['text']
            reply_token = event['replyToken']
            
            # ユーザーデータ取得
            user_data, _ = get_user_data(user_id, worksheet)
            
            # 登録状態確認
            reg_status = check_registration_status(user_data)
            
            # 卒業済みユーザー
            if reg_status == 'graduated':
                response = """申し訳ございません。

ご卒業されたため、サポートを終了させていただいております。

新しい学校でもご利用になりたい場合は、一度ブロックしていただき、新しい登録コードで再度ご登録ください。"""
                send_line_message(reply_token, response)
                continue
            
            # 登録フロー
            if not user_data or reg_status in ['not_registered', 'incomplete']:
                if not user_data:
                    user_data = {
                        'user_id': user_id,
                        'status': 'registering',
                        'progress': 0
                    }
                
                # 学校コード入力待ち
                if not user_data.get('school_code'):
                    code = user_message.strip().upper()
                    if code in VALID_SCHOOL_CODES:
                        user_data['school_code'] = code
                        user_data['school_name'] = VALID_SCHOOL_CODES[code]
                        user_data['enrollment_year'] = datetime.now().year
                        save_user_data(user_id, user_data, worksheet)
                        
                        response = f"""登録コードを確認しました。

次に、学年を教えてください。
以下から選んでください：

{', '.join(GRADE_OPTIONS)}"""
                        send_line_message(reply_token, response)
                    else:
                        response = """無効な登録コードです。

学校の担当者にお問い合わせいただき、正しい登録コードをご確認ください。"""
                        send_line_message(reply_token, response)
                    continue
                
                # 学年入力待ち
                if not user_data.get('grade'):
                    normalized_grade = normalize_grade(user_message)
                    if normalized_grade:
                        user_data['grade'] = normalized_grade
                        user_data['graduation_year'] = calculate_graduation_year(normalized_grade, datetime.now().year)
                        save_user_data(user_id, user_data, worksheet)
                        
                        response = """ありがとうございます。

最後に、名前またはニックネームを教えてください。"""
                        send_line_message(reply_token, response)
                    else:
                        response = f"""正しい学年を選んでください：

{', '.join(GRADE_OPTIONS)}"""
                        send_line_message(reply_token, response)
                    continue
                
                # 名前入力待ち
                if not user_data.get('name'):
                    user_data['name'] = user_message.strip()
                    user_data['status'] = 'active'
                    save_user_data(user_id, user_data, worksheet)
                    
                    response = f"""登録完了しました！

まずは初回アンケートにご協力ください：
{INITIAL_SURVEY_URL}

ご不明な点があれば、いつでもお聞きください。"""
                    send_line_message(reply_token, response)
                    continue
            
            # 通常の会話（登録完了後）
            if reg_status == 'active':
                # AI応答生成
                response = coach.respond(user_message, user_data)
                
                # ユーザーデータ更新
                user_data['progress'] = user_data.get('progress', 0) + 1
                user_data['last_interaction'] = str(datetime.now())
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
