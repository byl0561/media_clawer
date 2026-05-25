/** Server response shapes for the `/api/v1` endpoints. */

/** The two libraries with a 续集 ignore action. */
export type IgnoreLibrary = "tv" | "anime";

/** All three libraries that support the "最新" bind-alias action. */
export type BindLibrary = "movie" | "tv" | "anime";

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
    /** Present for TMDB/local shows (local-gaps); null for Douban/Bangumi. */
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

export interface CollectionGap {
    collection: string;
    missing: MovieItem[];
}

export interface SeasonRef {
    num: number;
    name: string;
}

export interface IncompleteSeason {
    season_num: number;
    season_name: string;
    local_max_episode: number;
    remote_max_episode: number;
}

export interface LocalGap {
    show: ShowItem;
    missing_seasons: SeasonRef[];
    incomplete_seasons: IncompleteSeason[];
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

/** One row of `/{movies,tv-shows,anime}/alias-targets`. */
export interface AliasTarget {
    tmdb_id: number;
    title: string;
    year: number;
    poster: string | null;
}

export interface AliasBindResult {
    bound: boolean;
    /** Number of new alias lines actually written (re-bind is a no-op). */
    added: number;
}
