from app import create_app

# アプリを作成
app = create_app()

if __name__ == "__main__":
    # デバッグモードONで起動（エラーが見やすくなり、保存すると自動で再起動する）
    app.run(debug=True)