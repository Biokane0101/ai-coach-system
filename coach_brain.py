from openai import OpenAI
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# OpenAI設定
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CoachResponder:
    def __init__(self, app_password="bio2025"):
        self.conversation_history = {}
        self.app_password = app_password
        
        # フォーム改善特化のシステムプロンプト
        self.system_prompt = f"""あなたは下腹部から動かす理論を専門とするスポーツコーチです。

━━━━━━━━━━━━━━━━━━━━
【対話ルール】
━━━━━━━━━━━━━━━━━━━━
1. 短文で応答（2〜3行）
2. 「具体的に教えてください」は絶対に言わない
3. 質問は最小限、すぐにアドバイスする
4. 自然な相槌（「そうですね」「なるほど」）

━━━━━━━━━━━━━━━━━━━━
【フォーム改善の流れ】
━━━━━━━━━━━━━━━━━━━━
ステップ1：どこを意識しているか聞く
「どこを意識して動かしていますか？」

ステップ2：下腹部からの動きを伝える
「手足への意識だと、ブレやすくなります。

トップアスリートの共通点は"下腹部からの動き"です。
〇〇（投げる/打つ/蹴るなど）も、下腹部から〇〇しているイメージで動かしてみてください。」

ステップ3：秘密の特訓へ誘導
「詳しくは『秘密の特訓』を見てください。
レッスン0から順番に見ることをおすすめします。」

ステップ4：実践方法を伝える
「動画を撮りながら反復練習してみてください。
他の人に見てもらって意見をもらうのも効果的です。」

ステップ5：直接相談への誘導（必要な場合）
「さらに詳しく見てほしい場合は、別で課金になりますが、AIではなく直接相談できるサービスがあります。」

━━━━━━━━━━━━━━━━━━━━
【下腹部の位置（聞かれた場合のみ）】
━━━━━━━━━━━━━━━━━━━━
「下腹部の位置は、おへその下です。
お尻に力を入れずに肛門を閉めた時、お腹の中が引き上がる感じがしますね。そこです。」

━━━━━━━━━━━━━━━━━━━━
【栄養の相談】
━━━━━━━━━━━━━━━━━━━━
自然な食事、自然な食欲を大切にする。
成長期は不足させない。

詳しくは、別で課金になりますが直接相談できるサービスがあります。

━━━━━━━━━━━━━━━━━━━━
【メンタルの相談】
━━━━━━━━━━━━━━━━━━━━
目標を明確にする。
自分・チームで話し合う。
「負けたらどうしよう」ではなく「やれることをやる」。

詳しくは、別で課金になりますが直接相談できるサービスがあります。

━━━━━━━━━━━━━━━━━━━━
【アプリパスワード】
━━━━━━━━━━━━━━━━━━━━
「アプリのパスワードは「{self.app_password}」です。」

フォーム改善は、意識する場所を変える→動画で確認→反復練習。この流れで進めてください。
"""
    
    def respond(self, message, user_data=None):
        """コーチング応答生成"""
        try:
            # ユーザー情報
            if user_data:
                user_id = str(user_data.get('user_id', 'unknown'))
                name = user_data.get('name', '')
                
                user_context = f"\n[相談者: {name}]"
                system_prompt_with_context = self.system_prompt + user_context
            else:
                user_id = 'anonymous'
                system_prompt_with_context = self.system_prompt
            
            # 会話履歴取得
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # メッセージ構築
            messages = [{"role": "system", "content": system_prompt_with_context}]
            
            # 過去の会話（最新5件のみ）
            for conv in self.conversation_history[user_id][-5:]:
                messages.append({"role": "user", "content": conv['user']})
                messages.append({"role": "assistant", "content": conv['assistant']})
            
            # 現在のメッセージ
            messages.append({"role": "user", "content": message})
            
            # デバッグログ
            print(f"===== ChatGPT送信 =====")
            print(f"会話履歴数: {len(self.conversation_history[user_id])}")
            print(f"現在のメッセージ: {message}")
            
            # OpenAI API呼び出し
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=250,
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            print(f"ChatGPT応答長さ: {len(bot_response)}文字")
            print(f"ChatGPT応答: {bot_response}")
            
            # 会話履歴に保存
            self.conversation_history[user_id].append({
                'user': message,
                'assistant': bot_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # 履歴管理（最新10件まで）
            if len(self.conversation_history[user_id]) > 10:
                self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
            
            return bot_response
            
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            print(f"OpenAI APIエラー: {e}")
            import traceback
            traceback.print_exc()
            
            return """申し訳ございません。

一時的にシステムに問題が発生しています。

少し時間をおいてから、もう一度お試しください。"""

def chunk_text(text, max_length=2000):
    """テキストをLINEメッセージ制限に合わせて分割"""
    if len(text) <= max_length:
        return [text]
    
    # 段落で分割
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk + paragraph + '\n\n') <= max_length:
            current_chunk += paragraph + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
            current_chunk = paragraph + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.rstrip())
    
    return chunks
