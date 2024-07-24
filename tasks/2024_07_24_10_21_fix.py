import subprocess
import os

def update_files():
    # app/page.tsxの更新
    page_content = """
import Link from 'next/link'
import LoginButton from './components/LoginButton'

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2 bg-gradient-to-r from-blue-400 to-purple-500">
      <div className="text-center bg-white p-8 rounded-lg shadow-2xl">
        <h1 className="text-4xl font-bold mb-4 text-gray-800">タスク管理アプリへようこそ</h1>
        <p className="text-xl mb-6 text-gray-600">効率的にタスクを管理し、生産性を向上させましょう。</p>
        <div className="space-y-4">
          <LoginButton />
          <Link href="/tasks">
            <span className="block bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition duration-300">
              タスク一覧へ
            </span>
          </Link>
        </div>
      </div>
    </div>
  )
}
    """.strip()

    with open('app/page.tsx', 'w') as f:
        f.write(page_content)

    # app/tasks/page.tsxの更新
    tasks_page_content = """
import TaskList from '../components/TaskList'
import LoginButton from '../components/LoginButton'

export default function Tasks() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-r from-blue-100 to-purple-100">
      <div className="bg-white shadow-2xl rounded-lg p-8 max-w-md w-full text-center">
        <h1 className="text-4xl font-bold mb-8 text-gray-800">タスク管理</h1>
        <div className="mb-8">
          <LoginButton />
        </div>
        <TaskList />
      </div>
    </main>
  )
}
    """.strip()

    with open('app/tasks/page.tsx', 'w') as f:
        f.write(tasks_page_content)

    print("ファイルが正常に更新されました。")

def run_next_dev():
    try:
        subprocess.run(["npm", "run", "dev"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"エラー: Next.js開発サーバーの起動に失敗しました。\n{e}")
    except FileNotFoundError:
        print("エラー: 'npm'コマンドが見つかりません。Node.jsがインストールされていることを確認してください。")

if __name__ == "__main__":
    update_files()
    run_next_dev()