"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/market", label: "Market" },
  { href: "/news", label: "News" },
] as const;

export function NavBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur supports-[backdrop-filter]:bg-zinc-950/80">
      <nav className="mx-auto flex max-w-6xl items-center gap-1 px-4 py-3 sm:gap-2 sm:px-6">
        <Link
          href="/"
          className="mr-2 text-sm font-semibold tracking-tight text-white sm:mr-6 sm:text-base"
        >
          Finance
        </Link>
        <div className="flex flex-1 flex-wrap items-center justify-end gap-1 sm:justify-start sm:gap-2">
          {links.map(({ href, label }) => {
            const active =
              href === "/"
                ? pathname === "/"
                : pathname === href || pathname.startsWith(`${href}/`);

            return (
              <Link
                key={href}
                href={href}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
