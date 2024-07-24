import re
import subprocess
import os
import sys
import json
import time
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint
import requests
from dotenv import load_dotenv
import asyncio


from create.create_files import create_file
from tasks.create_project_files import create_project_files
from tasks.build import (
    deploy_to_vercel,
    setup_supabase,
    update_package_json,
    update_supabase_settings,
    get_project_info,
    setup_project,
    process_env_file,
    load_env_variables,
    create_env_local_file,
    print_setup_complete_message,
    generate_file_tree,
    create_readme,
    run_local_dev
)

console = Console()
# グローバル変数
supabase_url = None
supabase_anon_key = None


async def main():
    # PROJECT_NAME = input("プロジェクト名を入力してください: ")
    PROJECT_NAME = "frontend-next"
    USE_TYPESCRIPT = len(sys.argv) <= 1 or sys.argv[1].lower() != 'no'


    # 環境変数の読み込み
    load_env_variables()
    # プロジェクト情報の取得
    project_id, vercel_project_name = get_project_info(PROJECT_NAME)

    # プロジェクトディレクトリの準備
    if os.path.exists(PROJECT_NAME):
        console.print(f"[yellow]{PROJECT_NAME}ディレクトリが既に存在します。削除します...[/yellow]")
        shutil.rmtree(PROJECT_NAME)


    # プロジェクトのセットアップ
    try:
        setup_project(PROJECT_NAME, USE_TYPESCRIPT)
    except Exception as e:
        console.print(f"[bold red]プロジェクトのセットアップ中にエラーが発生しました: {e}[/bold red]")
        return

    # プロジェクトディレクトリの存在確認
    if not os.path.exists(PROJECT_NAME):
        console.print(f"[bold red]{PROJECT_NAME}ディレクトリが作成されませんでした。[/bold red]")
        return

    # プロジェクトディレクトリに移動
    os.chdir(PROJECT_NAME)

    # プロジェクトファイルの作成
    create_project_files(PROJECT_NAME, USE_TYPESCRIPT)

    # package.jsonの更新
    update_package_json()

    # ローカル開発サーバーの起動
    console.print(Panel("[bold yellow]ステップ 1: ローカル開発サーバーを起動します[/bold yellow]"))
    # dev_process = await run_local_dev(PROJECT_NAME)

    console.print(Panel(
        "[bold green]ステップ 2: プロジェクトディレクトリに移動し、開発サーバーを起動してください。\n"
        "以下のコマンドを実行してください：\n"
        f"cd {PROJECT_NAME}\n"
        "npm run dev\n\n"
        "起動後、以下のURLでアクセスできます：\n"
        "http://localhost:3000\n\n"
        "サーバーを停止するには、Ctrl+C を押してください。[/bold green]"
    ))

    # Supabaseのセットアップ
    supabase_url, supabase_anon_key, callback_url = setup_supabase(project_id)

    # .env.localファイルの作成（Supabase情報がある場合）
    if supabase_url and supabase_anon_key and callback_url:
        # .env.localファイルを非同期で作成
        await create_file('.env.local', f"""
NEXT_PUBLIC_SUPABASE_URL={supabase_url}
NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}
NEXT_PUBLIC_SUPABASE_CALLBACK_URL={callback_url}
        """.strip())
        console.print("[green].env.localファイルが正常に作成されました。[/green]")
    else:
        console.print("[yellow]Supabase情報が不完全なため、.env.localファイルは作成されませんでした。[/yellow]")

    # Vercelへのデプロイ
    deploy_url = deploy_to_vercel(supabase_url, supabase_anon_key, vercel_project_name) if supabase_url and supabase_anon_key else None

    if deploy_url:
        process_env_file('.env.local', deploy_url)

    # README.mdの作成
    create_readme(PROJECT_NAME, deploy_url)

    # セットアップ完了メッセージの表示
    print_setup_complete_message(PROJECT_NAME, supabase_url, supabase_anon_key, deploy_url)



if __name__ == "__main__":
    asyncio.run(main())