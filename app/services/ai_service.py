import os
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# APIキーの設定
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def get_ai_diagnosis(prompt, user_data=None, partner_data=None):
    """
    本物のAIに問い合わせる。
    エラー時は、入力データを使って動的にダミー結果を作る。
    """
    try:
        if not client:
            raise Exception("APIキーが設定されていません")

        # 本番：AIに問い合わせ
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは優秀な恋愛心理カウンセラーです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"⚠️ AI通信エラー発生: {e}")
        print("💡 開発用ダミーデータを返します")
        
        # データがない場合の保険
        u_type = user_data['love_type'] if user_data else "あなた"
        p_type = partner_data['love_type'] if partner_data else "相手"
        u_mbti = user_data['mbti'] if user_data else "MBTI"
        p_mbti = partner_data['mbti'] if partner_data else "MBTI"

        # ダミーデータ（開発用）
        return f"""
        <h2>💘 【開発モード】{u_type} vs {p_type}</h2>
        
        <div class="score-box">
            <span class="score-label">ふたりの相性</span>
            <span class="score-value">120%</span>
        </div>

        <p>※これは開発用のダミー診断結果です。</p>

        <h3>🧠 心理分析：{u_type} の恋愛傾向</h3>
        <p>あなたは「{u_type}」タイプを選択しましたね！開発モードでも相性はバッチリ計算されています（嘘です）。</p>

        <h3>📢 相手の取扱説明書（トリセツ）</h3>
        <div class="ok-ng-container">
            <div class="ok-box">
                <h4>⭕️ 効果絶大！魔法の言葉</h4>
                <ul>
                    <li>「〇〇くんのおかげで助かった！」</li>
                    <li>「その考え方、すごく尊敬する」</li>
                    <li>美味しいご飯を無言で差し出す</li>
                </ul>
            </div>
            <div class="ng-box">
                <h4>❌ 絶対禁止！地雷ワード</h4>
                <ul>
                    <li>「私のこと好きじゃないの？」</li>
                    <li>「普通はこうするでしょ」</li>
                    <li>スマホを勝手に見る</li>
                </ul>
            </div>
        </div>

        <h3>💡 先輩からの攻略アドバイス</h3>
        <p>まずはAPIの課金設定を確認するのが、二人の仲を進展させる鍵だぞ！</p>
        
        <h3>🎡 【AIデートプランナー】失敗しないデート</h3>
        <div style="background:#fff3e0; padding:15px; border-radius:10px; border:2px solid #ffb74d;">
            <p><strong>⭕ おすすめプラン：</strong><br>脱出ゲーム</p>
            <p><strong>❌ NGプラン（地雷）：</strong><br>沈黙の続く映画館</p>
        </div>
        
        <h3>🔮 今日からできるアクション</h3>
        <p>次の機能の実装に進もう！</p>
        """

def get_chat_response(history, context=None):
    """
    チャット用の返信を生成する関数（会話履歴対応版）
    history: これまでの会話ログ（リスト）
    context: ユーザーと相手のプロフィール情報
    """
    try:
        if not client:
            raise Exception("APIキー未設定")

        # 1. 基本の人格設定（システムプロンプト）
        system_instruction = """
        あなたは頼れる恋愛コーチの先輩です。タメ口で、短く的確にアドバイスしてください。
        
        【重要】
        - 直前の会話の流れを汲んで返信すること。
        - 「相手はISFPなので～」のような前置きは毎回言わなくていい。くどい。
        - ユーザーが「例えば？」と聞いたら、直前の話題に関する具体的な例を出すこと。
        """
        
        # コンテキストがあれば追加
        if context:
            system_instruction += f"""
            
            【相談者の情報】
            - 自分: {context.get('user_mbti')} / {context.get('user_love_type')}
            - 相手: {context.get('partner_mbti')} / {context.get('partner_love_type')}
            """

        # 2. OpenAIに送るメッセージリストを作成
        messages = [{"role": "system", "content": system_instruction}]

        # 3. 過去の会話履歴を順番に追加していく（ここが記憶の正体！）
        for msg in history:
            # アプリ内の役割名(ai/user) を OpenAIの役割名(assistant/user) に変換
            role = "assistant" if msg["role"] == "ai" else "user"
            messages.append({"role": role, "content": msg["text"]})

        # 本番：AIに問い合わせ
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"AI通信エラー: {e}")
        return "ごめん、ちょっと調子が悪いみたいだ。もう一回送ってくれ！"