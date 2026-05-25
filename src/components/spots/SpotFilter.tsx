"use client";

import { useCallback, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CATEGORIES } from "@/lib/utils/categoryConfig";
import { TAGS } from "@/lib/utils/tagConfig";

export default function SpotFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [open, setOpen] = useState(false);

  const selectedCategories = (searchParams.get("category") ?? "").split(",").filter(Boolean);
  const selectedTags = (searchParams.get("tag") ?? "").split(",").filter(Boolean);
  const keyword = searchParams.get("keyword") ?? "";

  const updateParam = useCallback(
    (key: string, value: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) params.set(key, value);
      else params.delete(key);
      router.replace(`/?${params.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  const toggleCategory = (cat: string) => {
    const next = selectedCategories.includes(cat)
      ? selectedCategories.filter((c) => c !== cat)
      : [...selectedCategories, cat];
    updateParam("category", next.length > 0 ? next.join(",") : null);
  };

  const toggleTag = (tag: string) => {
    const next = selectedTags.includes(tag)
      ? selectedTags.filter((t) => t !== tag)
      : [...selectedTags, tag];
    updateParam("tag", next.length > 0 ? next.join(",") : null);
  };

  const clearAll = () => {
    router.replace("/", { scroll: false });
  };

  const hasFilter = selectedCategories.length > 0 || selectedTags.length > 0 || keyword;

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 py-3">
        <div className="flex items-center gap-2 flex-wrap">
          <input
            type="text"
            defaultValue={keyword}
            placeholder="スポット名・説明で検索..."
            className="flex-1 min-w-[200px] px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            onChange={(e) => {
              const value = e.target.value;
              clearTimeout((window as unknown as { _searchTimer?: number })._searchTimer);
              (window as unknown as { _searchTimer?: number })._searchTimer = window.setTimeout(
                () => updateParam("keyword", value || null),
                400,
              );
            }}
          />
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {open ? "▼ フィルタ" : "▶ フィルタ"}
          </button>
          {hasFilter && (
            <button
              type="button"
              onClick={clearAll}
              className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700"
            >
              クリア
            </button>
          )}
        </div>

        {open && (
          <div className="mt-3 pt-3 border-t border-gray-100 space-y-3">
            <div>
              <div className="text-xs font-bold text-gray-700 mb-1.5">カテゴリ</div>
              <div className="flex flex-wrap gap-1.5">
                {CATEGORIES.map((c) => {
                  const active = selectedCategories.includes(c.value);
                  return (
                    <button
                      key={c.value}
                      type="button"
                      onClick={() => toggleCategory(c.value)}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                        active
                          ? "text-white border-transparent"
                          : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                      }`}
                      style={active ? { backgroundColor: c.color } : undefined}
                    >
                      {c.icon} {c.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="text-xs font-bold text-gray-700 mb-1.5">特徴タグ</div>
              <div className="flex flex-wrap gap-1.5">
                {TAGS.map((t) => {
                  const active = selectedTags.includes(t.value);
                  return (
                    <button
                      key={t.value}
                      type="button"
                      onClick={() => toggleTag(t.value)}
                      className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                        active
                          ? "bg-primary-500 text-white border-transparent"
                          : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                      }`}
                    >
                      {t.icon} {t.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
