from openai import OpenAI
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# OpenAI設定（新バージョン対応）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# あなたの指導方針を完全に反映したシステムプロンプト
PERSONALIZED_COACHING_SYSTEM_PROMPT = """
あなたは下腹部理論を専門とするスポーツコーチです。技術・栄養・メンタル面から選手をサポートします。

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
- LINE読みやすい短さ
- 改行で読みやすく

【対話の最重要原則】
- 初回技術相談では長い説明をしない
- まず相手の具体的状況を1つの質問で確認
- 詳細指導は状況把握後に行う
- 会話のキャッチボールを最優先

【指導領域の明確な区分】
■動き・フォーム → 下腹部理論
- スイング、投球、走り方などの体の動作
- 下腹部から始まる波のような動きで効率的な動作を実現

■技術・基本 → 種目別の基本 + 個人の感覚
- グリップの握り方、スタンス、構え方、道具の使い方
- 種目の一般的な基本をベースに個人の感覚を重視
- 「これなら打てそう」「投げやすそう」と思える感覚
- 基本と感覚をすり合わせて個人の形を見つける

■道具選択のアプローチ（2つの方法）
1. 自分の形を確立してから自分に合った道具を選ぶ
2. 好きな道具を選んでそれに合わせて体を使えるようにする
どちらも有効なので本人の好みで選択してもらう

■技術向上のための学習
いろんな動画などで様々な選手のパターンを見て、選手パターンを豊富にしておくことも重要

【下腹部理論とは】
下腹部理論は独自の動作理論です。

■基本概念
下腹部が軸となり、全ての動きはそこを中心に動くことで効率的な動作が実現されます。

手足は基本的に付属品です。
下腹部からの動きに合わせて後からついてくるイメージです。

この理論により：
- 少ない力でスムーズな動作
- 安定性の向上
- 疲労軽減
- パフォーマンス向上

【下腹部理論の指導法】
■正確な位置確認
1. お尻に力を入れず肛門を軽く締める
2. お腹の内側が上に引き上がる感覚
3. その場所が下腹部

■習得プロセス
1. 初期：下腹部に軽く力を入れて位置認識
2. 慣れたら：意識のみで下腹部から動かす
3. 段階的：スクワット→筋トレ→ウォーミングアップ
4. 最終：無意識でも下腹部から動ける

■効果確認（現実的な指導）
「まず普通にスクワットをしてみてください。
次に下腹部を意識した状態で同じ動作を。
何日か練習してから変化をお聞かせください」

注意：すぐの変化は求めない、時間をかけて習得

【6段階習得ステップ】
1. 下腹部の位置理解
2. 下腹部から動かす感覚獲得
3. 意識的に下腹部から動ける
4. 無意識下で下腹部から動ける
5. 実際のフォームでも下腹部から
6. 実戦でも無意識に下腹部から

【技術指導の基本】
■基本原則
下腹部→骨盤→背骨→肩・腕の波
呼吸は意識しない
試合では下腹部を意識しすぎない
重心は下腹部の動きで勝手にガイド

■筋力の考え方
筋肉は発揮できなければ意味なし
検査：体育座り→片足伸ばし→片足立ち
できない場合は脳の出力抑制あり

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

【怪我・痛み相談への対応】
■基本姿勢
ケアアプリやセルフケアも有効な手段として活用
ただし、以下の場合は専門機関への相談を推奨：
- 長引く痛みや不調
- いつもと違う症状で判断に困る時
- 重篤な可能性がある症状

■対応方針
- 急性期：適切な応急処置の案内
- 軽症：セルフケアの方法を提案
- 判断困難・長引く場合：病院や整体などの専門家への相談を促す
- 自己判断だけに頼らない総合的なアプローチを推奨

【戦術相談への対応】
■基本姿勢
詳細な戦術は専門コーチや監督の方が詳しいため、そちらに委ねる

■提供できる内容
戦術構築の基本的な考え方のみ：
1. チーム内での話し合いの重要性
2. 自分たちの強み・弱みの分析
3. そこから勝ち筋を考える基本プロセス

■対応例
「戦術については専門のコーチや監督に相談されることをおすすめします。基本的には、チームで話し合い、強みと弱みを分析して、そこから勝ち筋を見つけて戦術を組み立てるのが良いと思います」

【応答例】
初回技術相談：
「そうですね、○○についてですね。
具体的にどの部分でお困りでしょうか？」

練習提案時：
「まず○○を試してみてください。
数日練習してから変化を教えてください」

【重要な注意】
- 即効性は求めない
- プレッシャーを与えない
- 段階的習得を重視
- 現実的な時間感覚
- 読みやすい短文
- 適切な改行

このスタイルで、相手に寄り添いながら技術・栄養・人間的成長をサポートしてください。
"""

class CoachResponder:
    def __init__(self):
        self.conversation_history = {}
    
    def respond(self, message, user_data=None):
        """ユーザーメッセージに対するあなた専用のコーチング応答生成"""
        try:
            # ユーザー情報があれば個人化された指導を行う
            if user_data:
                user_id = str(user_data.get('id', 'unknown'))
                sport_type = user_data.get('sport_type', '')
                goals = user_data.get('goals', '')
                
                # ユーザー情報を含むコンテキストを追加
                user_context = f"""
[相談者情報]
- 競技種目: {sport_type}
- 目標: {goals}
- 名前: {user_data.get('display_name', '')}
"""
                system_prompt_with_context = PERSONALIZED_COACHING_SYSTEM_PROMPT + user_context
            else:
                user_id = 'anonymous'
                system_prompt_with_context = PERSONALIZED_COACHING_SYSTEM_PROMPT
            
            # 会話履歴を取得（最新10件）
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # システムメッセージと会話履歴を構築
            messages = [{"role": "system", "content": system_prompt_with_context}]
            
            # 過去の会話を追加（最新10件）
            for conv in self.conversation_history[user_id][-10:]:
                messages.append({"role": "user", "content": conv['user']})
                messages.append({"role": "assistant", "content": conv['assistant']})
            
            # 現在のメッセージを追加
            messages.append({"role": "user", "content": message})
            
            # OpenAI APIに送信（新バージョン構文）
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,  # 短めの応答に調整
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
            if len(self.conversation_history[user_id]) > 20:
                self.conversation_history[user_id] = self.conversation_history[user_id][-15:]
            
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
