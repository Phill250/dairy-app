const isProd = process.env.NODE_ENV === "production";
const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// CSP is applied in production only, because dev mode needs eval() and websockets for hot reload.
// 'unsafe-inline' for scripts is needed by Next.js's own inline bootstrap code unless you set up nonces.
const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  `connect-src 'self' ${apiUrl}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "geolocation=(), microphone=(), camera=()" },
  ...(isProd ? [{ key: "Content-Security-Policy", value: csp }] : []),
];

module.exports = {
    turbopack: { root: __dirname },
    async headers() {
      return [{ source: "/(.*)", headers: securityHeaders }];
    },
  };