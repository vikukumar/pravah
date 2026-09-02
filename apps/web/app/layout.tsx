import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/providers/auth-provider";
import { OrgProvider } from "@/providers/org-provider";
import { ToastProvider } from "@/components/ui/toast";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "https://pravah.app"),
  title: "PRAVAH — AI-Powered Social Media Management, Automation & No-Code Operating System",
  description:
    "Production-grade, multi-tenant AI social media management platform. Connect social accounts, generate brand-aligned copy, build visual automation workflows, and schedule with smart recommendations.",
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
  manifest: "/site.webmanifest",
  openGraph: {
    title: "PRAVAH — AI Social Media Operating System",
    description: "Multi-tenant social media management, 400+ AI provider compatibility, and no-code automation workflows.",
    url: "https://pravah.app",
    siteName: "PRAVAH",
    images: [{ url: "/images/pravah_horizontal_logo.png", width: 1200, height: 630 }],
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080c14] text-slate-100 min-h-screen">
        <AuthProvider>
          <OrgProvider>
            <ToastProvider>{children}</ToastProvider>
          </OrgProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
