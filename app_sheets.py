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

# 初回アンケートURL（ベースURL）
INITIAL_SURVEY_BASE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdTTcEQr8irSOVUKs__0CAPyBDBEQbJt2p4_V6x33aMukeqSg/viewform"
INITIAL_SURVEY_ENTRY_ID = "entry.1948261894"

def get_survey_url_with_user_id(user_id):
    """LINE IDを埋め込んだアンケートURLを生成"""
    return f"{INITIAL_SURVEY_BASE_URL}?usp=pp_url&{INITIAL_SURVEY_ENTRY_ID}={user_id}"

# 効果測定用アンケートURL（ベースURL）
FOLLOWUP_SURVEY_BASE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc50ciUyIkxiGR7gX2nUq28Pk4WGhNRM8elGCziPvo20EcH8A/viewform"
FOLLOWUP_SURVEY_ENTRY_ID = "entry.1458350498"

def get_followup_survey_url_with_user_id(user_id):
    """LINE IDを埋め込んだ効果測定アンケートURLを生成"""
    return f"{FOLLOWUP_SURVEY_BASE_URL}?usp=pp_url&{FOLLOWUP_SURVEY_ENTRY_ID}={user_id}"

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
        'messages': messages[:5]
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
            sheet.update(f'A{row_num}:I{row_num}', [[
                data.get('user_id', ''),
                data.get('name', ''),
                data.get('registration_date', ''),
                data.get('concern_target', ''),
                data.get('target_detail', ''),
                data.get('concern_description', ''),
                data.get('concern_duration', ''),
                data.get('concern_score', ''),
                data.get('concern_date', '')
            ]])
        else:
            # 新規ユーザー追加
            sheet.append_row([
                data.get('user_id', ''),
                data.get('name', ''),
                data.get('registration_date', ''),
                data.get('concern_target', ''),
                data.get('target_detail', ''),
                data.get('concern_description', ''),
                data.get('concern_duration', ''),
                data.get('concern_score', ''),
                data.get('concern_date', '')
            ])
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
        coach = CoachResponder(APP_PASSWORD)
        
        for event in events:
            # 友だち追加イベント
            if event['type'] == 'follow':
                print(f"友だち追加イベント検知: {event}")
                reply_token = event['replyToken']
                user_id = event['source']['userId']
                
                welcome_message = """ご登録ありがとうございます！

お名前またはニックネームを教えてください。"""
                
                send_line_message(reply_token, welcome_message)
                
                # 仮登録
                save_user_data(user_id, {
                    'user_id': user_id,
                    'registration_date': str(datetime.now())
                }, worksheet)
                continue
            
            # メッセージイベント
            if event['type'] != 'message' or event['message']['type'] != 'text':
                continue
            
            user_id = event['source']['userId']
            user_message = event['message']['text']
            reply_token = event['replyToken']
            
            print(f"========== メッセージ受信 ==========")
            print(f"ユーザーID: {user_id}")
            print(f"メッセージ: {user_message}")
            
            # ユーザーデータ取得
            user_data, _ = get_user_data(user_id, worksheet)
            print(f"ユーザーデータ: {user_data}")
            
            # 登録フロー
            if not user_data or not user_data.get('name'):
                # 名前入力待ち
                if not user_data:
                    user_data = {'user_id': user_id, 'registration_date': str(datetime.now())}
                
                user_data['name'] = user_message.strip()
                save_user_data(user_id, user_data, worksheet)
                
                response = """ありがとうございます。

簡単な質問に答えてください。

この悩みは誰についてですか？
数字で答えてください：

1. 自分自身
2. 子供（小学生）
3. 子供（中学生）
4. 子供（高校生）
5. 子供（大学生・社会人）"""
                send_line_message(reply_token, response)
                continue
            
            # 質問1: 対象者
            if not user_data.get('concern_target'):
                print(f"質問1処理: 対象者選択")
                target = user_message.strip()
                if target in ['1', '2', '3', '4', '5']:
                    user_data['concern_target'] = target
                    save_user_data(user_id, user_data, worksheet)
                    print(f"対象者設定完了: {target}")
                    
                    # 子供の場合は学年を聞く
                    if target in ['2', '3', '4']:  # 小学生、中学生、高校生
                        print(f"学年質問を送信: カテゴリー{target}")
                        if target == '2':
                            response = """ありがとうございます。

何年生ですか？
1〜6の数字で答えてください。

1. 小学1年
2. 小学2年
3. 小学3年
4. 小学4年
5. 小学5年
6. 小学6年"""
                        elif target == '3':
                            response = """ありがとうございます。

何年生ですか？
1〜3の数字で答えてください。

1. 中学1年
2. 中学2年
3. 中学3年"""
                        elif target == '4':
                            response = """ありがとうございます。

何年生ですか？
1〜3の数字で答えてください。

1. 高校1年
2. 高校2年
3. 高校3年"""
                        send_line_message(reply_token, response)
                    else:
                        print(f"学年質問スキップ: カテゴリー{target}")
                        # 自分自身、または大学生・社会人の場合は学年不要
                        response = """ありがとうございます。

何に悩んでいますか？
自由に答えてください。

（例：落ち着きがない、姿勢が悪い、シュートが入らない、など）"""
                        send_line_message(reply_token, response)
                else:
                    response = """1〜5の数字で答えてください：

1. 自分自身
2. 子供（小学生）
3. 子供（中学生）
4. 子供（高校生）
5. 子供（大学生・社会人）"""
                    send_line_message(reply_token, response)
                continue
            
            # 質問1-2: 学年（子供の場合のみ）
            if user_data.get('concern_target') in ['2', '3', '4'] and not user_data.get('target_detail'):
                grade = user_message.strip()
                target = user_data.get('concern_target')
                
                # 小学生: 1〜6
                if target == '2' and grade in ['1', '2', '3', '4', '5', '6']:
                    user_data['target_detail'] = f"小{grade}"
                    save_user_data(user_id, user_data, worksheet)
                    
                    response = """ありがとうございます。

何に悩んでいますか？
自由に答えてください。

（例：落ち着きがない、姿勢が悪い、シュートが入らない、など）"""
                    send_line_message(reply_token, response)
                
                # 中学生: 1〜3
                elif target == '3' and grade in ['1', '2', '3']:
                    user_data['target_detail'] = f"中{grade}"
                    save_user_data(user_id, user_data, worksheet)
                    
                    response = """ありがとうございます。

何に悩んでいますか？
自由に答えてください。

（例：落ち着きがない、姿勢が悪い、シュートが入らない、など）"""
                    send_line_message(reply_token, response)
                
                # 高校生: 1〜3
                elif target == '4' and grade in ['1', '2', '3']:
                    user_data['target_detail'] = f"高{grade}"
                    save_user_data(user_id, user_data, worksheet)
                    
                    response = """ありがとうございます。

何に悩んでいますか？
自由に答えてください。

（例：落ち着きがない、姿勢が悪い、シュートが入らない、など）"""
                    send_line_message(reply_token, response)
                
                else:
                    # 範囲外の数字
                    if target == '2':
                        response = """1〜6の数字で答えてください。"""
                    else:
                        response = """1〜3の数字で答えてください。"""
                    send_line_message(reply_token, response)
                continue
            
            # 質問2: 悩みの内容
            if user_data.get('concern_target') and not user_data.get('concern_description'):
                # 学年が必要なのに未入力の場合はスキップ
                if user_data.get('concern_target') in ['2', '3', '4'] and not user_data.get('target_detail'):
                    continue
                
                user_data['concern_description'] = user_message.strip()
                save_user_data(user_id, user_data, worksheet)
                
                response = """ありがとうございます。

いつから気になっていますか？
数字で答えてください：

1. 最近（1ヶ月以内）
2. 数ヶ月前から
3. 半年以上前から
4. ずっと"""
                send_line_message(reply_token, response)
                continue
            
            # 質問3: 期間
            if not user_data.get('concern_duration'):
                duration = user_message.strip()
                if duration in ['1', '2', '3', '4']:
                    user_data['concern_duration'] = duration
                    save_user_data(user_id, user_data, worksheet)
                    
                    response = """ありがとうございます。

最後の質問です。

今の悩み度を1〜10で教えてください。
1=とても良い
10=とても悪い"""
                    send_line_message(reply_token, response)
                else:
                    response = """1〜4の数字で答えてください：

1. 最近（1ヶ月以内）
2. 数ヶ月前から
3. 半年以上前から
4. ずっと"""
                    send_line_message(reply_token, response)
                continue
            
            # 質問4: 悩み度
            if not user_data.get('concern_score'):
                score = user_message.strip()
                if score.isdigit() and 1 <= int(score) <= 10:
                    user_data['concern_score'] = score
                    user_data['concern_date'] = str(datetime.now())
                    save_user_data(user_id, user_data, worksheet)
                    
                    response = """ありがとうございました。
記録しました。

1ヶ月後に変化を確認させていただきます。

ご不明な点があれば、いつでもお聞きください。

時間を置いてから相談すると返答に時間がかかることがあります。
その際は数分程度置いてから、もう一度送信をお願いします。"""
                    send_line_message(reply_token, response)
                else:
                    response = """1〜10の数字で答えてください。

1=とても良い
10=とても悪い"""
                    send_line_message(reply_token, response)
                continue
            
            # 通常の会話（登録完了後）
            print(f"AI応答生成開始")
            response = coach.respond(user_message, user_data)
            print(f"AI応答: {response[:100]}...")
            
            # 応答送信
            send_line_message(reply_token, response)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Processing failed'}), 500

@app.route('/')
def home():
    return "AI Coach System - Running"

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
