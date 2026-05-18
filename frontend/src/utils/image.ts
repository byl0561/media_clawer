/**
 * Resolve a poster/cover URL for an <img>.
 *
 * - null            -> local 404 placeholder
 * - "/api/..."      -> used as-is
 * - "/v1/..."       -> prefixed with /api (nginx strips it back off)
 * - absolute URL    -> proxied through images.weserv.nl (bypasses Douban
 *                       hotlink protection)
 */
export function imageUrl(url: string | null): string {
    if (url == null) return "/images/404.png";
    if (url.startsWith("/api")) return url;
    if (url.startsWith("/")) return `/api${url}`;
    return `https://images.weserv.nl/?url=${encodeURIComponent(url)}`;
}
