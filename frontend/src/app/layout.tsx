import type { Metadata } from "next";
import { Orbitron, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Providers from "@/components/ui/Providers";

const orbitron = Orbitron({ subsets: ["latin"], variable: "--font-orbitron", weight: ["400", "700"] });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "PitWall.AI",
  description: "Virtual Race Engineer · ACC GT3",
};

// Root layout: SOLO fonts + globals. La Sidebar vive nel route group (app):
// così /login (route group (auth)) non la eredita più — fix INC-V2-004
// (megaprompt #6, FASE 8). Gli URL non cambiano: i gruppi non entrano nel path.
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it" className={`${orbitron.variable} ${inter.variable} ${mono.variable}`}>
      <body className="min-h-screen bg-bg font-body text-white">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
