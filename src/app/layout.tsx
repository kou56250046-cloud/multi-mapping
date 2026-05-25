import type { Metadata, Viewport } from "next";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";
import Header from "@/components/ui/Header";
import ServiceWorkerRegistrar from "@/components/pwa/ServiceWorkerRegistrar";

export const metadata: Metadata = {
  title: "自然スポットマップ | 静かな自然・穴場・BBQスポットを共有",
  description:
    "東京・神奈川の自然スポットを地図で共有。瞑想に最適な静かな場所、人が少ない穴場、滝、散歩道、BBQができるスポットなど。",
  manifest: "/manifest.json",
  openGraph: {
    title: "自然スポットマップ",
    description: "東京・神奈川の自然・穴場・BBQスポットを共有するマップ",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#22c55e",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body className="flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 flex flex-col">{children}</main>
        <ServiceWorkerRegistrar />
      </body>
    </html>
  );
}
