import openai
import os
from datetime import datetime

class CoachBrain:
    def __init__(self):
        # OpenAI v1.0以降の新しい初期化方法
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def generate_response(self, user_message, user_data):
        """ユーザーメッセージに対するAI応答を生成"""
        try:
            # システムプロンプト（あなたの下腹部理論）
            system_prompt = self._get_system_prompt(user_data)
            
            # OpenAI v1.0の新しいAPI形式
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_message = response.choices[0].message.content.strip()
            
            # ユーザーデータ更新判定
            updates = self._analyze_progress(user_message, user_data, ai_message)
            
            return {
                'message': ai_message,
                'user_data_updates': updates
            }
            
        except Exception as e:
            print(f"OpenAI API エラー: {e}")
            return {
                'message': "申し訳ございません。システムエラーが発生しました。しばらく経ってから再度お試しください。",
                'user_data_updates': {}
            }
    
    def _get_system_prompt(self, user_data):
        """ユーザーレベルに応じたシステムプロンプト"""
        level = user_data.get('level', 'beginner')
        
        base_prompt = """
あなたは専門的なフィットネスコーチです。以下の独自理論に基づいて指導してください：

【下腹部理論】
1. 基本原理：肛門を軽く締める→お腹の内側を引き上げる
2. 段階的習得：初心者から上級者まで段階的にマスター
3. 適用範囲：動き・フォーム指導のみ（技術・グリップは除く）

【指導方針】
- 動き・フォーム：下腹部理論を活用
- 技術・グリップ：種目別基本＋個人感覚を重視
- 栄養：レベル別・引き算アプローチ・ストレス確認必須
- 怪我：セルフケア情報＋専門機関相談推奨

常に親しみやすく、具体的で実践的なアドバイスを心がけてください。
"""
        
        if level == 'beginner':
            return base_prompt + "\n初心者向けに基礎から丁寧に説明してください。"
        elif level == 'intermediate':
            return base_prompt + "\n中級者として、より詳細な技術指導を行ってください。"
        else:
            return base_prompt + "\n上級者として、高度な理論と実践を組み合わせて指導してください。"
    
    def _analyze_progress(self, user_message, user_data, ai_response):
        """ユーザーの進捗を分析してデータ更新"""
        updates = {
            'last_interaction': datetime.now().isoformat(),
            'progress': user_data.get('progress', 0) + 1
        }
        
        # 卒業判定（簡単な例）
        if user_data.get('progress', 0) > 50:
            updates['graduation_ready'] = True
            
        # レベルアップ判定
        progress = updates['progress']
        if progress > 20 and user_data.get('level') == 'beginner':
            updates['level'] = 'intermediate'
        elif progress > 40 and user_data.get('level') == 'intermediate':
            updates['level'] = 'advanced'
            
        return updates
