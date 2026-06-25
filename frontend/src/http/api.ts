import {httpGet, httpGetSSE, httpPost} from "@/http/client";
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

// RESTful, versioned API. Nginx proxies `/api/` to the FastAPI backend.
const V1 = "/api/v1";

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

// --- SSE-backed slow endpoints (no timeout risk) ------------------------

type OnProgress = (step: string, pct: number) => void;

export const diffMovie = (p?: OnProgress) => httpGetSSE<Diff<MovieItem>>(`${V1}/movies/diff`, p);
export const movieSeriesGaps = (p?: OnProgress) => httpGetSSE<MovieSeriesGap[]>(`${V1}/movies/series-gaps`, p);
export const movieSubtitleGaps = (p?: OnProgress) => httpGetSSE<MovieItem[]>(`${V1}/movies/subtitle-gaps`, p);

export const diffTV = (p?: OnProgress) => httpGetSSE<Diff<ShowItem>>(`${V1}/tv-shows/diff`, p);
export const tvSeriesGaps = (p?: OnProgress) => httpGetSSE<ShowSeriesGap[]>(`${V1}/tv-shows/series-gaps`, p);
export const tvSubtitleGaps = (p?: OnProgress) => httpGetSSE<SubtitleShowGap[]>(`${V1}/tv-shows/subtitle-gaps`, p);

export const diffAnime = (p?: OnProgress) => httpGetSSE<Diff<ShowItem>>(`${V1}/anime/diff`, p);
export const animeSeriesGaps = (p?: OnProgress) => httpGetSSE<ShowSeriesGap[]>(`${V1}/anime/series-gaps`, p);
export const animeSubtitleGaps = (p?: OnProgress) => httpGetSSE<SubtitleShowGap[]>(`${V1}/anime/subtitle-gaps`, p);

export const diffAlbum = (p?: OnProgress) => httpGetSSE<Diff<AlbumItem>>(`${V1}/albums/diff`, p);
export const albumLyricGaps = (p?: OnProgress) => httpGetSSE<AlbumLyricGap[]>(`${V1}/albums/lyric-gaps`, p);

export const diffBook = (p?: OnProgress) => httpGetSSE<Diff<BookItem>>(`${V1}/books/diff`, p);

// --- Fast JSON endpoints (plain httpGet / httpPost) ----------------------

export const ignoreMovieCollection = (collectionId: number) =>
    httpPost<IgnoreCollectionResult>(`${V1}/movies/ignore-collection`, {
        collection_id: collectionId,
    });

export const ignoreMovieSubtitle = (tmdbId: number) =>
    httpPost<IgnoreFlagResult>(`${V1}/movies/ignore-subtitle`, {tmdb_id: tmdbId});

export const ignoreAlbumLyric = (token: string) =>
    httpPost<IgnoreFlagResult>(`${V1}/albums/ignore-lyric`, {token});

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
