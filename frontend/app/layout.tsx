import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";

import "./globals.css";

export const metadata: Metadata = {
  title: "Aegis OS",
  description:
    "Emergency intelligence platform for medical triage and disaster response."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-body">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
