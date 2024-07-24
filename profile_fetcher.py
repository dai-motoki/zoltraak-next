import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env.localファイルから環境変数を読み込む
load_dotenv('.env.local')

# Supabaseの接続情報を環境変数から取得
url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Supabaseクライアントの初期化
supabase: Client = create_client(url, key)

def fetch_profile():
    try:
        # プロフィールを取得
        response = supabase.table("profiles").select("*").execute()
        
        # エラーチェック
        if hasattr(response, 'error') and response.error is not None:
            raise Exception(response.error.message)
        
        # データが存在するか確認
        if len(response.data) == 0:
            print("プロフィールが見つかりません。")
        else:
            # 最初のプロフィールを表示
            profile = response.data[0]
            print("プロフィール情報:")
            print(f"ID: {profile.get('id')}")
            print(f"ユーザーID: {profile.get('user_id')}")
            print(f"Bio: {profile.get('bio')}")
            print(f"作成日時: {profile.get('created_at')}")
            print(f"更新日時: {profile.get('updated_at')}")
    
    except Exception as e:
        print(f"エラー: プロフィールの取得に失敗しました - {str(e)}")

if __name__ == "__main__":
    fetch_profile()