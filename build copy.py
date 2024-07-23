import subprocess
import os
import sys
import json
import time
import shutil

def main():
    PROJECT_NAME = "frontend-next"
    USE_TYPESCRIPT = len(sys.argv) <= 1 or sys.argv[1].lower() != 'no'

    # プロジェクトディレクトリの準備
    if os.path.exists(PROJECT_NAME):
        print(f"{PROJECT_NAME}ディレクトリが既に存在します。削除します...")
        shutil.rmtree(PROJECT_NAME)

    # プロジェクトのセットアップ
    try:
        setup_project(PROJECT_NAME, USE_TYPESCRIPT)
    except Exception as e:
        print(f"プロジェクトのセットアップ中にエラーが発生しました: {e}")
        return

    # プロジェクトディレクトリの存在確認
    if not os.path.exists(PROJECT_NAME):
        print(f"{PROJECT_NAME}ディレクトリが作成されませんでした。")
        return

    # プロジェクトディレクトリに移動
    os.chdir(PROJECT_NAME)

    # プロジェクトファイルの作成
    create_project_files(PROJECT_NAME, USE_TYPESCRIPT)

    # package.jsonの更新
    update_package_json()

    # Supabaseのセットアップ
    supabase_url, supabase_anon_key = setup_supabase()

    # .env.localファイルの作成（Supabase情報がある場合）
    if supabase_url and supabase_anon_key:
        create_file('.env.local', f"""
NEXT_PUBLIC_SUPABASE_URL={supabase_url}
NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}
        """.strip())

    # Vercelへのデプロイ
    deploy_url = deploy_to_vercel(supabase_url, supabase_anon_key) if supabase_url and supabase_anon_key else None

    # README.mdの作成
    create_readme(PROJECT_NAME, deploy_url)

    # セットアップ完了メッセージの表示
    print_setup_complete_message(PROJECT_NAME, supabase_url, supabase_anon_key, deploy_url)

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
    
    print(f"ファイル '{path}' が正常に作成されました。")

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
    
    print("Next.jsプロジェクトを作成しています...")
    result = run_command(" ".join(create_next_app_command))
    if result.returncode != 0:
        raise Exception(f"Next.jsプロジェクトの作成に失敗しました: {result.stderr}")

    os.chdir(PROJECT_NAME)

    print("追加の依存関係をインストールしています...")
    result = run_command("npm install @reduxjs/toolkit react-redux @supabase/auth-helpers-nextjs @supabase/auth-helpers-react @supabase/supabase-js")
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
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold">Task Manager</h1>
      <LoginButton />
      <TaskList />
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
    return <div>Please log in to view and manage tasks.</div>
  }

  return (
    <div className="w-full max-w-md">
      <div className="mb-4">
        <input
          type="text"
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          placeholder="New task"
        />
        <button
          onClick={handleAddTask}
          className="mt-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
        >
          Add Task
        </button>
      </div>
      <ul>
        {tasks.map((task) => (
          <li key={task.id} className="mb-2 flex items-center">
            <input
              type="checkbox"
              checked={task.completed}
              onChange={() => dispatch(toggleTask(task.id))}
              className="mr-2"
            />
            <span className={task.completed ? 'line-through' : ''}>{task.title}</span>
            <button
              onClick={() => dispatch(removeTask(task.id))}
              className="ml-auto bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded focus:outline-none focus:shadow-outline"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
        """,
        f'app/components/LoginButton.{TSX_EXT}': """
'use client'

import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'

export default function LoginButton() {
  const session = useSession()
  const supabase = useSupabaseClient()

  async function handleSignIn() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
    })

    if (error) {
      console.error('Error signing in:', error)
    }
  }

  async function handleSignOut() {
    const { error } = await supabase.auth.signOut()

    if (error) {
      console.error('Error signing out:', error)
    }
  }

  return (
    <div>
      {session ? (
        <button onClick={handleSignOut} className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">
          Sign Out
        </button>
      ) : (
        <button onClick={handleSignIn} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Sign In with Google
        </button>
      )}
    </div>
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
  throw new Error('Supabase URLまたは匿名キーが設定されていません。')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
        """,
    }

    for file_path, content in files.items():
        create_file(file_path, content.strip())

def update_package_json():
    with open('package.json', 'r') as f:
        package_json = json.load(f)
    
    package_json['scripts']['lint'] = "next lint"
    
    with open('package.json', 'w') as f:
        json.dump(package_json, f, indent=2)

def setup_supabase():
    print("Supabaseプロジェクトの情報を入力してください")
    print("\nGoogle認証の設定手順:")
    print("1. Google Cloud Console (https://console.cloud.google.com/) にアクセスし、ログインします。")
    print("2. 新しいプロジェクトを作成します。")
    print("3. 左側のメニューから「APIとサービス」>「OAuth同意画面」を選択し、設定します。")
    print("4. 「APIとサービス」>「認証情報」から、「認証情報を作成」>「OAuthクライアントID」をクリックします。")
    print("5. アプリケーションの種類として「ウェブアプリケーション」を選択します。")
    print("6. 「承認済みのリダイレクトURI」に以下のURLを追加します:")
    print("   https://[YOUR_PROJECT_ID].supabase.co/auth/v1/callback")
    print("   （[YOUR_PROJECT_ID]は実際のSupabaseプロジェクトIDに置き換えてください）")
    print("7. 「作成」をクリックし、表示されるクライアントIDとクライアントシークレットをコピーします。")
    print("8. Supabaseダッシュボードの「認証」>「プロバイダー」>「Google」に移動します。")
    print("9. 「有効」をオンにし、コピーしたクライアントIDとクライアントシークレットを貼り付けます。")
    print("10. 「保存」をクリックします。")
    print("\n上記の手順を完了してから、以下の情報を入力してください。\n")

    supabase_url = input("Supabase URL を入力してください (例: https://xxxxxxxxxxxxxxxx.supabase.co): ")
    supabase_anon_key = input("Supabase 匿名キー (anon key) を入力してください: ")

    if not supabase_url.startswith("https://") or not supabase_url.endswith(".supabase.co"):
        print("無効なSupabase URLです。正しいURLを入力してください。")
        return None, None

    if not supabase_anon_key.startswith("eyJ"):
        print("無効な匿名キーです。正しいキーを入力してください。")
        return None, None

    print("\n重要: Supabaseダッシュボードで以下の設定を再確認してください：")
    print("1. 認証 > プロバイダー > Googleが有効になっていること")
    print("2. 認証 > URLの設定 > サイトURL、リダイレクトURLが正しく設定されていること")
    print("3. APIキーが正しいこと")
    print("4. Google Cloud ConsoleでリダイレクトURIが正しく設定されていること")

    return supabase_url, supabase_anon_key

def print_loading_animation(message, duration):
    animation = "|/-\\"
    idx = 0
    start_time = time.time()
    
    while time.time() - start_time < duration:
        print(f"\r{message} {animation[idx % len(animation)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    
    print("\r" + " " * (len(message) + 2), end="", flush=True)
    print("\r", end="", flush=True)

def deploy_to_vercel(supabase_url, supabase_anon_key):
    print("Vercelにデプロイしています...")
    try:
        os.environ['NEXT_PUBLIC_SUPABASE_URL'] = supabase_url
        os.environ['NEXT_PUBLIC_SUPABASE_ANON_KEY'] = supabase_anon_key

        print("TypeScriptの型チェックを実行しています...")
        print_loading_animation("型チェック中", 5)
        type_check_result = run_command("npx tsc --noEmit")
        if type_check_result.returncode != 0:
            print("型チェックに失敗しました。エラーを確認してください:")
            print(type_check_result.stderr)
            return None

        print("プロジェクトをビルドしています...")
        print_loading_animation("ビルド中", 10)
        build_result = run_command("npm run build")
        if build_result.returncode != 0:
            print("ビルドに失敗しました。エラーを確認してください:")
            print(build_result.stderr)
            return None

        print("Vercel CLIをインストールしています...")
        print_loading_animation("Vercel CLIインストール中", 5)
        run_command("npm install -g vercel")

        deploy_command = "vercel --confirm"
        deploy_command += f" --build-env NEXT_PUBLIC_SUPABASE_URL={supabase_url}"
        deploy_command += f" --build-env NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}"

        print("Vercelにデプロイしています...")
        print_loading_animation("デプロイ中", 30)
        result = run_command(deploy_command)
        
        deploy_url = result.stdout.strip().split('\n')[-1]
        return deploy_url
    except subprocess.CalledProcessError as e:
        print(f"Vercelへのデプロイ中にエラーが発生しました: {e}")
        return None

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
    print("プロジェクトのセットアップが完了しました。")
    if supabase_url and supabase_anon_key:
        print("Supabaseの設定が完了し、.env.localファイルに保存されました。")
    else:
        print("Supabaseの設定を手動で行ってください。")
    
    if deploy_url:
        print(f"プロジェクトがVercelにデプロイされました。以下のURLでアクセスできます：")
        print(deploy_url)
    else:
        print("Vercelへのデプロイに失敗しました。手動でデプロイを行ってください。")

    print("ローカルで開発サーバーを起動するには、以下のコマンドを実行してください：")
    print(f"cd {PROJECT_NAME}")
    print("npm run dev")

if __name__ == "__main__":
    main()