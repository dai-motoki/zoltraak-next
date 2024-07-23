import re
import subprocess
import os
import sys
import json
import time
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
import requests
from dotenv import load_dotenv
import asyncio

console = Console()

# グローバル変数
supabase_url = None
supabase_anon_key = None

def load_env_variables():
    global supabase_url, supabase_anon_key
    # .env.localファイルが存在する場合、それを読み込む
    if os.path.exists('.env.local'):
        load_dotenv('.env.local')
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        supabase_anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        console.print("[green].env.localファイルから環境変数を読み込みました。[/green]")
    else:
        console.print("[yellow].env.localファイルが見つかりません。手動で入力が必要です。[/yellow]")

async def run_dev_server(project_dir):
    os.chdir(project_dir)
    console.print(Panel("[bold cyan]ステップ 1: 開発サーバーを起動しています[/bold cyan]"))
    process = await asyncio.create_subprocess_shell(
        "npm run dev",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return process

async def wait_for_server(url, timeout=60):
    console.print("[cyan]ステップ 2: サーバーの起動を確認しています...[/cyan]")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        await asyncio.sleep(1)
    return False

async def run_local_dev(PROJECT_NAME):
    dev_process = await run_dev_server(PROJECT_NAME)
    server_ready = await wait_for_server("http://localhost:3000")
    if server_ready:
        console.print("[green]ステップ 3: 開発サーバーが正常に起動しました。[/green]")
    else:
        console.print("[yellow]ステップ 3: 開発サーバーの起動を確認できませんでした。手動で確認してください。[/yellow]")
    return dev_process

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
    dev_process = await run_local_dev(PROJECT_NAME)

    console.print(Panel(
        "[bold green]ステップ 2: 開発サーバーが起動しました。\n"
        "以下のURLでアクセスできます：\n"
        "http://localhost:3000\n\n"
        "サーバーを停止するには、Ctrl+C を押してください。[/bold green]"
    ))

    # Supabaseのセットアップ
    supabase_url, supabase_anon_key, callback_url = setup_supabase(project_id)

    # .env.localファイルの作成（Supabase情報がある場合）
    if supabase_url and supabase_anon_key and callback_url:
        create_file('.env.local', f"""
NEXT_PUBLIC_SUPABASE_URL={supabase_url}
NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}
NEXT_PUBLIC_SUPABASE_CALLBACK_URL={callback_url}
        """.strip())

    # Vercelへのデプロイ
    deploy_url = deploy_to_vercel(supabase_url, supabase_anon_key, vercel_project_name) if supabase_url and supabase_anon_key else None

    if deploy_url:
        # .env.localファイルから情報を読み込む
        with open('.env.local', 'r') as env_file:
            env_content = env_file.read()
        
        # URLを抽出
        supabase_url = re.search(r'NEXT_PUBLIC_SUPABASE_URL=(.*)', env_content).group(1)
        
        # プロジェクトIDを抽出
        supabase_project_id = supabase_url.split('//')[1].split('.')[0]
        
        # APIキーを抽出
        supabase_api_key = re.search(r'NEXT_PUBLIC_SUPABASE_ANON_KEY=(.*)', env_content).group(1)
        
        console.print(f"[green]SupabaseプロジェクトID: {supabase_project_id}[/green]")
        console.print(f"[green]Supabase管理APIキー: {supabase_api_key}[/green]")
        callback_url = f"{deploy_url}/auth/callback"
        update_supabase_settings(supabase_project_id, supabase_api_key, deploy_url, callback_url)

        console.print("\n[bold cyan]Google Cloud Consoleでの設定:[/bold cyan]")
        console.print(f"[cyan]Google Cloud Consoleで、承認済みのリダイレクトURIに {callback_url} を追加してください。[/cyan]")

    # README.mdの作成
    create_readme(PROJECT_NAME, deploy_url)

    # セットアップ完了メッセージの表示
    print_setup_complete_message(PROJECT_NAME, supabase_url, supabase_anon_key, deploy_url)

    # ユーザーが Ctrl+C を押すまで待機
    try:
        await dev_process.communicate()
    except asyncio.CancelledError:
        console.print(Panel("[bold red]ステップ 3: 開発サーバーを停止しています...[/bold red]"))
        dev_process.terminate()
        await dev_process.wait()
        console.print(Panel("[bold green]ステップ 4: 開発サーバーが正常に停止しました。[/bold green]"))

def run_command(command, shell=True):
    return subprocess.run(command, shell=shell, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def create_file(path, content):
    if not path:
        raise ValueError("ファイルパスが空です。有効なパスを指定してください。")
    
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    
    with open(path, 'w') as f:
        f.write(content)
    
    console.print(f"[green]ファイル '{path}' が正常に作成されました。[/green]")

def setup_project(PROJECT_NAME, USE_TYPESCRIPT):
    FILE_EXT = 'ts' if USE_TYPESCRIPT else 'js'
    TSX_EXT = 'tsx' if USE_TYPESCRIPT else 'jsx'

    create_next_app_command = [
        "npx", "create-next-app@latest", PROJECT_NAME,
        "--eslint", "--tailwind", "--app", "--no-src-dir",
        "--import-alias", "@/*"
    ]
    if USE_TYPESCRIPT:
        create_next_app_command.append("--typescript")
    else:
        create_next_app_command.append("--js")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task1 = progress.add_task("[cyan]Next.jsプロジェクトを作成しています...", total=None)
        result = run_command(" ".join(create_next_app_command))
        progress.update(task1, completed=True)
        if result.returncode != 0:
            raise Exception(f"Next.jsプジェクトの作成に失敗しました: {result.stderr}")

    os.chdir(PROJECT_NAME)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task2 = progress.add_task("[cyan]追加の依存関係をインストールしています...", total=None)
        result = run_command("npm install @reduxjs/toolkit react-redux @supabase/auth-helpers-nextjs @supabase/auth-helpers-react @supabase/supabase-js framer-motion")
        progress.update(task2, completed=True)
        if result.returncode != 0:
            raise Exception(f"依存関係のインストールに失敗しました: {result.stderr}")

    os.chdir('..')  # 親ディレクトリに戻る

def create_project_files(PROJECT_NAME, USE_TYPESCRIPT):
    FILE_EXT = 'ts' if USE_TYPESCRIPT else 'js'
    TSX_EXT = 'tsx' if USE_TYPESCRIPT else 'jsx'

    directories = [
        'app/components', 'app/store', 'app/utils', 'app/types',
        'app/features/auth', 'app/features/tasks'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    files = {
        f'app/layout.{TSX_EXT}': """
import './globals.css'
import { Inter } from 'next/font/google'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Task Manager',
  description: 'A simple task manager built with Next.js, Redux, and Supabase',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
        """,
        f'app/page.{TSX_EXT}': """
import TaskList from './components/TaskList'
import LoginButton from './components/LoginButton'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-r from-blue-100 to-purple-100">
      <div className="bg-white shadow-2xl rounded-lg p-8 max-w-md w-full">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">タスク管理アプリ</h1>
        <div className="mb-8 flex justify-center">
          <LoginButton />
        </div>
        <TaskList />
      </div>
    </main>
  )
}
        """,
        f'app/providers.{TSX_EXT}': """
'use client'

import { Provider } from 'react-redux'
import { store } from './store'
import { createBrowserSupabaseClient } from '@supabase/auth-helpers-nextjs'
import { SessionContextProvider } from '@supabase/auth-helpers-react'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [supabaseClient] = useState(() => createBrowserSupabaseClient())

  return (
    <SessionContextProvider supabaseClient={supabaseClient}>
      <Provider store={store}>
        {children}
      </Provider>
    </SessionContextProvider>
  )
}
        """,
        f'app/components/TaskList.{TSX_EXT}': """
'use client'

import { useSelector, useDispatch } from 'react-redux'
import { addTask, toggleTask, removeTask } from '../store/tasksSlice'
import { useState } from 'react'
import { RootState, AppDispatch } from '../store'
import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function TaskList() {
  const tasks = useSelector((state: RootState) => state.tasks)
  const dispatch = useDispatch<AppDispatch>()
  const [newTask, setNewTask] = useState('')
  const session = useSession()
  const supabase = useSupabaseClient()

  const handleAddTask = () => {
    if (newTask.trim()) {
      dispatch(addTask({ title: newTask }))
      setNewTask('')
    }
  }

  if (!session) {
    return <div className="text-center text-gray-600">タスクを表示・管理するにはログインしてください。</div>
  }

  return (
    <div className="w-full max-w-md bg-white shadow-lg rounded-lg p-6">
      <div className="mb-4">
        <input
          type="text"
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          placeholder="新しいタスク"
        />
        <button
          onClick={handleAddTask}
          className="mt-2 w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-300 ease-in-out transform hover:scale-105"
        >
          タスクを追加
        </button>
      </div>
      <AnimatePresence>
        {tasks.map((task) => (
          <motion.div
            key={task.id}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="mb-2 flex items-center bg-gray-100 p-3 rounded-lg"
          >
            <input
              type="checkbox"
              checked={task.completed}
              onChange={() => dispatch(toggleTask(task.id))}
              className="mr-2 form-checkbox h-5 w-5 text-blue-600"
            />
            <span className={`flex-grow ${task.completed ? 'line-through text-gray-500' : 'text-gray-800'}`}>
              {task.title}
            </span>
            <button
              onClick={() => dispatch(removeTask(task.id))}
              className="ml-2 bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded focus:outline-none focus:shadow-outline transition duration-300 ease-in-out"
            >
              削除
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
        """,
        f'app/components/LoginButton.{TSX_EXT}': """
'use client'

import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'
import { useState } from 'react'
import { motion } from 'framer-motion'

export default function LoginButton() {
  const session = useSession()
  const supabase = useSupabaseClient()
  const [isLoading, setIsLoading] = useState(false)

  async function handleSignIn() {
    setIsLoading(true)
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })

      if (error) {
        console.error('ログインエラー:', error)
        alert(`ログインエラー: ${error.message}`)
      }
    } catch (error) {
      console.error('予期せぬエラー:', error)
      alert('予期せぬエラーが発生しました。コンソールを確認してください。')
    }
    // ログイン処理が完了しても、リダイレクトされるまでローディング状態を維持
  }

  async function handleSignOut() {
    setIsLoading(true)
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('ログアウトエラー:', error)
        alert(`ログアウトエラー: ${error.message}`)
      }
    } catch (error) {
      console.error('予期せぬエラー:', error)
      alert('予期せぬエラーが発生しました。コンソールを確認してください。')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {session ? (
        <button
          onClick={handleSignOut}
          className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded shadow-md transition duration-300 ease-in-out flex items-center"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              ログアウト中...
            </>
          ) : (
            'ログアウト'
          )}
        </button>
      ) : (
        <button
          onClick={handleSignIn}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow-md transition duration-300 ease-in-out flex items-center"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              ログイン中...
            </>
          ) : (
            <>
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path fill="#fff" d="M12.24 10.285V14.4h6.806c-.275 1.765-2.056 5.174-6.806 5.174-4.095 0-7.439-3.389-7.439-7.574s3.345-7.574 7.439-7.574c2.33 0 3.891.989 4.785 1.849l3.254-3.138C18.189 1.186 15.479 0 12.24 0c-6.635 0-12 5.365-12 12s5.365 12 12 12c6.926 0 11.52-4.869 11.52-11.726 0-.788-.085-1.39-.189-1.989H12.24z"/>
              </svg>
              Googleでログイン
            </>
          )}
        </button>
      )}
    </motion.div>
  )
}
        """,
        f'app/store/index.{FILE_EXT}': """
import { configureStore } from '@reduxjs/toolkit'
import tasksReducer from './tasksSlice'

export const store = configureStore({
  reducer: {
    tasks: tasksReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
        """,
        f'app/store/tasksSlice.{FILE_EXT}': """
import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Task {
  id: number
  title: string
  completed: boolean
}

const initialState: Task[] = []

let nextId = 1

const tasksSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    addTask: (state, action: PayloadAction<{ title: string }>) => {
      state.push({ id: nextId++, title: action.payload.title, completed: false })
    },
    toggleTask: (state, action: PayloadAction<number>) => {
      const task = state.find(task => task.id === action.payload)
      if (task) {
        task.completed = !task.completed
      }
    },
    removeTask: (state, action: PayloadAction<number>) => {
      return state.filter(task => task.id !== action.payload)
    },
  },
})

export const { addTask, toggleTask, removeTask } = tasksSlice.actions
export default tasksSlice.reducer
        """,
        f'app/utils/supabase.{FILE_EXT}': """
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Supabase URLまたは匿名キーが設定されていせん。')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
        """,
        f'app/auth/callback/route.{FILE_EXT}': """
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const supabase = createRouteHandlerClient({ cookies })
    await supabase.auth.exchangeCodeForSession(code)
  }

  // URL to redirect to after sign in process completes
  return NextResponse.redirect(requestUrl.origin)
}
        """,
    }

    for file_path, content in files.items():
        create_file(file_path, content.strip())

    # .env.localファイルをプロジェクトディレクトリにコピー
    if os.path.exists('.env.local'):
        shutil.copy('.env.local', os.path.join(PROJECT_NAME, '.env.local'))
        console.print("[green].env.localファイルをプロジェクトディレクトリにコピーしました。[/green]")
    else:
        # .env.localファイルが存在しない場合、新しく作成
        env_content = f"""
NEXT_PUBLIC_SUPABASE_URL={supabase_url}
NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}
        """.strip()
        create_file(os.path.join(PROJECT_NAME, '.env.local'), env_content)
        console.print("[green]新しい.env.localファイルを作成しました。[/green]")

def update_package_json():
    with open('package.json', 'r') as f:
        package_json = json.load(f)
    
    package_json['scripts']['lint'] = "next lint"
    package_json['dependencies']['@supabase/auth-helpers-nextjs'] = "^0.7.0"
    package_json['dependencies']['framer-motion'] = "^10.12.16"
    package_json['dependencies']['@reduxjs/toolkit'] = "^1.9.5"
    package_json['dependencies']['react-redux'] = "^8.1.1"
    
    with open('package.json', 'w') as f:
        json.dump(package_json, f, indent=2)

def get_project_info(PROJECT_NAME):
    console.print(Panel(f"[bold cyan]プロジェクト '{PROJECT_NAME}' の情報[/bold cyan]"))
    
    project_id = PROJECT_NAME
    vercel_project_name = PROJECT_NAME
    
    return project_id, vercel_project_name

def setup_supabase(project_id):
    global supabase_url, supabase_anon_key
    
    if not supabase_url or not supabase_anon_key:
        console.print(Panel(f"[bold cyan]Supabaseプロジェクト '{project_id}' の情報を入力してください[/bold cyan]"))
        console.print("\n[bold cyan]Google認証の設定手順:[/bold cyan]")
        console.print("[cyan]1. Google Cloud Console (https://console.cloud.google.com/) にアクセスし、ログインします。[/cyan]")
        console.print("[cyan]2. 新しいプロジェクトを作成します。[/cyan]")
        console.print("[cyan]3. 左側のメニューから「APIとサービス」>「OAuth同意画面」を選択し、設定します。[/cyan]")
        console.print("[cyan]4. APIとサービス」>「認証情報」から「認��情報を作成>「OAuthクライアントID」をクリックします。[/cyan]")
        console.print("[cyan]5. アプリケーションの種類として「ウェブアプリケーション」を選択します。[/cyan]")
        console.print("[cyan]6. 「承認済みのリダイレクトURI」に以下のURLを追加します:[/cyan]")
        console.print(f"[cyan]   https://{project_id}.supabase.co/auth/v1/callback[/cyan]")
        console.print("[cyan]7. 「作成」をクリックし、表示されるクライアントIDとクライアントシークレットをコピーします。[/cyan]")
        console.print("[cyan]8. Supabaseダッシュボードの「認証」>プロバイダー」>「Google」に移動します。[/cyan]")
        console.print("[cyan]9. 「有効」をオンにし、コピーしたクライアントIDとクライアントシークレットを貼り付けます。[/cyan]")
        console.print("[cyan]10. 「保存」をクリックします。[/cyan]")
        console.print("\n[bold cyan]上記の手順を完了してから、以下の情報を入力してください。\n[/bold cyan]")

        while True:
            supabase_url = input(f"Supabase URL を入力してください (例: https://{project_id}.supabase.co): ")
            if supabase_url.startswith("https://") and supabase_url.endswith(".supabase.co"):
                break
            console.print("[bold red]無効なSupabase URLです。正しいURLを入力してください。[/bold red]")

        while True:
            supabase_anon_key = input("Supabase 匿名キー (anon key) を入力してください: ")
            if supabase_anon_key.startswith("eyJ"):
                break
            console.print("[bold red]無効な匿名キーです。正しいキーを入力してください。[/bold red]")

    callback_url = f"{supabase_url}/auth/v1/callback"

    console.print("\n[bold cyan]重要: Supabaseダッシュボードで以下の設定を再確認してください：[/bold cyan]")
    console.print(f"[cyan]1. 認証 > プロバイダー > Googleが有効になっていると（https://supabase.com/dashboard/project/{project_id}/auth/providers）[/cyan]")
    console.print(f"[cyan]2. 認証 > URLの設定 > サイトURL が正しく設定されていること（https://supabase.com/dashboard/project/{project_id}/auth/url-configuration）[/cyan]")
    console.print(f"[cyan]3. APIキーが正しいこと（https://supabase.com/dashboard/project/{project_id}/settings/api）[/cyan]")
    console.print(f"[cyan]4. Google Cloud ConsoleでリダイレクトURIに {callback_url} が設定されていること（https://console.cloud.google.com/apis/credentials）[/cyan]")

    console.print("\n[bold red]意: Vercelにデプロイ後、以の設定を必ず行ってください：[/bold red]")
    console.print("[red]1. Supabaseダッシュボード > 認証 > URLの設定 > サイトURL: Vercelのデプロイ先URLを設定（https://supabase.com/dashboard/project/[YOUR_PROJECT_ID]/auth/url-configuration）[/red]")
    console.print("[red]2. Supabaseダッシュボード > 認証 > URLの設定 > リダイレクトURL: Vercelのデプロイ先URLに /auth/callback を追加（https://supabase.com/dashboard/project/[YOUR_PROJECT_ID]/auth/url-configuration）[/red]")
    console.print("[red]3. Google Cloud Console > 承認済みのリダイレクトURI: Vercelのデプロイ先URLに /auth/callback を追加（https://console.cloud.google.com/apis/credentials）[/red]")
    console.print("[red]これらの設定を行わないと、本番環境でのGoogle認証が正常に機能しない可能性があります[/red]")

    return supabase_url, supabase_anon_key, callback_url

def print_loading_animation(message, duration):
    with Progress() as progress:
        task = progress.add_task(f"[cyan]{message}", total=100)
        while not progress.finished:
            progress.update(task, advance=1)
            time.sleep(duration / 100)

def deploy_to_vercel(supabase_url, supabase_anon_key, vercel_project_name):
    console.print(Panel("[bold green]Vercelにデプロイしています...[/bold green]"))
    try:
        os.environ['NEXT_PUBLIC_SUPABASE_URL'] = supabase_url
        os.environ['NEXT_PUBLIC_SUPABASE_ANON_KEY'] = supabase_anon_key

        console.print("[cyan]TypeScriptの型チェックを実行しています...[/cyan]")
        print_loading_animation("", 5)
        type_check_result = run_command("npx tsc --noEmit")
        if type_check_result.returncode != 0:
            console.print("[bold red]型チェックに失敗しました。エラーを確認してください:[/bold red]")
            console.print(type_check_result.stderr)
            return None

        console.print("[cyan]プロジェクトをビルドしています...[/cyan]")
        print_loading_animation("", 20)
        build_result = run_command("npm run build")
        if build_result.returncode != 0:
            console.print("[bold red]ビルドに失敗しました。エラーを確認してください:[/bold red]")
            console.print(build_result.stderr)
            return None

        console.print("[cyan]Vercel CLIをインストールしています...[/cyan]")
        print_loading_animation("", 5)
        run_command("npm install vercel")

        deploy_command = f"vercel --name {vercel_project_name} --confirm"
        deploy_command += f" --build-env NEXT_PUBLIC_SUPABASE_URL={supabase_url}"
        deploy_command += f" --build-env NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}"

        console.print("[cyan]Vercelにデプロイしています...[/cyan]")
        print_loading_animation("", 180)
        result = run_command(deploy_command)
        
        deploy_url = result.stdout.strip().split('\n')[-1]
        return deploy_url
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Vercelへのデプロイ中にエラが発生しました: {e}[/bold red]")
        return None

def update_supabase_settings(project_id, api_key, site_url, callback_url):
    # Supabase管理APIのエンドポイント
    api_url = f"https://api.supabase.com/v1/projects/{project_id}/config/auth"

    # リクエストヘッダー
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 更新するデータ
    data = {
        "site_url": site_url,
        "additional_redirect_urls": [callback_url]
    }

    try:
        # PATCHリクエストを送信
        response = requests.patch(api_url, headers=headers, json=data)
        response.raise_for_status()
        console.print("[green]Supabaseの設定が正常に更新されました。[/green]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Supabaseの設定更新中にエラーが発生しました: {e}[/bold red]")

def generate_file_tree(startpath):
    tree = []
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree.append('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            tree.append('{}{}'.format(subindent, f))
    return '\n'.join(tree)

def create_readme(PROJECT_NAME, deploy_url):
    readme_content = f"""
# Task Manager

This is a simple task manager application built with Next.js, Redux, and Supabase, featuring Google authentication.

## Project Structure

```
{generate_file_tree('.')}
```

## Getting Started

1. Clone this repository
2. Install dependencies:
   ```
   npm install
   ```
3. Set up your Supabase project:
   - Create a new project on Supabase
   - Enable Google Authentication in the Auth settings
   - Update the `.env.local` file with your Supabase URL and anon key
4. Run the development server:
   ```
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Features

- Google Authentication
- Add new tasks
- Mark tasks as completed
- Delete tasks
- State management with Redux
- Styling with Tailwind CSS

## Deployment

This project is automatically deployed to Vercel. You can view the live version at:
{deploy_url if deploy_url else "[Deployment URL will be available after manual deploy]"}

## Learn More

To learn more about the technologies used in this project, check out the following resources:

- [Next.js Documentation](https://nextjs.org/docs)
- [Redux Toolkit](https://redux-toolkit.js.org/)
- [Supabase](https://supabase.io/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Supabase Auth Helpers](https://supabase.com/docs/guides/auth/auth-helpers/nextjs)

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
    """

    create_file('README.md', readme_content.strip())

def print_setup_complete_message(PROJECT_NAME, supabase_url, supabase_anon_key, deploy_url):
    console.print(Panel("[bold green]プロジェクトのセットアップが完了しました。[/bold green]"))
    if supabase_url and supabase_anon_key:
        console.print("[cyan]Supabaseの設定が完了し、.env.localファイルに保存されました。[/cyan]")
    else:
        console.print("[yellow]Supabaseの設定を手動でってください。[/yellow]")
    
    if deploy_url:
        console.print(f"[green]プロジェクトがVercelにデプロイされました。以下のURLでアクセスできます：[/green]")
        console.print(f"[link={deploy_url}]{deploy_url}[/link]")
        console.print("\n[bold red]重要: Vercelデプロイ後の設定を忘れずに行ってください：[/bold red]")
        console.print("[red]1. SupabaseダッシュボードでサイトURLとリダイレクトURLを更新[/red]")
        console.print("[red]2. Google Cloud ConsoleでリダイレクトURIを更新[/red]")
        console.print("[red]詳細は上記の注意事項を参照してください。[/red]")
    else:
        console.print("[yellow]Vercelへのデプロイに失敗しました。手動でデプロイを行ってください。[/yellow]")

    console.print("\n[bold cyan]ローカルで開発サーバーを起動するには、以下のコマンドを実行してください：[/bold cyan]")
    console.print(f"[green]cd {PROJECT_NAME}[/green]")
    console.print("[green]npm run dev[/green]")

if __name__ == "__main__":
    asyncio.run(main())