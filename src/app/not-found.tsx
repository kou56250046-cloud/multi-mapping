import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
      <div className="text-6xl mb-4">🗺️</div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">スポットが見つかりません</h1>
      <p className="text-gray-600 mb-6">
        お探しのスポットは削除されたか、URLが間違っている可能性があります。
      </p>
      <Link
        href="/"
        className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-md font-medium"
      >
        マップに戻る
      </Link>
    </div>
  );
}
