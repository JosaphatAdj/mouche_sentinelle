import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mouche Sentinel — IndabaX Bénin 2026",
  description: "Surveillance intelligente de la mouche des fruits et assistant en langue Fon",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="bg-slate-50 min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
