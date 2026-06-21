import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import NavLinks from "@/components/nav-links";
import BrandLogo from "@/components/brand-logo";
import SiteBackground from "@/components/site-background";

export const metadata: Metadata = {
  title: "WC26 Intelligence",
  description: "Daily World Cup 2026 intelligence briefs and standings",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body
        className="min-h-full flex flex-col relative isolate"
        style={{ backgroundColor: "#060E22", color: "#FFFFFF" }}
      >
        <SiteBackground />
        <div className="relative z-10 flex min-h-full flex-col">
          <header className="app-header">
            <nav className="nav-inner">
              <Link href="/" aria-label="WC26 Intelligence — home" className="brand">
                <BrandLogo height={40} />
              </Link>
              <NavLinks />
            </nav>
          </header>

          <main className="flex-1">{children}</main>

          <footer
            className="text-center text-xs py-4 px-6"
            style={{ color: "#6B7A9E", borderTop: "1px solid #1E3157" }}
          >
            Auto-published daily, 7:00 AM Australia/Melbourne
          </footer>
        </div>
      </body>
    </html>
  );
}
