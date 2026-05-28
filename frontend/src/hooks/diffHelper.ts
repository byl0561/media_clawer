import type {MediaItem, MediaItemGroupData, SeriesGroupData, SeriesPoster, SeriesRow} from "@/types";
import type {ApiResult} from "@/http/client";
import type {
    BindLibrary,
    IgnoreLibrary,
    IncompleteSeason,
    MediaItemDTO,
    MovieSeriesGap,
    SeasonRef,
    ShowSeriesGap,
} from "@/types/api";

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

// --- 续集 tab builders --------------------------------------------------

function moviePoster(item: MediaItemDTO): SeriesPoster {
    return {title: item.title, poster: item.poster, link: item.link};
}

function seasonPoster(season: SeasonRef): SeriesPoster {
    return {
        title: season.name,
        poster: season.poster,
        link: null,
    };
}

function incompletePoster(
    show: ShowSeriesGap,
    inc: IncompleteSeason,
    library: IgnoreLibrary,
): SeriesPoster {
    // Reuse the season poster from local_seasons when we have it (the local
    // season exists by definition for an incomplete entry); fall back to none.
    const local = show.local_seasons.find((s) => s.num === inc.season_num);
    const tmdbId = show.show.tmdb_id;
    return {
        title: `${inc.season_name} · 缺 ${inc.local_max_episode + 1}–${inc.remote_max_episode} 集`,
        poster: local?.poster ?? null,
        link: null,
        ignore: tmdbId != null ? {library, tmdbId} : undefined,
    };
}

/** Movie collection → SeriesRow. */
export function buildMovieSeries(load: Loader<MovieSeriesGap[]>): Promise<SeriesGroupData> {
    return collectSeries(load, (gaps) =>
        gaps.map((gap) => ({
            title: gap.collection_name ?? `合集 ${gap.collection_id}`,
            link: null,
            score: gap.score,
            local: gap.local.map(moviePoster),
            missing: gap.missing.map(moviePoster),
            ignoreCollection: {collectionId: gap.collection_id},
        })),
    );
}

/** TV/anime show → SeriesRow (missing + incomplete seasons combined on the right). */
export function buildShowSeries(
    load: Loader<ShowSeriesGap[]>,
    library: IgnoreLibrary,
): Promise<SeriesGroupData> {
    return collectSeries(load, (gaps) =>
        gaps.map((gap) => {
            const tmdbId = gap.show.tmdb_id;
            const ignore = tmdbId != null ? {library, tmdbId} : undefined;
            const missing: SeriesPoster[] = [
                ...gap.missing_seasons.map((s) => ({...seasonPoster(s), ignore})),
                ...gap.incomplete_seasons.map((inc) => incompletePoster(gap, inc, library)),
            ];
            return {
                title: gap.show.title,
                link: gap.show.link,
                score: gap.show.score,
                local: gap.local_seasons.map(seasonPoster),
                missing,
            };
        }),
    );
}

async function collectSeries<T>(
    load: Loader<T>,
    rows: (data: T) => SeriesRow[],
): Promise<SeriesGroupData> {
    const group: SeriesGroupData = {valid: true, rows: []};
    const res = await load();
    if (!res.success) {
        group.valid = false;
        return group;
    }
    if (res.data == null) return group;
    group.rows = rows(res.data);
    return group;
}
