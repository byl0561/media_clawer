import type {MediaItem, MediaItemGroupData} from "@/types";
import type {ApiResult} from "@/http/client";
import type {BindLibrary, IgnoreLibrary, LocalGap, MediaItemDTO} from "@/types/api";

export type Loader<T> = () => Promise<ApiResult<T>>;

/** Map a server media object to the UI's MediaItem shape. */
export function toMedia(item: MediaItemDTO): MediaItem {
    return {title: item.title, img: item.poster, score: item.score, link: item.link};
}

/**
 * Wrap a request so it runs at most once per page load. The diff endpoints
 * recompute server-side on every call, so the "missing" and "extra" tabs
 * must share a single response instead of fetching twice.
 */
export function once<T>(load: Loader<T>): Loader<T> {
    let cached: Promise<ApiResult<T>> | null = null;
    return () => {
        if (!cached) cached = load();
        return cached;
    };
}

async function collect<T>(
    load: Loader<T>,
    fill: (data: T, items: MediaItem[]) => void,
): Promise<MediaItemGroupData> {
    const group: MediaItemGroupData = {valid: true, mediaItems: []};
    const res = await load();
    if (!res.success) {
        group.valid = false;
        return group;
    }
    if (res.data == null) return group;
    fill(res.data, group.mediaItems);
    return group;
}

/** Build a tab from a diff-style payload by mapping `pick(data)`.
 *
 * Pass `bindLibrary` only for the "最新" tab — every missing rank item then
 * gets a `bind` ref that powers the per-poster bind-alias dialog. The "过时"
 * tab maps locals back to the same diff response and must not carry it.
 */
export function buildGroup<T>(
    load: Loader<T>,
    pick: (data: T) => MediaItemDTO[],
    bindLibrary?: BindLibrary,
): Promise<MediaItemGroupData> {
    return collect(load, (data, items) => {
        for (const item of pick(data)) {
            const media = toMedia(item);
            if (bindLibrary && item.title) {
                media.bind = {library: bindLibrary, alias: item.title};
            }
            items.push(media);
        }
    });
}

/** Build the "续集" tab from a `local-gaps` payload (shared by tv & anime). */
export function buildLocalGapGroup(
    load: Loader<LocalGap[]>,
    library: IgnoreLibrary,
): Promise<MediaItemGroupData> {
    return collect(load, (gaps, items) => {
        for (const gap of gaps) {
            const seasons = new Set<number>();
            for (const s of gap.missing_seasons) seasons.add(s.num);
            for (const s of gap.incomplete_seasons) seasons.add(s.season_num);
            const sorted = [...seasons].sort((a, b) => a - b);
            const media = toMedia(gap.show);
            media.title = `${media.title} - ${sorted.map((n) => `S${n}`).join(",")}`;
            // tmdb_id drives the ignore dialog; only present for TMDB/local
            // shows (it always is here — gap.show is the TMDB object).
            if (gap.show.tmdb_id != null) {
                media.ignore = {library, tmdbId: gap.show.tmdb_id};
            }
            items.push(media);
        }
    });
}
