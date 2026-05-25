import { Suspense } from "react";
import HomeClient from "@/components/spots/HomeClient";

export default function HomePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">読み込み中...</div>}>
      <HomeClient />
    </Suspense>
  );
}
