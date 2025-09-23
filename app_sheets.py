from flask import Flask, request, jsonify
import os
import json
import logging
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from coach_brain import CoachResponder
import gspread
from google.oauth2.service_account import Credentials

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 環境変数から設定を読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# LINE Bot設定
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Sheets設定（環境変数から認証情報を取得）
try:
    # 環境変数からGoogle認証情報を読み込み（Render用）
    google_credentials = os.getenv('GOOGLE_CREDENTIALS')
    if google_credentials:
        # JSON文字列をパース
        creds_dict = json.loads(google_credentials)
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
        logger.info("Google Sheets connection established (from environment variables)")
    else:
        # ローカル開発用（credentials.jsonファイル）
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
        logger.info("Google Sheets connection established (from local file)")
except Exception as e:
    logger.error(f"Google Sheets connection failed: {e}")
    gc = None
    sheet = None

# コーチ初期化
coach = CoachResponder()

def calculate_graduation_date(school_year, registration_date):
    """登録時の学年から卒業予定日を自動計算"""
    reg_year = registration_date.year
    reg_month = registration_date.month
    
    # 学年から卒業までの年数を計算
    years_to_graduation = {
        '中学1年': 3, '中学2年': 2, '中学3年': 1,
        '高校1年': 3, '高校2年': 2, '高校3年': 1
    }
    
    remaining_years = years_to_graduation.get(school_year, 0)
    
    # 年度の考え方：4月〜3月が1年度
    if reg_month >= 4:  # 4月以降の登録
        graduation_year = reg_year + remaining_years
    else:  # 1-3月の登録（前年度の続き）
        graduation_year = reg_year + remaining_years - 1
    
    # 卒業は3月とする
    graduation_date = datetime(graduation_year, 3, 1)
    return graduation_date

def save_user_minimal(line_id, display_name, school_year, sport_type, goals=""):
    """最小限ユーザー情報をGoogle Sheetsに保存"""
    if not sheet:
        logger.warning("Google Sheets not available, skipping save")
        return False
    
    try:
        registration_date = datetime.now()
        graduation_date = calculate_graduation_date(school_year, registration_date)
        
        row_data = [
            line_id,
            display_name,
            school_year,
            sport_type,
            goals,
            registration_date.strftime('%Y-%m-%d'),
            graduation_date.strftime('%Y-%m-%d'),
            'active'
        ]
        
        sheet.append_row(row_data)
        logger.info(f"User saved: {display_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save user: {e}")
        return False

def get_user_minimal(line_id):
    """最小限ユーザー情報をGoogle Sheetsから取得"""
    if not sheet:
        return None
    
    try:
        records = sheet.get_all_records()
        for record in records:
            if record.get('line_id') == line_id and record.get('status') == 'active':
                return record
        return None
        
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        return None

def check_graduation_status(user_data):
    """自動卒業チェック"""
    graduation_date_str = user_data.get('graduation_date')
    if not graduation_date_str:
        return False
    
    try:
        graduation_date = datetime.strptime(graduation_date_str, '%Y-%m-%d')
        current_date = datetime.now()
        return current_date >= graduation_date
    except:
        return False

def deactivate_user(line_id):
    """ユーザーを卒業状態に変更"""
    if not sheet:
        return
    
    try:
        records = sheet.get_all_values()
        for i, row in enumerate(records):
            if len(row) > 0 and row[0] == line_id:  # line_idが一致
                sheet.update_cell(i + 1, 8, 'graduated')  # status列を更新
                logger.info(f"User graduated: {line_id}")
                break
    except Exception as e:
        logger.error(f"Failed to deactivate user: {e}")

@app.route("/health", methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sheets_connected": sheet is not None
    })

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400
    
    return 'OK'

# 簡易セッション管理
user_sessions = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_id = event.source.user_id
        user_message = event.message.text
        
        # ユーザー情報取得
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        logger.info(f"Received message from {display_name}: {user_message}")
        
        # Google Sheetsからユーザー情報取得
        user_data = get_user_minimal(user_id)
        
        if user_data:
            # 既存ユーザーの卒業チェック
            if check_graduation_status(user_data):
                deactivate_user(user_id)
                reply_message = f"""ご卒業おめでとうございます！{display_name}さん

スポーツを通じて培った「壁を乗り越える力」を、社会でも活かしてください。

今後のご活躍を心よりお祈りしています。"""
            else:
                # 通常のコーチング応答
                if any(word in user_message.lower() for word in ['こんにちは', 'おはよう', 'こんばんは', 'はじめまして', 'hello']):
                    reply_message = f"""こんにちは、{display_name}さん！

下腹部理論を専門とするスポーツコーチです。技術のこと、栄養のこと、メンタル面など、何でもお気軽にご相談ください。"""
                else:
                    coach_response = coach.respond(user_message, user_data)
                    reply_message = coach_response
        else:
            # 新規ユーザー登録
            reply_message = handle_new_user_registration(user_id, user_message, display_name)
        
        # 応答送信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ございませんが、一時的にシステムに問題が発生しています。")
        )

def handle_new_user_registration(user_id, user_message, display_name):
    """新規ユーザー登録処理"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {'step': 0}
    
    session = user_sessions[user_id]
    step = session.get('step', 0)
    
    if step == 0:
        session['step'] = 1
        return "学年を教えてください。（例：高校2年、中学3年）"
    
    elif step == 1:
        session['school_year'] = user_message
        session['step'] = 2
        return "競技種目を教えてください。（例：野球、サッカー、バスケットボール）"
    
    elif step == 2:
        session['sport_type'] = user_message
        session['step'] = 3
        return "目標があれば教えてください。（なければ「なし」と入力）"
    
    elif step == 3:
        goals = user_message if user_message.lower() != 'なし' else ""
        
        # Google Sheetsに保存
        success = save_user_minimal(
            user_id, display_name, 
            session['school_year'], 
            session['sport_type'], 
            goals
        )
        
        # セッションクリア
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        if success:
            return f"""ご登録ありがとうございました！

{display_name}さんの{session['sport_type']}を下腹部理論でサポートします。

何でもお気軽にご相談ください。"""
        else:
            return """登録処理で問題が発生しましたが、一時的にコーチング機能をご利用いただけます。

技術のこと、栄養のこと、何でもお気軽にご相談ください。"""

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
