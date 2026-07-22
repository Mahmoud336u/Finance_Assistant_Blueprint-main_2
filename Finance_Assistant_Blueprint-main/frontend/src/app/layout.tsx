import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meridian — AI-Powered Financial Intelligence",
  description:
    "Your personal AI financial advisor. Track spending, manage budgets, and get intelligent insights — all in one premium experience.",
  keywords: ["finance", "ai", "budgeting", "spending", "personal finance"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
