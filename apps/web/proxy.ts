import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Ignore static assets, public assets, and Next.js internal routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/images") ||
    pathname.startsWith("/icons") ||
    pathname.startsWith("/favicon.ico") ||
    pathname.startsWith("/site.webmanifest") ||
    pathname.startsWith("/robots.txt")
  ) {
    return NextResponse.next();
  }

  try {
    const apiUrl = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
    const res = await fetch(`${apiUrl}/setup/status`, {
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(2000),
    });

    if (res.ok) {
      const data = await res.json();

      // Case 1: First time setup not done yet -> Redirect to /setup
      if (!data.is_initialized && pathname !== "/setup") {
        const setupUrl = new URL("/setup", request.url);
        return NextResponse.redirect(setupUrl);
      }

      // Case 2: Setup is already completed -> Prevent visiting /setup again
      if (data.is_initialized && pathname === "/setup") {
        const loginUrl = new URL("/login", request.url);
        return NextResponse.redirect(loginUrl);
      }
    }
  } catch {
    // If backend is still starting up, let request proceed
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
