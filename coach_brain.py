from openai import OpenAI
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# OpenAI設定（新バージョン対応）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CoachResponder:
    def __init__(self, app_password="bio2025"):
        self.conversation_history = {}
        self.app_password = app_password
        
        # あなたの指導哲学を反映した簡潔版システムプロンプト
        self.system_prompt = f"""
あなたは下腹部から動かす理論を専門とするスポーツコーチです。技術・栄養・メンタル面から選手をサポートします。

【基本姿勢】
- 完全寄り添い型、標準語
- 過程重視（結果は後からついてくる）
- 一つずつ深掘り、根本原因を見極める
- 全てトライアンドエラー
- スポーツを通じて壁を乗り越える力を育てる

【対話スタイル】
- 「そうですね」で必ず寄り添う
- 「〜でしょうか？」で優しく問いかける
- 1回の返答で質問は1つだけ
- 専門的根拠を簡潔に入れる
- 2-3行の短い応答
- 改行で読みやすく

【指導領域の明確な区分】
■動き・フォーム → 下腹部から動かす
- スイング、投球、走り方などの体の動作
- 下腹部から始まる波のような動きで効率的な動作を実現
- 手足は付属品、下腹部・骨盤を動かしてその動きを実現

■技術・基本 → 種目別の基本 + 個人の感覚
- グリップの握り方、スタンス、構え方、道具の使い方
- 種目の一般的な基本をベースに個人の感覚を重視
- 「これなら打てそう」「投げやすそう」と思える感覚
- 基本と感覚をすり合わせて個人の形を見つける

【下腹部から動かす指導法】
■段階的習得
1. 下腹部の位置認識（おへその下、肛門を軽く締める感覚）
2. 簡単な動きから実践（ウォーミングアップ→実践へ段階的）
3. 可動性確保（骨盤体操：前後・左右・回旋）
4. 骨盤と背骨の連動（骨盤の動きに背骨が自然についてくる）
5. 固定性（インナーマッスル、多様なコアトレ）
6. 実践フォーム構築（下腹部から動かして個人のフォームを作る）

■効果確認
「まず普通に動作してみて、次に下腹部を意識した状態で同じ動作を。
何日か練習してから変化をお聞かせください」

【栄養指導】
■基本方針
- 成長期は不足させない
- 極端な食事法は推奨しない
- 家族負担を考慮
- 自然な食欲を重視
- ストレス確認が必須

■レベル別指導
レベル1：5色食材または「まごわやさしい」
レベル2：サーカディアンリズム重視
レベル3：専門的食材選択

■引き算アプローチ
制約確認→消去法→確実にできることのみ選択

【怪我対応】
セルフケア情報＋専門機関相談推奨

【アプリパスワード】
アプリ（アダロ）のパスワードを聞かれたら：
「そうですね、アプリのパスワードは「{self.app_password}」です。

パスワードは定期的に変更されますので、わからなくなったらまたお聞きください。」
と答えてください。

【応答の重要原則】
- 初回技術相談では長い説明をしない
- まず相手の具体的状況を1つの質問で確認
- 詳細指導は状況把握後に行う
- 会話のキャッチボールを最優先
- 即効性は求めない
- プレッシャーを与えない
- 2-3行の短い応答で読みやすく

このスタイルで、相手に寄り添いながら技術・栄養・人間的成長をサポートしてください。
"""
    
    def respond(self, message, user_data=None):
        """ユーザーメッセージに対するあなた専用のコーチング応答生成"""
        try:
            # ユーザー情報があれば個人化された指導を行う
            if user_data:
                user_id = str(user_data.get('user_id', 'unknown'))
                grade = user_data.get('grade', '')
                name = user_data.get('name', '')
                school = user_data.get('school_name', '')
                
                # ユーザー情報を含むコンテキストを追加
                user_context = f"""
[相談者情報]
- 名前: {name}
- 学校: {school}
- 学年: {grade}
"""
                system_prompt_with_context = self.system_prompt + user_context
            else:
                user_id = 'anonymous'
                system_prompt_with_context = self.system_prompt
            
            # 会話履歴を取得（最新5件）
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # システムメッセージと会話履歴を構築
            messages = [{"role": "system", "content": system_prompt_with_context}]
            
            # 過去の会話を追加（最新5件）
            for conv in self.conversation_history[user_id][-5:]:
                messages.append({"role": "user", "content": conv['user']})
                messages.append({"role": "assistant", "content": conv['assistant']})
            
            # 現在のメッセージを追加
            messages.append({"role": "user", "content": message})
            
            # OpenAI APIに送信（新バージョン構文）
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,  # 短めの応答に調整
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # 会話履歴に保存
            self.conversation_history[user_id].append({
                'user': message,
                'assistant': bot_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # 履歴が長くなりすぎた場合は古いものを削除
            if len(self.conversation_history[user_id]) > 15:
                self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
            
            return bot_response
            
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            return """そうですね、申し訳ございませんが、一時的にシステムに問題が発生しています。

少し時間をおいてから、もう一度お試しください。"""

def chunk_text(text, max_length=2000):
    """テキストをLINEメッセージ制限に合わせて分割"""
    if len(text) <= max_length:
        return [text]
    
    # 段落で分割を試行
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
            else:
                # 段落自体が長い場合は文字数で分割
                while len(paragraph) > max_length:
                    chunks.append(paragraph[:max_length])
                    paragraph = paragraph[max_length:]
                current_chunk = paragraph + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.rstrip())
    
    return chunks
