"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import LocationPicker from "./LocationPicker";
import TagSelector from "./TagSelector";
import { CATEGORIES } from "@/lib/utils/categoryConfig";
import { createSpot } from "@/lib/storage/local";
import type { SpotCategory, SpotTag } from "@/types/spot";

export default function SpotForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<SpotCategory>("meditation");
  const [latlng, setLatlng] = useState<{ lat: number; lng: number } | null>(null);
  const [tags, setTags] = useState<SpotTag[]>([]);
  const [nickname, setNickname] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("スポット名を入力してください");
      return;
    }
    if (name.length > 100) {
      setError("スポット名は100文字以内で入力してください");
      return;
    }
    if (description.length > 1000) {
      setError("説明文は1000文字以内で入力してください");
      return;
    }
    if (nickname.length > 50) {
      setError("ニックネームは50文字以内で入力してください");
      return;
    }
    if (!latlng) {
      setError("地図上で位置を指定してください");
      return;
    }

    setSubmitting(true);
    try {
      const spot = createSpot({
        name: name.trim(),
        description: description.trim(),
        category,
        latitude: latlng.lat,
        longitude: latlng.lng,
        nickname: nickname.trim(),
        tags,
      });
      router.push(`/spots/${spot.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "投稿に失敗しました");
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-5 max-w-2xl mx-auto p-4">
      <div className="text-xs bg-blue-50 border border-blue-200 text-blue-800 p-3 rounded">
        ℹ️ 現在はMVP版のため、投稿スポットはこのブラウザ内のみに保存されます（他の人には見えません）。
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-1">
          スポット名 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={100}
          required
          placeholder="例: 多摩川河川敷の穴場"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <div className="text-xs text-gray-500 mt-0.5">{name.length}/100</div>
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-1">
          カテゴリ <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              type="button"
              onClick={() => setCategory(c.value)}
              className={`px-3 py-2 rounded-md border text-sm font-medium transition-all ${
                category === c.value
                  ? "text-white border-transparent shadow-md"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }`}
              style={category === c.value ? { backgroundColor: c.color } : undefined}
            >
              {c.icon} {c.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-1">説明 (任意)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={1000}
          rows={4}
          placeholder="例: サッカーができる広場があります。トイレも近くにあって便利。"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
        />
        <div className="text-xs text-gray-500 mt-0.5">{description.length}/1000</div>
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-1">
          位置 <span className="text-red-500">*</span>
        </label>
        <LocationPicker onChange={(lat, lng) => setLatlng({ lat, lng })} value={latlng} />
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-1">特徴タグ (複数選択可)</label>
        <TagSelector selected={tags} onChange={setTags} />
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-1">ニックネーム (任意)</label>
        <input
          type="text"
          value={nickname}
          onChange={(e) => setNickname(e.target.value)}
          maxLength={50}
          placeholder="未入力の場合「匿名」と表示されます"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded">
          {error}
        </div>
      )}

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={() => router.back()}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          キャンセル
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="px-6 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-gray-400 text-white font-medium rounded-md transition-colors"
        >
          {submitting ? "投稿中..." : "スポットを投稿"}
        </button>
      </div>
    </form>
  );
}
