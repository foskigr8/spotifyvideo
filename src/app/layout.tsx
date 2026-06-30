import type { Metadata } from "next";
import { Caveat, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const caveat = Caveat({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const geistSans = Geist({
  variable: "--font-body",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Spotify Video Previewer",
  description: "Word-synced doodle-animation previewer for the Spotify video essay.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${caveat.variable} ${geistSans.variable} ${geistMono.variable} antialiased bg-[#F5F0E8] text-[#1A1A1A]`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
