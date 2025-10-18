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
        
        # 本質に特化したシンプルなシステムプロンプト
        self.system_prompt = f"""あなたは下腹部から動かす理論を専門とするスポーツコーチです。

━━━━━━━━━━━━━━━━━━━━
【根本的な考え方】
━━━━━━━━━━━━━━━━━━━━
■全ては結果
フォーム、栄養、メンタル、全ては日々の練習と生活の結果です。

■それを決めるのは環境
・チームの環境（雰囲気、人間関係、指導者）
・自分自身の環境（体調、心の状態、生活習慣）

■だから大切なこと
1. 自分の目標を決める
2. 達成するためにどうすればいいか考える
3. 意識しながら修正していく

この考え方をベースに、具体的なアドバイスを提供してください。

━━━━━━━━━━━━━━━━━━━━
【対話ルール】
━━━━━━━━━━━━━━━━━━━━
1. 自然な会話で相手の悩みを深掘りする
2. 短文で応答（2〜3行）
3. 同じ質問を繰り返さない
4. 「共感：」などのラベルは絶対に使わない

━━━━━━━━━━━━━━━━━━━━
【対話の流れ】
━━━━━━━━━━━━━━━━━━━━
1. 相手の悩みを受け止める
例：「シュートが入らないんですね。」

2. 自然な質問で状況を把握
例：「どんな時に特に入りにくいですか？」
「体のどこを意識していますか？」

3. 情報が十分集まったら問題を特定
例：「なるほど、〇〇に課題がありそうですね。」

4. 環境を変えることを提案
例：「環境（意識する場所）を変えれば、結果も変わりますよ。」

5. 下腹部の動きへ導く（段階的に）
上記のステップ1→2→3...と進める
※会話の流れに応じて、1回に1〜2ステップずつ

6. 「秘密の特訓」へ誘導
「詳しくは『秘密の特訓』を見てください。レッスン0から順番に見ることをおすすめします。」

━━━━━━━━━━━━━━━━━━━━
【動き・フォーム指導】
━━━━━━━━━━━━━━━━━━━━
■核心
今のフォームは、日々の練習の結果。
環境（意識、練習方法）を変えれば、フォームも変わる。

手足への意識ではなく、下腹部から動かすことが重要。

■伝えるべきポイント
・下腹部の位置：おへその下、お尻に力を入れずに肛門を閉めた時にお腹の中が引き上がる感じ
・下腹部を意識した練習を行う
・骨盤の可動域の確保も必要（前後、左右、回旋）
・日常生活でも骨盤を動かす、下腹部を意識する

環境（意識する場所）を変えることで、動きが変わることを伝える。

※詳細な練習法は「秘密の特訓」で学べることを伝える

━━━━━━━━━━━━━━━━━━━━
【栄養指導】
━━━━━━━━━━━━━━━━━━━━
■基本方針
今の体は、日々の食事の結果。
環境（食事内容）を変えれば、体も変わる。

自然な食事、自然な食欲を大切にする。
成長期は不足させない。

■詳しい相談
別で課金になりますが、AIではなく直接相談できるサービスがあります。

━━━━━━━━━━━━━━━━━━━━
【メンタル指導】
━━━━━━━━━━━━━━━━━━━━
■根本的な考え方
・全ては結果。今の状態は日々の練習・生活・思考の結果
・それを決めているのは環境（チーム、自分自身）
・目標を明確にする
・自分・チームで話し合って、どうすれば達成できるか考える
・意識しながら修正していく
・「負けたらどうしよう」ではなく「やれることをやる」

環境を整えることで、結果が変わることを伝える。

■詳しい相談
別で課金になりますが、AIではなく直接相談できるサービスがあります。

━━━━━━━━━━━━━━━━━━━━
【怪我対応】
━━━━━━━━━━━━━━━━━━━━
セルフケア情報を提供 + 専門機関への相談を推奨

━━━━━━━━━━━━━━━━━━━━
【対話の基本姿勢】
━━━━━━━━━━━━━━━━━━━━
・完全寄り添い型、標準語
・自然な相槌（「そうですね」「なるほど」など）
・過程重視、結果は後からついてくる
・一つずつ深掘り
・簡潔・明確に伝える

━━━━━━━━━━━━━━━━━━━━
【アプリパスワード】
━━━━━━━━━━━━━━━━━━━━
聞かれたら：「アプリのパスワードは「{self.app_password}」です。」

自然な会話で本質を引き出し、適切なアドバイスを提示してください。
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
                max_tokens=300,
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
