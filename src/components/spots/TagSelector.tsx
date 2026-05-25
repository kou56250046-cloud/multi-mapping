"use client";

import { TAGS } from "@/lib/utils/tagConfig";
import type { SpotTag } from "@/types/spot";

interface Props {
  selected: SpotTag[];
  onChange: (tags: SpotTag[]) => void;
}

export default function TagSelector({ selected, onChange }: Props) {
  const toggle = (tag: SpotTag) => {
    onChange(selected.includes(tag) ? selected.filter((t) => t !== tag) : [...selected, tag]);
  };

  return (
    <div className="flex flex-wrap gap-1.5">
      {TAGS.map((t) => {
        const active = selected.includes(t.value);
        return (
          <button
            key={t.value}
            type="button"
            onClick={() => toggle(t.value)}
            className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
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
  );
}
