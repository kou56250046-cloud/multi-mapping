import SpotDetailClient from "@/components/spots/SpotDetailClient";

export default async function SpotDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <SpotDetailClient id={id} />;
}
