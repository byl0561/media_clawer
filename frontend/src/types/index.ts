/** UI-facing view models (server shapes live in `@/types/api`). */

import type {BindLibrary, IgnoreLibrary} from "@/types/api";

/** Set only on TV/anime 续集 right-side tiles: opens the per-show ignore dialog.
 *
 * ``mode`` switches which endpoints the dialog talks to:
 * - ``"series"`` (default) — series gap (drives ``checked_episode``)
 * - ``"subtitle"`` — subtitle gap (drives ``subtitle_checked_episode``)
 */
export interface IgnoreRef {
    library: IgnoreLibrary;
    tmdbId: number;
    mode?: "series" | "subtitle";
}

/** Set on movie subtitle-gap tiles: confirm + POST /movies/ignore-subtitle. */
export interface IgnoreSubtitleRef {
    tmdbId: number;
}

/** Set on album lyric-gap tiles: confirm + POST /albums/ignore-lyric. */
export interface IgnoreLyricRef {
    token: string;
}

/** Set only on 最新 items: enables the per-poster bind-alias action. */
export interface BindRef {
    library: BindLibrary;
    /** The rank title that will be written as an alias on the chosen local. */
    alias: string;
}

export interface MediaItem {
    title: string;
    img: string | null;
    score: number | null;
    link: string | null;
    ignore?: IgnoreRef;
    bind?: BindRef;
    /** Set only on the 字幕 tab — movie variant only. */
    ignoreSubtitle?: IgnoreSubtitleRef;
    /** Set only on the 歌词 tab — album variant only. */
    ignoreLyric?: IgnoreLyricRef;
}

export interface MediaItemGroupData {
    valid: boolean;
    mediaItems: MediaItem[];
}

/** A poster on the series-gap card (left stack or right tile). */
export interface SeriesPoster {
    /** Hover label (movie title / "Season N" / "Season N · 缺 m-n 集"). */
    title: string;
    poster: string | null;
    link: string | null;
    /** TMDB score (rounded to 1 dp), null when there isn't one yet. */
    score: number | null;
    /** Set on right-side TV/anime tiles to open the per-season ignore dialog. */
    ignore?: IgnoreRef;
}

/** One row in the 续集 list: a movie collection or a TV/anime show. */
export interface SeriesRow {
    /** Display title (collection name / show title). */
    title: string;
    link: string | null;
    /** Vote-weighted collection score / show's own TMDB score. */
    score: number | null;
    local: SeriesPoster[];
    missing: SeriesPoster[];
    /** Only set on the movie variant — triggers the confirm + ignore-collection POST. */
    ignoreCollection?: {
        collectionId: number;
    };
}

export interface SeriesGroupData {
    valid: boolean;
    rows: SeriesRow[];
}

/** A tab returns either the flat item list or the series-card list. */
export interface MediaItemFunctionGroup {
    name: string;
    /** Optional display label used by the Overview cards. Defaults to ``name``. */
    overviewLabel?: string;
    acquireData?: (onProgress?: (step: string, pct: number) => void) => Promise<MediaItemGroupData>;
    acquireSeries?: (onProgress?: (step: string, pct: number) => void) => Promise<SeriesGroupData>;
}

export interface MediaGroup {
    name: string;
    mediaItemFunctionGroups: MediaItemFunctionGroup[];
}
