import Link from "next/link";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-2xl">🗺️</span>
          <div className="flex flex-col leading-tight">
            <span className="font-bold text-base text-gray-900 group-hover:text-primary-600 transition-colors">
              自然スポットマップ
            </span>
            <span className="text-[10px] text-gray-500">東京・神奈川の自然スポット</span>
          </div>
        </Link>
      </div>
    </header>
  );
}
