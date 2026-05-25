import type { SpotCategory } from "@/types/spot";
import { getCategoryColor, getCategoryIcon, getCategoryLabel } from "@/lib/utils/categoryConfig";

export default function CategoryBadge({ category }: { category: SpotCategory }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-white text-xs font-medium"
      style={{ backgroundColor: getCategoryColor(category) }}
    >
      <span>{getCategoryIcon(category)}</span>
      <span>{getCategoryLabel(category)}</span>
    </span>
  );
}
