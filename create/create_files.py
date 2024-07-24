import os
import asyncio
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from llms.anthropic_service import generate_text_anthropic

console = Console()

async def create_file(path, content):
    if not path:
        raise ValueError("ファイルパスが空です。有効なパスを指定してください。")
    
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    
    if os.path.exists(path):
        with open(path, 'r') as f:
            existing_content = f.read()
        
        if existing_content == content:
            console.print(f"[yellow]ファイル '{path}' は既に存在し、内容に変更はありません。[/yellow]")
        else:
            import difflib
            diff = list(difflib.unified_diff(
                existing_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile='既存',
                tofile='新規'
            ))
            
            # カラフルな差分表示
            table = Table(show_header=False, box=None)
            for line in diff:
                if line.startswith('+'):
                    table.add_row(Syntax(line, "diff", theme="ansi_dark", background_color="green"))
                elif line.startswith('-'):
                    table.add_row(Syntax(line, "diff", theme="ansi_dark", background_color="red"))
                else:
                    table.add_row(Syntax(line, "diff", theme="ansi_dark"))
            
            console.print(f"[yellow]ファイル '{path}' は既に存在します。差分:[/yellow]")
            console.print(table)
            
            # Claudeによる変更箇所の説明
            prompt = f"以下の差分を簡潔に説明してください:\n{''.join(diff)}"
            explanation = await generate_text_anthropic(prompt)
            console.print("[cyan]変更箇所の説明:[/cyan]")
            console.print(explanation["generated_text"])
            
            overwrite = input("ファイルを上書きしますか？ (y/n): ").lower() == 'y'
            if not overwrite:
                console.print(f"[yellow]ファイル '{path}' の作成をキャンセルしました。[/yellow]")
                return
    
    with open(path, 'w') as f:
        f.write(content)
    
    console.print(f"[green]ファイル '{path}' が正常に作成されました。[/green]")

# create_file関数を非同期で呼び出すためのヘルパー関数
def create_file_sync(path, content):
    asyncio.run(create_file(path, content))

# create_file関数を直接呼び出す場合は、非同期環境で実行する必要があります