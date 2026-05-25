import SpotForm from "@/components/spots/SpotForm";

export const metadata = {
  title: "スポットを投稿 | 自然スポットマップ",
};

export default function NewSpotPage() {
  return (
    <div className="bg-gray-50 min-h-screen py-6">
      <div className="max-w-2xl mx-auto px-4 mb-4">
        <h1 className="text-xl font-bold text-gray-900 mb-1">新しいスポットを投稿</h1>
        <p className="text-sm text-gray-600">
          静かな場所、穴場、BBQができる場所など、あなたが知っているスポットを教えてください。
        </p>
      </div>
      <SpotForm />
    </div>
  );
}
