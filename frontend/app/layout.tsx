import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CampusIQ — AI Student Query Management System",
  description: "College query assistance grounded in official documents, with faculty escalation workflows.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light" style={{ colorScheme: "light" }}>
      <body className="antialiased bg-gray-50 text-gray-900 min-h-screen">
        {children}
      </body>
    </html>
  );
}
