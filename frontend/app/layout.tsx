import type { Metadata } from "next";
import { Syne, Space_Mono } from "next/font/google";
import "./globals.css";

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const spaceMono = Space_Mono({
  variable: "--font-space-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "STREAM — Anti-Corruption Intelligence Engine",
  description: "Suspicious Transaction Risk Engine for Anomaly Monitoring",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${syne.variable} ${spaceMono.variable} antialiased`}
      >
        {/* Background orbs */}
        <div className="orb orb-green" style={{ width: 400, height: 400, top: '10%', left: '5%', opacity: 0.07 }} />
        <div className="orb orb-blue" style={{ width: 300, height: 300, top: '60%', right: '10%', opacity: 0.07 }} />
        <div className="orb orb-purple" style={{ width: 350, height: 350, bottom: '5%', left: '40%', opacity: 0.07 }} />
        <div className="grid-bg min-h-screen relative z-10">
          {children}
        </div>
      </body>
    </html>
  );
}
