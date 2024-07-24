# タスクマネージャー

これはNext.js、Redux、Supabaseを使用して構築されたシンプルなタスク管理アプリケーションで、Google認証機能を備えています。

## 始め方

1. このリポジトリをクローンします
git clone https://github.com/dai-motoki/zoltraak-next.git

2. 必要なパッケージをインストールします：
    cd zoltraak-next
   pip install -r requirements.txt

3. 環境変数を設定します：
   export ANTHROPIC_API_KEY=sk-ant-aaaaa

4. ビルドスクリプトを実行します：
   python build.py


## 機能

- Google認証
- 新しいタスクの追加
- タスクの完了マーク
- タスクの削除
- Reduxを使用した状態管理
- Tailwind CSSによるスタイリング

## デプロイ

このプロジェクトは自動的にVercelにデプロイされます。ライブバージョンは以下のURLで確認できます：
（デプロイURLをここに記載）

## もっと学ぶ

このプロジェクトで使用されている技術についてもっと学ぶには、以下のリソースをチェックしてください：

- [Next.jsドキュメント](https://nextjs.org/docs)
- [Redux Toolkit](https://redux-toolkit.js.org/)
- [Supabase](https://supabase.io/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Supabase認証ヘルパー](https://supabase.com/docs/guides/auth/auth-helpers/nextjs)

## Vercelでのデプロイ

Next.jsアプリをデプロイする最も簡単な方法は、Next.jsの作者が提供する[Vercelプラットフォーム](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme)を使用することです。

詳細については、[Next.jsデプロイドキュメント](https://nextjs.org/docs/deployment)をご覧ください。


