import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BookMe",
  description: "Schedule a meeting",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
