-- 自然スポットマッピングアプリ - Cloudflare D1 (SQLite) スキーマ

-- スポット本体
CREATE TABLE IF NOT EXISTS spots (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  description TEXT,
  category    TEXT NOT NULL CHECK (category IN ('meditation', 'waterside', 'hidden_gem', 'waterfall', 'walking', 'sports', 'bbq')),
  latitude    REAL NOT NULL,
  longitude   REAL NOT NULL,
  nickname    TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_spots_category ON spots(category);
CREATE INDEX IF NOT EXISTS idx_spots_location ON spots(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_spots_created_at ON spots(created_at DESC);

-- スポット×タグ（多対多）
CREATE TABLE IF NOT EXISTS spot_tags (
  spot_id TEXT NOT NULL,
  tag     TEXT NOT NULL,
  PRIMARY KEY (spot_id, tag),
  FOREIGN KEY (spot_id) REFERENCES spots(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_spot_tags_tag ON spot_tags(tag);

-- コメント
CREATE TABLE IF NOT EXISTS comments (
  id         TEXT PRIMARY KEY,
  spot_id    TEXT NOT NULL,
  body       TEXT NOT NULL,
  nickname   TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (spot_id) REFERENCES spots(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_comments_spot_id ON comments(spot_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC);
