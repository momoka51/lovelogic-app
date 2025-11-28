from flask import Flask

def create_app():
    # Flaskアプリのインスタンス作成
    app = Flask(__name__)

    # さっき作った「routes/main.py」を登録する
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app