/** Server response shapes for the `/api/v1` endpoints. */

/** The two libraries with a 续集 ignore action. */
export type IgnoreLibrary = "tv" | "anime";

/** Libraries that bind by TMDB id (movies/tv/anime — public unique key). */
export type TmdbBindLibrary = "movie" | "tv" | "anime";

/** Libraries that bind by signed path token (album/book — no public id). */
export type TokenBindLibrary = "album" | "book";

/** All libraries supporting the "最新" bind-alias action. */
export type BindLibrary = TmdbBindLibrary | TokenBindLibrary;

export interface MediaItemDTO {
    title: string;
    score: number | null;
    votes: number | null;
    poster: string | null;
    link: string | null;
}

export interface MovieItem extends MediaItemDTO {
    year: number;
}

export interface ShowItem extends MediaItemDTO {
    year: number[];
    /** Present for TMDB/local shows (series-gaps); null for Douban/Bangumi. */
    tmdb_id: number | null;
}

export interface AlbumItem extends MediaItemDTO {
    artist: string;
    year: number;
}

export interface BookItem extends MediaItemDTO {
    author: string;
}

export interface Diff<T> {
    missing: T[];
    extra: T[];
}

/** `GET /api/v1/movies/series-gaps` row. */
export interface MovieSeriesGap {
    collection_id: number;
    collection_name: string | null;
    /** Vote-weighted score across every TMDB member of the collection. */
    score: number | null;
    votes: number;
    local: MovieItem[];
    missing: MovieItem[];
}

/** One season identifier + display fields (poster + chinese name + TMDB score). */
export interface SeasonRef {
    num: number;
    name: string;
    poster: string | null;
    score?: number | null;
}

export interface IncompleteSeason {
    season_num: number;
    season_name: string;
    local_max_episode: number;
    remote_max_episode: number;
    /** Real count of aired episodes the user is missing in this season —
     * accurate for non-contiguous gaps (e.g. has 1,2,4,5 missing 3,6-10). */
    missing_count: number;
}

/** `GET /api/v1/{tv-shows,anime}/series-gaps` row. */
export interface ShowSeriesGap {
    show: ShowItem;
    local_seasons: SeasonRef[];
    missing_seasons: SeasonRef[];
    incomplete_seasons: IncompleteSeason[];
}

/** One season tile in the subtitle-gap card. */
export interface SubtitleGapSeason {
    num: number;
    name: string;
    poster: string | null;
    score?: number | null;
    /** Count of episodes in this season missing a subtitle. */
    missing_count: number;
    /** Highest such episode number — drives the ignore dialog's "整季" choice. */
    max_missing_episode: number;
}

/** `GET /api/v1/{tv-shows,anime}/subtitle-gaps` row. */
export interface SubtitleShowGap {
    show: ShowItem;
    seasons: SubtitleGapSeason[];
}

/** `GET /api/v1/albums/lyric-gaps` row (token-keyed for the ignore action). */
export interface AlbumLyricGap {
    token: string;
    title: string;
    artist: string | null;
    year: number;
    poster: string | null;
}

/** One episode the user could ignore up to (from TMDB, on dialog open). */
export interface IgnoreEpisode {
    num: number;
    name: string;
    date: string | null;
}

/** A gap season offered in the ignore dialog. */
export interface IgnoreSeason {
    season_num: number;
    season_name: string;
    /** Highest episode already present locally (0 if the season is absent). */
    local_max_episode: number;
    /** Highest episode TMDB knows — selecting this ignores the whole rest. */
    latest_episode: number;
    /** Selectable episodes: the currently-missing range, ascending. */
    episodes: IgnoreEpisode[];
}

export interface IgnoreOptions {
    title: string;
    seasons: IgnoreSeason[];
}

/** One season's chosen cutoff: ignore episodes up to and including `episode`. */
export interface IgnoreSelection {
    season_num: number;
    episode: number;
}

export interface IgnoreResult {
    /** True iff every gap season was selected at its latest episode. */
    fully_ignored: boolean;
}

export interface IgnoreCollectionResult {
    /** How many local movies now carry this collection id in skip_collections. */
    updated: number;
}

export interface IgnoreFlagResult {
    /** True iff the per-item skip flag was newly written. */
    updated: boolean;
}

/** One row of `/{movies,tv-shows,anime}/alias-targets` (id-keyed). */
export interface AliasTarget {
    tmdb_id: number;
    title: string;
    year: number;
    poster: string | null;
}

/** One row of `/albums/alias-targets` (token-keyed). */
export interface AlbumAliasTarget {
    token: string;
    title: string;
    artist: string | null;
    year: number;
    poster: string | null;
}

/** One row of `/books/alias-targets` (token-keyed). */
export interface BookAliasTarget {
    token: string;
    title: string;
    author: string | null;
    poster: string | null;
}

export interface AliasBindResult {
    bound: boolean;
    /** Number of new alias lines actually written (re-bind is a no-op). */
    added: number;
}
