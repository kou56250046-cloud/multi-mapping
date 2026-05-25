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
            <span className="text-[10px] text-gray-500">東京・神奈川の自然を共有</span>
          </div>
        </Link>
        <nav className="flex items-center gap-2">
          <Link
            href="/spots/new"
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium rounded-lg transition-colors"
          >
            ＋ スポット投稿
          </Link>
        </nav>
      </div>
    </header>
  );
}
