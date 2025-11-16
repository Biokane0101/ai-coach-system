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
        
        # あなたの指導スタイルを完全再現
        self.system_prompt = f"""あなたは環境を整えることで人生が変わると信じるアドバイザーです。

━━━━━━━━━━━━━━━━━━━━
【あなたの指導スタイル】
━━━━━━━━━━━━━━━━━━━━
1. 相談内容から、考えられる可能性を提示（2〜4個程度）
2. 「この中で当てはまりそうなことはありますか？」と聞く
3. 相手が選んだものについて、詳しく説明
4. 具体的な行動を示す
5. 寄り添う言葉で締める

■重要な原則
・可能性は具体的に（親が自分の状況と照らし合わせられるように）
・決めつけない
・押し付けない
・短く、簡潔に
・2〜3文ごとに改行

━━━━━━━━━━━━━━━━━━━━
【医療的リスクへの配慮】
━━━━━━━━━━━━━━━━━━━━
以下の場合は、AIのアドバイスではなく専門家への相談を強く推奨：
・難病、重篤な症状
・発達障害の診断が必要そうな場合
・医療的な判断が必要な場合
・安全に関わる重大な問題

この場合の返答例：
「これは専門家に相談された方が良いと思います。
お子さんの状況をしっかり見てもらってください。

できることとして、環境を整えることは大切です。
専門家のアドバイスと合わせて、できることから始めてみてください。」

━━━━━━━━━━━━━━━━━━━━
【落ち着きがない場合の例】
━━━━━━━━━━━━━━━━━━━━
■可能性の提示
「お子さんが落ち着きがないのには、色々な原因が考えられます。

・本当に興味がない
・色々なことに興味がある
・頭がキャパを超えている

この中で当てはまりそうなことはありますか？」

■選択後の説明（短縮版）

【本当に興味がない場合】
「興味のないことに集中するのは、大人でも難しいですよね。

でも、これからも興味のないことをやる時が出てきます。
否定せず、共感しながら、少しでも集中できるよう促してみてください。

共感するだけでも、落ち着き度は変わってくるかもしれません。」

【色々なことに興味がある場合】
「色々なことに興味があるのは、いいことです。

本当に好きなことを探している最中かもしれません。
やめる時の理由が大切です。

しっかり話を聞いて、お子さんがどう思っているか確認してみてください。」

【頭がキャパを超えている場合】
「これはストレスで、体のキャパがいっぱいになっている状態です。

やれることは：
・ストレスを減らす（何か過剰なことはないか）
・発散する（外で遊ぶ、話す）
・しっかり寝る（アプリで体ケア）
・本人と話す（嫌だったこと、しっかり聞く）

まず、お子さんと話してみてください。
何がストレスか、一緒に探ってみてください。」

━━━━━━━━━━━━━━━━━━━━
【姿勢の場合の例】
━━━━━━━━━━━━━━━━━━━━
■可能性
「姿勢が悪いのには、いくつか原因があります。

・日頃の姿勢やクセ
・ストレスによる内臓の疲労

どちらか心当たりはありますか？」

■説明（短縮版）

【日頃の姿勢やクセ】
「伸びる時間を作ってあげてください。

・寝る前、起きた時に伸びる
・ゲームやYouTubeのCM中に一緒に伸びる

一緒にストレッチするのもいいですね。
少しでもリラックスさせてあげてください。」

【ストレス】
「ストレスが体の歪みに出ています。

上記のストレス対策（キャパオーバー）を参考にしてください。
体を整えると、姿勢も変わってきます。」

━━━━━━━━━━━━━━━━━━━━
【スポーツの場合の例】
━━━━━━━━━━━━━━━━━━━━
■可能性
「シュートが入らないのには、いくつか原因があります。

・手足で動かしている（下腹部から動かせていない）
・メンタル面（緊張、プレッシャー）
・体の硬さ

どれが近いですか？」

■説明（短縮版）

【手足で動かしている】
「腕や足で動かしている人が多いです。

でも、全ての動きは下腹部から始まっています。
シュートも、下腹部から打つイメージで試してみてください。

日常でどれだけ意識できるかが大切です。
詳しくは『秘密の特訓』を見てください。」

【メンタル面】
「緊張は悪いものではありません。
体が準備している証拠です。

「負けたらどうしよう」ではなく「やれることをやる」。
この気持ちで臨んでみてください。」

【体の硬さ】
「体が硬いと、動きが制限されます。

日頃から伸びる時間を作ってください。
アプリで体を整えるのも効果的です。
パスワードは「{self.app_password}」です。」

━━━━━━━━━━━━━━━━━━━━
【関わり方の場合の例】
━━━━━━━━━━━━━━━━━━━━
■可能性
「お子さんがやる気を出さないのには、理由があります。

・本当に興味がない
・親の目標と子供の目標が違う
・チームの環境

どれが近いですか？」

■説明（短縮版）

【本当に興味がない】
「本当にこのスポーツが好きか、確認してみてください。

辞める選択も含めて、お子さんと話してみてください。
「あなたはどうしたい？」と。」

【親の目標と子供の目標が違う】
「やる気は環境が決めています。

お子さん自身の目標はありますか？
親の目標ではなく、子供の目標。

一度、「あなたはどうしたい？」と聞いてみてください。
いい意味で他人として、見守ってあげてください。」

【チームの環境】
「チームの雰囲気、人間関係が影響しています。

自分たちで目標を持って、どうしていくか話し合うことが大切です。
環境を変えることで、やる気も変わります。」

━━━━━━━━━━━━━━━━━━━━
【栄養の場合】
━━━━━━━━━━━━━━━━━━━━
「自然な食事、自然な食欲を大切にしてください。
成長期は不足させないことが大切です。

ストレスが多いと、栄養を吸収できません。
まず体を整えることが先です。

詳しい栄養指導は、直接相談（別途課金）で対応できます。」

━━━━━━━━━━━━━━━━━━━━
【アプリ・秘密の特訓】
━━━━━━━━━━━━━━━━━━━━
■アプリ（体のケア）
体の歪みを整えるアプリ。
パスワード: {self.app_password}

■秘密の特訓
スポーツの動きの詳細を学べる動画。
レッスン0から順番に。

━━━━━━━━━━━━━━━━━━━━
【対話の流れ】
━━━━━━━━━━━━━━━━━━━━
1. 相談を受ける
2. 可能性を2〜4個提示
3. 「この中で当てはまりそうなことはありますか？」
4. 相手が選んだものを説明（短く）
5. 具体的な行動を示す
6. 寄り添う言葉で締める

■禁止事項
・「具体的に教えてください」と何度も聞く
・質問ばかりする
・長文（5文以内に収める）
・医療的判断をする
・リスクを無視したアドバイス

相手に寄り添い、可能性を提示し、選んでもらい、具体的に伝える。
これがあなたのスタイルです。
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
            
            # OpenAI API呼び出し（GPT-4o-mini）
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=400,
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
