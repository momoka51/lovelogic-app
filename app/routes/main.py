import os
import random
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, current_app
from app.logic.prompt_builder import create_diagnosis_prompt
from app.services.ai_service import get_ai_diagnosis, get_chat_response

main_bp = Blueprint('main', __name__)

# --- 📊 レーダーチャート計算ロジック（ここを極端に調整！） ---
def calculate_love_stats(love_type):
    """
    ラブタイプ(4文字)からステータス(1~5)を算出
    基準値を3として、文字によってガッツリ加点・減点する
    """
    # スタートは全部「3（普通）」
    stats = {
        "menhera": 3,   # メンヘラ度
        "devotion": 3,  # 尽くし度
        "cheating": 3,  # 浮気耐性（高いほど浮気しない）
        "commu": 3,     # コミュ力
        "psycho": 3     # サイコパス度
    }
    
    type_str = str(love_type).upper() # 大文字に統一

    # 1. 【L vs F】 主導権
    if "L" in type_str: # Lead（俺様・姉御）
        stats["commu"] += 1      # 引っ張る力
        stats["psycho"] += 1     # 少し冷酷に見える
        stats["devotion"] -= 1   # 尽くすより尽くされたい
    elif "F" in type_str: # Follow（尽くす）
        stats["devotion"] += 2   # 尽くし度爆上げ
        stats["commu"] -= 1      # 受け身

    # 2. 【C vs A】 愛情表現
    if "C" in type_str: # Cuddly（デレデレ・甘えたい）
        stats["menhera"] += 2    # メンヘラ度爆上げ
        stats["devotion"] += 1   # 構ってちゃん
        stats["psycho"] -= 1     # 情に厚い
    elif "A" in type_str: # Accept（包容力）
        stats["cheating"] += 1   # どっしり構える
        stats["menhera"] -= 2    # メンヘラとは無縁

    # 3. 【R vs P】 価値観
    if "P" in type_str: # Passionate（情熱・刺激）
        stats["menhera"] += 1    # 感情の起伏が激しい
        stats["cheating"] -= 1   # 刺激を求めて浮気しがち
    elif "R" in type_str: # Realistic（現実・安定）
        stats["cheating"] += 1   # リスクを冒さない
        stats["psycho"] += 1     # 合理的すぎる一面も

    # 4. 【O vs E】 誠実さ
    if "E" in type_str: # Earnest（真面目・一途）
        stats["cheating"] += 2   # 浮気耐性MAX
        stats["psycho"] -= 1     # 人の痛みがわかる
    elif "O" in type_str: # Optimistic（楽観・自由）
        stats["commu"] += 2      # 誰とでも仲良くなる
        stats["cheating"] -= 2   # 浮気リスク激高（要注意！）

    # リスト形式に変換（1未満は1に、5以上は5に制限する）
    raw_list = [stats["menhera"], stats["devotion"], stats["cheating"], stats["commu"], stats["psycho"]]
    return [max(1, min(5, x)) for x in raw_list]

# --- ☀️ 天気予報ロジック ---
def get_love_forecast():
    weathers = [
        {"icon": "☀️", "status": "恋愛日和", "desc": "今日は攻めの姿勢でOK！気になるあの子に連絡してみよう。"},
        {"icon": "⛅", "status": "曇りのち晴れ", "desc": "午前中は様子見が吉。夕方以降にチャンス到来かも？"},
        {"icon": "☔", "status": "涙雨", "desc": "メンタルが不安定になりがち。今日は自分磨きに集中しよう。"},
        {"icon": "⚡", "status": "波乱の予感", "desc": "些細なことで喧嘩しそう。「余計な一言」に要注意！"},
        {"icon": "🌈", "status": "奇跡の予感", "desc": "まさかの再会や急展開があるかも！？身だしなみは完璧に。"},
    ]
    lucky_types = ["忠犬ハチ公", "ボス猫", "隠れベイビー", "ライオン", "不思議生命体"]
    caution_types = ["恋愛モンスター", "デビル天使", "管理者(ISTJ)", "論理学者(INTP)", "エンターテイナー(ESFP)"]
    selected = random.choice(weathers)
    return {
        "icon": selected["icon"], "status": selected["status"], "desc": selected["desc"],
        "lucky": random.choice(lucky_types), "caution": random.choice(caution_types)
    }

# --- 🚦 ルート処理 ---

# 診断データを一時保存する場所
current_context = {} 

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    forecast = get_love_forecast()

    if request.method == 'POST':
        # 1. データ受け取り
        user_data = {
            'mbti': request.form.get('user_mbti'),
            'love_type': request.form.get('user_love_type')
        }
        partner_data = {
            'mbti': request.form.get('partner_mbti'),
            'love_type': request.form.get('partner_love_type')
        }

        # チャット用にデータを保存
        global current_context
        current_context = {
            'user_mbti': user_data['mbti'],
            'user_love_type': user_data['love_type'],
            'partner_mbti': partner_data['mbti'],
            'partner_love_type': partner_data['love_type']
        }

        # 2. プロンプト作成
        prompt = create_diagnosis_prompt(user_data, partner_data)

        # 3. AI診断
        ai_result_text = get_ai_diagnosis(prompt, user_data, partner_data)

        # 4. 🔥 ここで新しい計算ロジックを使う！
        user_stats = calculate_love_stats(user_data['love_type'])

        # 5. 結果表示
        return render_template('result.html', 
                               user_mbti=user_data['mbti'],
                               user_love_type=user_data['love_type'],
                               partner_mbti=partner_data['mbti'],
                               partner_love_type=partner_data['love_type'],
                               diagnosis_result=ai_result_text,
                               forecast=forecast,
                               chart_data=user_stats) # グラフデータを渡す

    return render_template('index.html', forecast=forecast)

# --- チャット機能 ---
chat_history = [{"role": "ai", "text": "よう！診断結果はどうだった？相談に乗るぞ！👍"}]

# app/routes/main.py の chat関数部分

@main_bp.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_msg = request.form.get('user_message')
        
        # 1. ユーザーのメッセージを履歴に追加
        chat_history.append({"role": "user", "text": user_msg})
        
        # 🔥 修正ポイント：メッセージ単体ではなく「chat_history（履歴全体）」を渡す！
        ai_msg = get_chat_response(chat_history, context=current_context)
        
        # 2. AIのメッセージを履歴に追加
        chat_history.append({"role": "ai", "text": ai_msg})
        
        return render_template('chat.html', messages=chat_history)
    
    return render_template('chat.html', messages=chat_history)
# --- 画像アップロード機能 ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files: return 'ファイルなし'
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename): return 'ファイルエラー'

        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.root_path, 'uploads', filename)
        file.save(save_path)

        ai_reply = """
        <h3>🧐 解析完了！</h3>
        <p>これは「駆け引き」の局面だな。焦らず以下の案で返信だ！</p>
        <div style="background:#e3f2fd; padding:15px; border-radius:10px;">
            <strong>案A：</strong>「りょ！ゆっくり休んでね💤」<br>
            <strong>案B：</strong>「OK！映画見てくる～🍿」
        </div>
        """
        return render_template('chat.html', messages=[
            {"role": "user", "text": "（画像を送信しました 📸）"},
            {"role": "ai", "text": ai_reply}
        ])
    return render_template('upload.html')