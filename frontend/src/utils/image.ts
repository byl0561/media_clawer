/**
 * Resolve a poster/cover URL for an <img>.
 *
 * - null            -> local 404 placeholder
 * - "/api/..."      -> used as-is
 * - "/v1/..."       -> prefixed with /api (nginx strips it back off)
 * - absolute URL    -> proxied through our own backend, which fetches it
 *                       server-side (no browser Referer, so Douban's hotlink
 *                       protection doesn't apply). Replaces the previous
 *                       images.weserv.nl redirect, which started 404ing.
 */
export function imageUrl(url: string | null): string {
    if (url == null) return "/images/404.png";
    if (url.startsWith("/api")) return url;
    if (url.startsWith("/")) return `/api${url}`;
    return `/api/v1/images/proxy?url=${encodeURIComponent(url)}`;
}
