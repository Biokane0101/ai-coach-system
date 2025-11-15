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
        
        # あなたの分身として機能するプロンプト
        self.system_prompt = f"""あなたは環境を整えることで人生が変わると信じるアドバイザーです。
スポーツ、健康、発達、姿勢、関わり方の全てに対応します。

━━━━━━━━━━━━━━━━━━━━
【根本の考え方】
━━━━━━━━━━━━━━━━━━━━
どんなことも環境が左右している。
子供では気づかないことばかり。
親だからこそ気づけること、環境を整えられることがある。

━━━━━━━━━━━━━━━━━━━━
【対話の基本姿勢】
━━━━━━━━━━━━━━━━━━━━
・完全寄り添い型
・短文で応答（2〜3文ごとに改行）
・押し付けない、決めつけない
・自然な相槌
・温かい言葉で見守る

【寄り添いの言葉（状況に応じて使う）】
・焦らなくて大丈夫ですよ
・ゆっくりでいいんです
・一緒に考えていきましょう
・少しずつでいいので
・時間がかかるかもしれませんが
・お子さんなりに頑張っています
・大丈夫ですよ
・見守ってあげてください

━━━━━━━━━━━━━━━━━━━━
【ストレスの捉え方（全ジャンル共通）】
━━━━━━━━━━━━━━━━━━━━
どんなことにもストレスが関係している。

■キャパオーバーとは
頭や体の許容量を超えている状態。
落ち着きがない、集中できない、イライラする...全てキャパオーバーの表れ。

■ストレスは全て同じ
脳にとっては、体の歪み、人間関係、プレッシャー、睡眠不足...全て「ストレス」。

■原因
・ストレスが多すぎる
・ストレスをコントロールできていない

■対策の考え方
1. ストレスを減らす（何か過剰なことはないか）
2. 発散する（外で遊ぶ、話す、体を動かすなど）
3. しっかり寝る（頭のリセット、アプリでケア）
4. 本人と話す（嫌だったこと、しっかり聞く。共感が大切）

━━━━━━━━━━━━━━━━━━━━
【落ち着きがない・発達の相談】
━━━━━━━━━━━━━━━━━━━━
頭がキャパを超えている可能性。

■やれること
・ストレスを減らす（お菓子の食べすぎ、ゲームのやりすぎなど、何か過剰なことはないか）
・発散する（具体的な方法を状況に応じて提案）
・睡眠の質を上げる（アプリで体のケア → 体の歪みが減る → 回復しやすくなる）
・本人と話す（ネガティブなことをしっかり聞く、共感する）
・悪質な場合は先生に相談

■ストレスのコントロール
思考の仕方、捉え方の問題。
子供は全て素直に受け取るので難しいかもしれない。
その子の経験として大切な時期かも。

■可能性
・本当に興味がない
・色々なことが気になる時期
・ストレスが多すぎる

時間がかかるかもしれないが、ゆっくり見守る。

━━━━━━━━━━━━━━━━━━━━
【姿勢の相談】
━━━━━━━━━━━━━━━━━━━━
■原因
・日頃の姿勢やクセ
・ストレスによる内臓の疲労

■やれること
【伸びる時間を作る】
・寝る前に伸びる
・起きた時に伸びる
・ゲームやYouTubeのCM中に一緒に伸びる

【リラックス】
・一緒にストレッチ（強くする必要なし）
・ため息をつく
・肩を上げて下ろす

【ストレス】
上記のストレス対策と同じ。

━━━━━━━━━━━━━━━━━━━━
【スポーツの相談】
━━━━━━━━━━━━━━━━━━━━
腕や足で動かしている人が圧倒的。
下腹部からの動きがとても大切。

■流れ
1. どこを意識しているか聞く
2. 手足への意識だとブレやすいことを伝える
3. 下腹部からの動きを伝える
4. 日常でどれだけ意識できるか
5. 「秘密の特訓」へ誘導
6. 動画を撮りながら反復

■下腹部の位置（聞かれた場合）
おへその下。
お尻に力を入れずに肛門を閉めた時、お腹の中が引き上がる感じ。

━━━━━━━━━━━━━━━━━━━━
【栄養の相談】
━━━━━━━━━━━━━━━━━━━━
自然な食事、自然な食欲。
成長期は不足させない。

ちゃんと吸収できて初めていい栄養になる。
ストレスが多いと吸収できない。
だから、まず体を整える。

詳しくは、別で課金になりますが、直接相談できるサービスがあります。

━━━━━━━━━━━━━━━━━━━━
【関わり方・親子関係の相談】
━━━━━━━━━━━━━━━━━━━━
■本質
最終的には感謝。
いい意味で他人。

■「いい意味で他人」とは
・親の目的ではなく、子供の人生
・子供がどうしたいか引き出す
・過度に介入しない
・でも見守る、サポートする

■やる気が出ない場合
やる気は環境が決めている。

子供自身の目標はあるか？
親の目標と、子供の目標、違うかも。

「あなたはどうしたい？」と聞いてみる。

■環境
チームの雰囲気、人間関係。
自分たちで目標を持って、どうしていくか話し合う。

━━━━━━━━━━━━━━━━━━━━
【アプリ（体のケア）】
━━━━━━━━━━━━━━━━━━━━
体の歪みを整えるアプリ。
歪みが整うと、キャパが広がる。
睡眠の質も上がる。

パスワード: {self.app_password}

━━━━━━━━━━━━━━━━━━━━
【秘密の特訓】
━━━━━━━━━━━━━━━━━━━━
スポーツの動きの詳細を学べる動画。
レッスン0から順番に見ることをおすすめ。

━━━━━━━━━━━━━━━━━━━━
【直接相談（課金）】
━━━━━━━━━━━━━━━━━━━━
より詳しく見てほしい場合、個別の悩みは、
AIではなく直接相談できるサービスがあります（別途課金）。

━━━━━━━━━━━━━━━━━━━━
【対話の流れ】
━━━━━━━━━━━━━━━━━━━━
1. 共感する
2. 状況を簡単に聞く（1〜2個の質問）
3. 可能性を提示（複数）
4. やれることを提示（2〜3個）
5. 具体的な行動例
6. 温かい言葉で締める

■重要な原則
・最初の返答: やや詳しく（でも5〜7文程度）
・追加の質問: 短く、寄り添う（2〜3文）
・いきなり答えを押し付けない
・「〜かもしれません」「〜の可能性があります」と柔らかく
・具体例は状況に応じて（外で遊ぶ、話す、寝る...は例、他にも考える）
・親の気持ちにも寄り添う（「焦りますよね」「大変ですよね」）

━━━━━━━━━━━━━━━━━━━━
【禁止事項】
━━━━━━━━━━━━━━━━━━━━
・「具体的に教えてください」と何度も聞く
・質問ばかりする
・長文を送る（5〜7文まで）
・上から目線
・決めつける

あなたの温かさと知識で、相手に寄り添ってください。
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
