import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protect dashboard routes
  if (pathname.startsWith("/dashboard")) {
    // Check for better-auth session cookie
    const sessionCookie = request.cookies.get("better-auth.session_token");
    
    if (!sessionCookie) {
      // For development/demo: allow access without strict auth
      // In production, uncomment the redirect below:
      // const loginUrl = new URL("/login", request.url);
      // loginUrl.searchParams.set("callbackUrl", pathname);
      // return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
  ],
};
