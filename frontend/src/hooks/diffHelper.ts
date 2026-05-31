import type {MediaItem, MediaItemGroupData, SeriesGroupData, SeriesPoster, SeriesRow} from "@/types";
import type {ApiResult} from "@/http/client";
import type {
    AlbumLyricGap,
    BindLibrary,
    IgnoreLibrary,
    IncompleteSeason,
    MediaItemDTO,
    MovieItem,
    MovieSeriesGap,
    SeasonRef,
    ShowSeriesGap,
    SubtitleShowGap,
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
    return {title: item.title, poster: item.poster, link: item.link, score: item.score};
}

function seasonLink(tmdbId: number | null, num: number): string | null {
    return tmdbId != null
        ? `https://www.themoviedb.org/tv/${tmdbId}/season/${num}`
        : null;
}

function seasonPoster(
    season: SeasonRef,
    tmdbId: number | null,
    ignore?: SeriesPoster["ignore"],
): SeriesPoster {
    return {
        title: season.name,
        poster: season.poster,
        link: seasonLink(tmdbId, season.num),
        score: season.score ?? null,
        ignore,
    };
}

function incompletePoster(
    show: ShowSeriesGap,
    inc: IncompleteSeason,
    library: IgnoreLibrary,
): SeriesPoster {
    // Reuse the season poster (and score) from local_seasons when we have it
    // — the local season exists by definition for an incomplete entry.
    const local = show.local_seasons.find((s) => s.num === inc.season_num);
    const tmdbId = show.show.tmdb_id;
    return {
        // `missing_count` is accurate even when the gap is non-contiguous
        // (1,2,4,5 missing 3,6-10 → 6 missing, not 5 from the local-max range).
        title: `${inc.season_name} · 缺 ${inc.missing_count} 集`,
        poster: local?.poster ?? null,
        link: seasonLink(tmdbId, inc.season_num),
        score: local?.score ?? null,
        ignore: tmdbId != null ? {library, tmdbId} : undefined,
    };
}

/** Movie collection → SeriesRow. */
export function buildMovieSeries(load: Loader<MovieSeriesGap[]>): Promise<SeriesGroupData> {
    return collectSeries(load, (gaps) =>
        gaps.map((gap) => ({
            title: gap.collection_name ?? `合集 ${gap.collection_id}`,
            // Open the TMDB collection page when the user clicks the title.
            link: `https://www.themoviedb.org/collection/${gap.collection_id}`,
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
                ...gap.missing_seasons.map((s) => seasonPoster(s, tmdbId, ignore)),
                ...gap.incomplete_seasons.map((inc) => incompletePoster(gap, inc, library)),
            ];
            return {
                title: gap.show.title,
                link: gap.show.link,
                score: gap.show.score,
                // Local seasons stay informational; they have no ignore ref.
                local: gap.local_seasons.map((s) => seasonPoster(s, tmdbId)),
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

// --- Subtitle / lyric gap builders --------------------------------------

/** Flat list of local movies missing a subtitle. Each tile carries an
 *  `ignoreSubtitle` ref that triggers the per-poster confirm dialog. */
export function buildMovieSubtitleGroup(
    load: Loader<MovieItem[]>,
): Promise<MediaItemGroupData> {
    return collect(load, (movies, items) => {
        for (const m of movies) {
            const media = toMedia(m);
            // Local movies always have a TMDB id, but parse defensively.
            const tmdbAny = m as MovieItem & {tmdb_id?: number};
            if (m.link) {
                const match = m.link.match(/\/movie\/(\d+)/);
                if (match) media.ignoreSubtitle = {tmdbId: Number(match[1])};
            } else if (tmdbAny.tmdb_id != null) {
                media.ignoreSubtitle = {tmdbId: tmdbAny.tmdb_id};
            }
            items.push(media);
        }
    });
}

/** Flat list of local albums whose tracks lack lyrics. Each tile carries an
 *  `ignoreLyric` ref keyed by signed path token. */
export function buildAlbumLyricGroup(
    load: Loader<AlbumLyricGap[]>,
): Promise<MediaItemGroupData> {
    return collect(load, (albums, items) => {
        for (const a of albums) {
            items.push({
                title: a.title,
                img: a.poster,
                score: null,
                link: null,
                ignoreLyric: {token: a.token},
            });
        }
    });
}

/** TV/anime subtitle gap → SeriesRow with empty local (flat right-grid only).
 *  Each season tile triggers the IgnoreDialog in subtitle mode. */
export function buildShowSubtitleSeries(
    load: Loader<SubtitleShowGap[]>,
    library: IgnoreLibrary,
): Promise<SeriesGroupData> {
    return collectSeries(load, (gaps) =>
        gaps.map((gap) => {
            const tmdbId = gap.show.tmdb_id;
            const ignore =
                tmdbId != null
                    ? ({library, tmdbId, mode: "subtitle"} as const)
                    : undefined;
            const tiles: SeriesPoster[] = gap.seasons.map((s) => ({
                title:
                    s.missing_count > 1
                        ? `${s.name} · 缺 ${s.missing_count} 集`
                        : `${s.name} · 缺 1 集`,
                poster: s.poster,
                link:
                    tmdbId != null
                        ? `https://www.themoviedb.org/tv/${tmdbId}/season/${s.num}`
                        : null,
                score: s.score ?? null,
                ignore,
            }));
            return {
                title: gap.show.title,
                link: gap.show.link,
                score: gap.show.score,
                local: [],
                missing: tiles,
            };
        }),
    );
}
