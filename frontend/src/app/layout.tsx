import type { Metadata } from "next";
import { Orbitron, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/ui/Sidebar";
import MotionProvider from "@/components/ui/MotionProvider";

const orbitron = Orbitron({ subsets: ["latin"], variable: "--font-orbitron", weight: ["400", "700"] });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "PitWall.AI",
  description: "Virtual Race Engineer · ACC GT3",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it" className={`${orbitron.variable} ${inter.variable} ${mono.variable}`}>
      <body className="min-h-screen bg-bg font-body text-white">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="max-w-6xl flex-1 px-6 py-6">
            <MotionProvider>{children}</MotionProvider>
          </main>
        </div>
      </body>
    </html>
  );
}
