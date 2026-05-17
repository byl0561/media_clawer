import type {MediaItem, MediaItemGroupData} from "@/types";
import type {ResponseWrapper} from "@/http/httpInstance";

export type Loader = () => Promise<ResponseWrapper>;

/** Map a server media object to the UI's MediaItem shape. */
export function toMedia(m: any): MediaItem {
    return {title: m.title, img: m.poster, score: m.score, link: m.link};
}

/**
 * Wrap a request so the underlying call runs at most once per page load.
 * The diff endpoints recompute server-side on every call, so the "missing"
 * and "extra" tabs must share a single response instead of fetching twice.
 */
export function once(load: Loader): Loader {
    let cached: Promise<ResponseWrapper> | null = null;
    return () => {
        if (!cached) cached = load();
        return cached;
    };
}

/** Build a tab's data by mapping `pick(data)` through {@link toMedia}. */
export async function buildGroup(
    load: Loader,
    pick: (data: any) => any[],
): Promise<MediaItemGroupData> {
    const group: MediaItemGroupData = {valid: true, mediaItems: []};
    const res = await load();
    if (!res.success) {
        group.valid = false;
        return group;
    }
    if (res.data == null) return group;
    for (const item of pick(res.data)) group.mediaItems.push(toMedia(item));
    return group;
}
