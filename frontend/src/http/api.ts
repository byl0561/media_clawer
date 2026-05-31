import {httpGet, httpPost} from "@/http/client";
import type {
    AlbumAliasTarget,
    AlbumItem,
    AlbumLyricGap,
    AliasBindResult,
    AliasTarget,
    BindLibrary,
    BookAliasTarget,
    BookItem,
    Diff,
    IgnoreCollectionResult,
    IgnoreFlagResult,
    IgnoreLibrary,
    IgnoreOptions,
    IgnoreResult,
    IgnoreSelection,
    MovieItem,
    MovieSeriesGap,
    ShowItem,
    ShowSeriesGap,
    SubtitleShowGap,
    TmdbBindLibrary,
    TokenBindLibrary,
} from "@/types/api";

// RESTful, versioned API. Nginx proxies `/api/` to the Django backend.
const V1 = "/api/v1";

// Maps a library to its REST URL segment (tv -> tv-shows).
const IGNORE_SEGMENT: Record<IgnoreLibrary, string> = {
    tv: "tv-shows",
    anime: "anime",
};

const BIND_SEGMENT: Record<BindLibrary, string> = {
    movie: "movies",
    tv: "tv-shows",
    anime: "anime",
    album: "albums",
    book: "books",
};

export const diffMovie = () => httpGet<Diff<MovieItem>>(`${V1}/movies/diff`);
export const movieSeriesGaps = () =>
    httpGet<MovieSeriesGap[]>(`${V1}/movies/series-gaps`);
export const ignoreMovieCollection = (collectionId: number) =>
    httpPost<IgnoreCollectionResult>(`${V1}/movies/ignore-collection`, {
        collection_id: collectionId,
    });

export const diffTV = () => httpGet<Diff<ShowItem>>(`${V1}/tv-shows/diff`);
export const tvSeriesGaps = () =>
    httpGet<ShowSeriesGap[]>(`${V1}/tv-shows/series-gaps`);

export const diffAnime = () => httpGet<Diff<ShowItem>>(`${V1}/anime/diff`);
export const animeSeriesGaps = () =>
    httpGet<ShowSeriesGap[]>(`${V1}/anime/series-gaps`);

export const diffAlbum = () => httpGet<Diff<AlbumItem>>(`${V1}/albums/diff`);
export const diffBook = () => httpGet<Diff<BookItem>>(`${V1}/books/diff`);

// --- Subtitle / lyric gaps ----------------------------------------------

export const movieSubtitleGaps = () =>
    httpGet<MovieItem[]>(`${V1}/movies/subtitle-gaps`);
export const ignoreMovieSubtitle = (tmdbId: number) =>
    httpPost<IgnoreFlagResult>(`${V1}/movies/ignore-subtitle`, {tmdb_id: tmdbId});

export const tvSubtitleGaps = () =>
    httpGet<SubtitleShowGap[]>(`${V1}/tv-shows/subtitle-gaps`);
export const animeSubtitleGaps = () =>
    httpGet<SubtitleShowGap[]>(`${V1}/anime/subtitle-gaps`);

export const albumLyricGaps = () =>
    httpGet<AlbumLyricGap[]>(`${V1}/albums/lyric-gaps`);
export const ignoreAlbumLyric = (token: string) =>
    httpPost<IgnoreFlagResult>(`${V1}/albums/ignore-lyric`, {token});

// --- Per-show ignore dialogs (series + subtitle modes) ------------------

export const ignoreOptions = (
    library: IgnoreLibrary,
    tmdbId: number,
    mode: "series" | "subtitle" = "series",
) => {
    const segment = IGNORE_SEGMENT[library];
    const path =
        mode === "subtitle"
            ? `${segment}/subtitle-ignore-options`
            : `${segment}/ignore-options`;
    return httpGet<IgnoreOptions>(`${V1}/${path}?tmdb_id=${tmdbId}`);
};

export const applyIgnore = (
    library: IgnoreLibrary,
    tmdbId: number,
    selections: IgnoreSelection[],
    mode: "series" | "subtitle" = "series",
) => {
    const segment = IGNORE_SEGMENT[library];
    const path = mode === "subtitle" ? `${segment}/ignore-subtitle` : `${segment}/ignore`;
    return httpPost<IgnoreResult>(`${V1}/${path}`, {
        tmdb_id: tmdbId,
        selections,
    });
};

// Two response shapes — tmdb-id libraries vs token-keyed libraries — share
// the same endpoint name but differ in row schema.
export const aliasTargetsById = (library: TmdbBindLibrary) =>
    httpGet<AliasTarget[]>(`${V1}/${BIND_SEGMENT[library]}/alias-targets`);

export const aliasTargetsByToken = (library: TokenBindLibrary) =>
    httpGet<(AlbumAliasTarget | BookAliasTarget)[]>(
        `${V1}/${BIND_SEGMENT[library]}/alias-targets`,
    );

export const bindAliasById = (
    library: TmdbBindLibrary,
    tmdbId: number,
    aliases: string[],
) =>
    httpPost<AliasBindResult>(`${V1}/${BIND_SEGMENT[library]}/alias-bind`, {
        tmdb_id: tmdbId,
        aliases,
    });

export const bindAliasByToken = (
    library: TokenBindLibrary,
    token: string,
    aliases: string[],
) =>
    httpPost<AliasBindResult>(`${V1}/${BIND_SEGMENT[library]}/alias-bind`, {
        token,
        aliases,
    });
