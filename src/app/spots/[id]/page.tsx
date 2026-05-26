import { loadAllSpots } from "@/lib/data/spots";
import SpotDetailClient from "@/components/spots/SpotDetailClient";

/** ビルド時に全スポットの詳細ページを静的生成 */
export async function generateStaticParams() {
  return loadAllSpots().map((s) => ({ id: s.id }));
}

export default async function SpotDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <SpotDetailClient id={id} />;
}
