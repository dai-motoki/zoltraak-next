import os
import subprocess

def create_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def create_nextjs_structure():
    base_dir = "my-nextjs-app"
    os.makedirs(base_dir, exist_ok=True)
    os.chdir(base_dir)

    # Create directory structure
    directories = [
        "app",
        "app/components",
        "app/dashboard",
        "app/dashboard/overview",
        "app/dashboard/analytics",
        "app/profile",
        "app/profile/[username]",
        "app/settings",
        "app/settings/account",
        "app/settings/notifications",
        "app/api",
        "public"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Create files with basic content
    files = {
        "app/layout.tsx": """
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
""",
        "app/page.tsx": "export default function Home() { return <h1>Welcome to Next.js!</h1> }",
        "app/globals.css": "body { font-family: sans-serif; }",
        "app/components/Sidebar.tsx": "export default function Sidebar() { return <nav>Sidebar</nav> }",
        "app/components/MainContent.tsx": "export default function MainContent() { return <main>Main Content</main> }",
        "app/dashboard/page.tsx": "export default function Dashboard() { return <h1>Dashboard</h1> }",
        "app/dashboard/overview/page.tsx": "export default function Overview() { return <h1>Dashboard Overview</h1> }",
        "app/dashboard/analytics/page.tsx": "export default function Analytics() { return <h1>Dashboard Analytics</h1> }",
        "app/profile/page.tsx": "export default function Profile() { return <h1>Profile</h1> }",
        "app/profile/[username]/page.tsx": "export default function UserProfile({ params }) { return <h1>Profile of {params.username}</h1> }",
        "app/settings/page.tsx": "export default function Settings() { return <h1>Settings</h1> }",
        "app/settings/account/page.tsx": "export default function AccountSettings() { return <h1>Account Settings</h1> }",
        "app/settings/notifications/page.tsx": "export default function NotificationSettings() { return <h1>Notification Settings</h1> }",
        "package.json": """{
  "name": "my-nextjs-app",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "13.4.19",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  }
}
""",
        "next.config.js": "/** @type {import('next').NextConfig} */\nconst nextConfig = {}\nmodule.exports = nextConfig"
    }

    for file_path, content in files.items():
        create_file(file_path, content)

    # Initialize git repository
    subprocess.run(["git", "init"])

    # Install dependencies
    subprocess.run(["npm", "install"])

    print("Next.js App Router structure created successfully!")

if __name__ == "__main__":
    create_nextjs_structure()