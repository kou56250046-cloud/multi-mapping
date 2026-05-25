# 自然スポットマップ

東京・神奈川の自然・穴場・BBQスポットを地図で共有するPWA Webアプリ。

## 特徴

- 🗺️ **maplibre-gl + OpenStreetMap** で軽量・無料の地図表示
- 📍 **ログイン不要** で誰でもスポット投稿・コメント可能
- 🏷️ **7カテゴリ + 12タグ** でフィルタリング
- 📱 **PWA対応** でスマホのホーム画面に追加可能
- 🛡️ **Cloudflare Turnstile** でスパム対策
- 🌐 **GPS近隣検索** で現在地から近いスポット表示

## 技術スタック

- Next.js 15 (App Router) + TypeScript
- maplibre-gl 5.24 + OpenStreetMap ラスタタイル
- Cloudflare D1 (SQLite) — HTTP API経由
- Cloudflare Turnstile
- Tailwind CSS
- Vercel (GitHub連携・PRプレビューURL自動発行)

## セットアップ手順

### 1. 依存関係のインストール

```bash
npm install
```

### 2. Cloudflare D1データベース作成

[Cloudflare Dashboard](https://dash.cloudflare.com) で：

1. D1 (Workers & Pages → D1) → 「Create database」
2. データベース名: `nature-spots` (任意)
3. 作成後、Database IDをコピー

**スキーマ適用**:

Cloudflare Dashboardの該当データベース → Console から `d1/schema.sql` の内容を実行。  
または、Wrangler CLI を使う場合：

```bash
npx wrangler d1 execute nature-spots --file=./d1/schema.sql --remote
# 開発データを入れる場合
npx wrangler d1 execute nature-spots --file=./d1/seed.sql --remote
```

### 3. Cloudflare API トークン発行

1. [API Tokens](https://dash.cloudflare.com/profile/api-tokens) → 「Create Token」
2. 「Custom token」を選択
3. **Permissions**: `Account` → `D1` → `Edit`
4. **Account Resources**: 該当アカウント
5. トークンをコピー

### 4. Cloudflare Turnstile サイトキー発行

1. [Turnstile](https://dash.cloudflare.com/?to=/:account/turnstile) → 「Add site」
2. Domain: `localhost` (開発用) + 本番ドメイン
3. Widget Mode: `Managed` (推奨)
4. Site Key と Secret Key をコピー

### 5. 環境変数設定

`.env.example` をコピーして `.env.local` を作成：

```bash
cp .env.example .env.local
```

`.env.local` に値を設定：

```bash
CF_ACCOUNT_ID=xxxxxxxxxxxx
CF_API_TOKEN=xxxxxxxxxxxx
CF_D1_DATABASE_ID=xxxxxxxxxxxx
NEXT_PUBLIC_TURNSTILE_SITE_KEY=0x4AAAxxxxxxxx
TURNSTILE_SECRET_KEY=0x4AAAxxxxxxxx
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 6. 開発サーバー起動

```bash
npm run dev
```

http://localhost:3000 を開く。

### 7. Vercelデプロイ

1. GitHubにリポジトリを作成・push
2. [Vercel](https://vercel.com/new) でリポジトリをインポート
3. 環境変数を設定（`.env.local` と同じキー）
4. デプロイ → URL発行

PRを作成するたびにプレビューURLが自動発行されます。

## ディレクトリ構成

```
src/
├── app/
│   ├── api/               # API Routes (D1 + Turnstile)
│   ├── spots/             # 投稿・詳細ページ
│   └── page.tsx           # トップページ（地図）
├── components/
│   ├── map/               # 地図関連 (MapView, LocationPicker)
│   ├── spots/             # スポット関連 (Form, Card, Filter)
│   ├── comments/          # コメント関連
│   └── ui/                # 共通UI
├── lib/
│   ├── d1/                # Cloudflare D1 クライアント
│   ├── turnstile/         # Turnstile 検証
│   └── utils/             # カテゴリ・タグ・距離計算
├── hooks/                 # React hooks (useGeolocation)
└── types/                 # TypeScript型定義
d1/
├── schema.sql             # D1スキーマ
└── seed.sql               # 開発用シードデータ
public/
├── manifest.json          # PWA設定
├── sw.js                  # Service Worker
└── icons/icon.svg         # PWAアイコン
```

## スポットカテゴリ

| 値 | 表示名 | アイコン |
|---|---|---|
| `meditation` | 瞑想・癒し | 🧘 |
| `waterside` | 川・水辺 | 🏞️ |
| `hidden_gem` | 穴場 | 💎 |
| `waterfall` | 滝 | 💦 |
| `walking` | 散歩道 | 🚶 |
| `sports` | スポーツ | ⚽ |
| `bbq` | BBQ | 🍖 |

## 注意事項

- Cloudflare D1 の無料枠は十分（5GB/月、5000万読み取り）
- 画像アップロード機能はなし（テキスト情報のみ）
- 本番ドメインを Turnstile に登録するのを忘れずに
