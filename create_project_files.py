import os
import shutil
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

console = Console()

def create_project_files(PROJECT_NAME, USE_TYPESCRIPT):
    FILE_EXT = 'ts' if USE_TYPESCRIPT else 'js'
    TSX_EXT = 'tsx' if USE_TYPESCRIPT else 'jsx'

    directories = [
        'app/components', 'app/store', 'app/utils', 'app/types',
        'app/features/auth', 'app/features/tasks', 'app/tasks'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    files = {
        '.gitignore': """
# 依存関係
/node_modules
/.pnp
.pnp.js

# テスト
/coverage

# Next.js
/.next/
/out/

# 本番環境
/build

# その他
.DS_Store
*.pem

# デバッグ
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# ローカル環境設定
.env*.local

# Vercel
.vercel

# TypeScript
*.tsbuildinfo
next-env.d.ts

# Supabase
.env.local
        """,
        f'app/layout.{TSX_EXT}': """
import './globals.css'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import SideMenu from './components/SideMenu'
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Task Manager',
  description: 'A simple task manager built with Next.js, Redux, and Supabase',
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createServerComponentClient({ cookies })
  const { data: { session } } = await supabase.auth.getSession()

  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="flex">
            {session && <SideMenu />}
            <main className={`flex-grow ${session ? 'ml-64' : ''} p-8`}>
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
        """,
        f'app/page.{TSX_EXT}': """
import Link from 'next/link'

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2">
      <h1 className="text-4xl font-bold mb-8">タスク管理アプリへようこそ</h1>
      <Link href="/tasks">
        <span className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          タスク一覧へ
        </span>
      </Link>
    </div>
  )
}
        """,
        f'app/tasks/page.{TSX_EXT}': """
import TaskList from '../components/TaskList'
import LoginButton from '../components/LoginButton'

export default function Tasks() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-r from-blue-100 to-purple-100">
      <div className="bg-white shadow-2xl rounded-lg p-8 max-w-md w-full">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">タスク管理</h1>
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
        f'app/components/SideMenu.{TSX_EXT}': """
'use client'

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'
import { useState } from 'react'

const menuItems = [
  { name: 'ホーム', path: '/' },
  { name: 'タスク', path: '/tasks' },
  { name: 'プロフィール', path: '/profile' },
];

export default function SideMenu() {
  const pathname = usePathname();
  const session = useSession()
  const supabase = useSupabaseClient()
  const [isLoading, setIsLoading] = useState(false)

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

  if (!session) {
    return null; // セッションがない場合は何も表示しない
  }

  return (
    <nav className="bg-gray-800 text-white h-screen w-64 fixed left-0 top-0 p-5 flex flex-col">
      <h2 className="text-2xl font-bold mb-5">タスク管理アプリ</h2>
      <ul className="flex-grow">
        {menuItems.map((item) => (
          <li key={item.path} className="mb-3">
            <Link href={item.path}>
              <span className={`block p-2 rounded ${
                pathname === item.path ? 'bg-blue-600' : 'hover:bg-gray-700'
              }`}>
                {item.name}
              </span>
            </Link>
          </li>
        ))}
      </ul>
      <button
        onClick={handleSignOut}
        className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded shadow-md transition duration-300 ease-in-out"
        disabled={isLoading}
      >
        {isLoading ? 'ログアウト中...' : 'ログアウト'}
      </button>
    </nav>
  );
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
        f'app/profile/page.{TSX_EXT}': """
'use client'

import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'
import { useEffect, useState } from 'react'

export default function Profile() {
  const session = useSession()
  const supabase = useSupabaseClient()
  const [loading, setLoading] = useState(true)
  const [username, setUsername] = useState<string | null>(null)
  const [website, setWebsite] = useState<string | null>(null)
  const [avatar_url, setAvatarUrl] = useState<string | null>(null)

  useEffect(() => {
    getProfile()
  }, [session])

  async function getProfile() {
    try {
      setLoading(true)
      if (!session?.user) throw new Error('ユーザーが見つかりません')

      let { data, error, status } = await supabase
        .from('profiles')
        .select(`username, website, avatar_url`)
        .eq('id', session?.user.id)
        .single()

      if (error && status !== 406) {
        throw error
      }

      if (data) {
        setUsername(data.username)
        setWebsite(data.website)
        setAvatarUrl(data.avatar_url)
      }
    } catch (error) {
      alert('エラーが発生しました。プロフィールの取得に失敗しました。')
    } finally {
      setLoading(false)
    }
  }

  async function updateProfile({ username, website, avatar_url }: { username: string | null, website: string | null, avatar_url: string | null }) {
    try {
      setLoading(true)
      if (!session?.user) throw new Error('ユーザーが見つかりません')

      const updates = {
        id: session?.user.id,
        username,
        website,
        avatar_url,
        updated_at: new Date().toISOString(),
      }

      let { error } = await supabase.from('profiles').upsert(updates)
      if (error) throw error
      alert('プロフィールが更新されました！')
    } catch (error) {
      alert('エラーが発生しました。プロフィールの更新に失敗しました。')
    } finally {
      setLoading(false)
    }
  }

  if (!session) {
    return <div>プロフィールを表示するにはログインしてください。</div>
  }

  return (
    <div className="form-widget">
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="text" value={session?.user?.email} disabled />
      </div>
      <div>
        <label htmlFor="username">ユーザー名</label>
        <input
          id="username"
          type="text"
          value={username || ''}
          onChange={(e) => setUsername(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="website">ウェブサイト</label>
        <input
          id="website"
          type="url"
          value={website || ''}
          onChange={(e) => setWebsite(e.target.value)}
        />
      </div>

      <div>
        <button
          className="button primary block"
          onClick={() => updateProfile({ username, website, avatar_url })}
          disabled={loading}
        >
          {loading ? '読み込み中...' : 'プロフィールを更新'}
        </button>
      </div>
    </div>
  )
}
        """,
    }

    for file_path, content in files.items():
        create_file(file_path, content.strip())

    # .env.localファイルをプロジェクトディレクトリにコピー
    if os.path.exists('../.env.local'):
        shutil.copy('../.env.local', '.env.local')
        console.print("[green].env.localファイルをプロジェクトディレクトリにコピーしました。[/green]")
        console.print("[green]新しい.env.localファイルをコピーしました。[/green]")
    else:
        # .env.localファイルが存在しない場合、新しく作成
        env_content = f"""
NEXT_PUBLIC_SUPABASE_URL={supabase_url}
NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}
        """.strip()
        create_file('.env.local', env_content)
        console.print("[green]新しい.env.localファイルを作成しました。[/green]")

def create_file(path, content):
    if not path:
        raise ValueError("ファイルパスが空です。有効なパスを指定してください。")
    
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    
    with open(path, 'w') as f:
        f.write(content)
    
    console.print(f"[green]ファイル '{path}' が正常に作成されました。[/green]")