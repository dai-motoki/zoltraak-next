import os
from rich.console import Console
from rich.prompt import Confirm

console = Console()

def create_additional_files():
    files = {
        'frontend-next/app/components/SideMenu.tsx': """
'use client'

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const menuItems = [
  { name: 'ホーム', path: '/' },
  { name: 'プロフィール', path: '/profile' },
  { name: '設定', path: '/settings' },
];

export default function SideMenu() {
  const pathname = usePathname();

  return (
    <nav className="bg-gray-800 text-white h-screen w-64 fixed left-0 top-0 p-5">
      <h2 className="text-2xl font-bold mb-5">タスク管理アプリ</h2>
      <ul>
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
    </nav>
  );
}
        """,
        'frontend-next/app/globals.css': """
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-100;
}
        """,
        'frontend-next/app/layout.tsx': """
import './globals.css'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import SideMenu from './components/SideMenu'

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
        <Providers>
          <div className="flex">
            <SideMenu />
            <main className="flex-grow ml-64 p-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
        """,
        'frontend-next/app/profile/page.tsx': """
'use client'

import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'
import { useEffect, useState } from 'react'

export default function Profile() {
  const session = useSession()
  const supabase = useSupabaseClient()
  const [loading, setLoading] = useState(true)
  const [username, setUsername] = useState(null)
  const [website, setWebsite] = useState(null)
  const [avatar_url, setAvatarUrl] = useState(null)

  useEffect(() => {
    getProfile()
  }, [session])

  async function getProfile() {
    try {
      setLoading(true)
      if (!session?.user) throw new Error('No user on the session!')

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
      alert('Error loading user data!')
      console.log(error)
    } finally {
      setLoading(false)
    }
  }

  async function updateProfile({ username, website, avatar_url }) {
    try {
      setLoading(true)
      if (!session?.user) throw new Error('No user on the session!')

      const updates = {
        id: session?.user.id,
        username,
        website,
        avatar_url,
        updated_at: new Date().toISOString(),
      }

      let { error } = await supabase.from('profiles').upsert(updates)
      if (error) throw error
      alert('Profile updated!')
    } catch (error) {
      alert('Error updating the data!')
      console.log(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="form-widget">
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="text" value={session?.user?.email} disabled />
      </div>
      <div>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          value={username || ''}
          onChange={(e) => setUsername(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="website">Website</label>
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
          {loading ? 'Loading ...' : 'Update'}
        </button>
      </div>

      <div>
        <button className="button block" onClick={() => supabase.auth.signOut()}>
          Sign Out
        </button>
      </div>
    </div>
  )
}
        """,
        'frontend-next/app/settings/page.tsx': """
'use client'

import { useState } from 'react'

export default function Settings() {
  const [notifications, setNotifications] = useState(true)
  const [theme, setTheme] = useState('light')

  return (
    <div className="max-w-md mx-auto bg-white shadow-lg rounded-lg p-6">
      <h1 className="text-2xl font-bold mb-4">設定</h1>
      
      <div className="mb-4">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={notifications}
            onChange={() => setNotifications(!notifications)}
            className="form-checkbox h-5 w-5 text-blue-600"
          />
          <span className="ml-2 text-gray-700">通知を受け取る</span>
        </label>
      </div>
      
      <div className="mb-4">
        <label className="block text-gray-700 mb-2">テーマ</label>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="form-select mt-1 block w-full"
        >
          <option value="light">ライト</option>
          <option value="dark">ダーク</option>
        </select>
      </div>
      
      <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        保存
      </button>
    </div>
  )
}
        """,
        'frontend-next/app/store/index.ts': """
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
        'frontend-next/app/store/tasksSlice.ts': """
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
        'frontend-next/app/providers.tsx': """
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
    }

    for file_path, content in files.items():
        create_file(file_path, content.strip())

def create_file(path, content):
    if not path:
        raise ValueError("ファイルパスが空です。有効なパスを指定してください。")
    
    directory = os.path.dirname(path)
    if (directory):
        os.makedirs(directory, exist_ok=True)
    
    if os.path.exists(path):
        should_overwrite = Confirm.ask(f"ファイル '{path}' は既に存在します。上書きしますか？")
        if not should_overwrite:
            console.print(f"[yellow]ファイル '{path}' はスキップされました。[/yellow]")
            return

    with open(path, 'w') as f:
        f.write(content)
    
    console.print(f"[green]ファイル '{path}' が正常に作成されました。[/green]")

if __name__ == "__main__":
    create_additional_files()
    console.print("[bold green]追加のファイルが正常に作成されました。[/bold green]")