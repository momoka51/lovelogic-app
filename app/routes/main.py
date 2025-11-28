import os
import random
from datetime import datetime, timedelta # 🕒 日付操作用に追加
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, current_app
from app.logic.prompt_builder import create_diagnosis_prompt
from app.services.ai_service import get_ai_diagnosis, get_chat_response

main_bp = Blueprint('main', __name__)

# --- 📊 レーダーチャート計算ロジック ---
def calculate_love_stats(love_type):
    """ラブタイプからステータス(1~5)を算出"""
    stats = {"menhera": 3, "devotion": 3, "cheating": 3, "commu": 3, "psycho": 3}
    type_str = str(love_type).upper()

    if "F" in type_str: stats["devotion"] += 1; stats["commu"] -= 1
    elif "L" in type_str: stats["commu"] += 1; stats["psycho"] += 1

    if "C" in type_str: stats["menhera"] += 2; stats["devotion"] += 1
    elif "A" in type_str: stats["cheating"] += 1; stats["menhera"] -= 1

    if "P" in type_str: stats["menhera"] += 1; stats["cheating"] -= 1
    elif "R" in type_str: stats["cheating"] += 1; stats["psycho"] += 1

    if "E" in type_str: stats["cheating"] += 2; stats["psycho"] -= 1
    elif "O" in type_str: stats["commu"] += 2; stats["cheating"] -= 2

    raw_list = [stats["menhera"], stats["devotion"], stats["cheating"], stats["commu"], stats["psycho"]]
    return [max(1, min(5, x)) for x in raw_list]

# --- ☀️ 今日の恋愛天気予報（日替わり機能） ---
# --- ☀️ 今日の恋愛天気予報（全タイプ対応版） ---
def get_love_forecast():
    # 1. 日本時間（JST）の現在時刻を取得
    jst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = jst_now.strftime('%Y-%m-%d')

    # 2. 「今日の日付」を元に乱数生成器を作る
    rng = random.Random(today_str)

    weathers = [
        {"icon": "☀️", "status": "恋愛日和", "desc": "今日は攻めの姿勢でOK！気になるあの子に連絡してみよう。"},
        {"icon": "⛅", "status": "曇りのち晴れ", "desc": "午前中は様子見が吉。夕方以降にチャンス到来かも？"},
        {"icon": "☔", "status": "涙雨", "desc": "メンタルが不安定になりがち。今日は自分磨きに集中しよう。"},
        {"icon": "⚡", "status": "波乱の予感", "desc": "些細なことで喧嘩しそう。「余計な一言」に要注意！"},
        {"icon": "🌈", "status": "奇跡の予感", "desc": "まさかの再会や急展開があるかも！？身だしなみは完璧に。"},
    ]

    # 🔥 全16種類のラブタイプ
    all_love_types = [
        "忠犬ハチ公(FCPE)", "ボス猫(LCRO)", "隠れベイビー(LCRE)", "カリスマバランサー(LARE)",
        "憧れの先輩(LARO)", "主役タイプ(LCPO)", "ツンデレヤンキー(LCPE)", "ライオン(LAPE)",
        "パーフェクトカメレオン(LAPO)", "敏腕マネージャー(FARE)", "不思議生命体(FARO)", "恋愛モンスター(FCPO)",
        "ちゃっかりうさぎ(FCRE)", "ロマンスマジシャン(FCRO)", "デビル天使(FAPO)", "最後の恋人(FAPE)"
    ]

    # 🔥 全16種類のMBTI
    all_mbti_types = [
        "建築家(INTJ)", "論理学者(INTP)", "指揮官(ENTJ)", "討論者(ENTP)",
        "提唱者(INFJ)", "仲介者(INFP)", "主人公(ENFJ)", "広報運動家(ENFP)",
        "管理者(ISTJ)", "擁護者(ISFJ)", "幹部(ESTJ)", "領事官(ESFJ)",
        "巨匠(ISTP)", "冒険家(ISFP)", "起業家(ESTP)", "エンターテイナー(ESFP)"
    ]

    # 全部混ぜる！
    all_types = all_love_types + all_mbti_types
    
    # 3. 今日のラッキー＆注意タイプを選ぶ
    # rng.choice でランダムに選出
    lucky = rng.choice(all_types)
    caution = rng.choice(all_types)

    # もし同じのが選ばれたら、違うのになるまで選び直す
    while caution == lucky:
        caution = rng.choice(all_types)
    
    selected_weather = rng.choice(weathers)
    
    return {
        "icon": selected_weather["icon"], 
        "status": selected_weather["status"], 
        "desc": selected_weather["desc"],
        "lucky": lucky, 
        "caution": caution
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

        # 3. AI診断（本番AI）
        ai_result_text = get_ai_diagnosis(prompt, user_data, partner_data)

        # 4. グラフ用の数値を計算
        user_stats = calculate_love_stats(user_data['love_type'])

        # 5. 結果表示
        return render_template('result.html', 
                               user_mbti=user_data['mbti'],
                               user_love_type=user_data['love_type'],
                               partner_mbti=partner_data['mbti'],
                               partner_love_type=partner_data['love_type'],
                               diagnosis_result=ai_result_text,
                               forecast=forecast,
                               chart_data=user_stats)

    return render_template('index.html', forecast=forecast)

# --- チャット機能 ---
chat_history = [{"role": "ai", "text": "よう！診断結果はどうだった？相談に乗るぞ！👍"}]

@main_bp.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_msg = request.form.get('user_message')
        chat_history.append({"role": "user", "text": user_msg})
        
        # 履歴全体とコンテキストを渡す（修正済み）
        ai_msg = get_chat_response(chat_history, context=current_context)
        
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

        # ダミーの解析結果（実際はここもAI化可能）
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