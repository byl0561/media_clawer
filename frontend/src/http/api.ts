import {httpGet, httpPost} from "@/http/client";
import type {
    AlbumAliasTarget,
    AlbumItem,
    AliasBindResult,
    AliasTarget,
    BindLibrary,
    BookAliasTarget,
    BookItem,
    CollectionGap,
    Diff,
    IgnoreLibrary,
    IgnoreOptions,
    IgnoreResult,
    IgnoreSelection,
    LocalGap,
    MovieItem,
    ShowItem,
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
export const movieCollectionGaps = () =>
    httpGet<CollectionGap[]>(`${V1}/movies/collection-gaps`);

export const diffTV = () => httpGet<Diff<ShowItem>>(`${V1}/tv-shows/diff`);
export const tvLocalGaps = () => httpGet<LocalGap[]>(`${V1}/tv-shows/local-gaps`);

export const diffAnime = () => httpGet<Diff<ShowItem>>(`${V1}/anime/diff`);
export const animeLocalGaps = () => httpGet<LocalGap[]>(`${V1}/anime/local-gaps`);

export const diffAlbum = () => httpGet<Diff<AlbumItem>>(`${V1}/albums/diff`);
export const diffBook = () => httpGet<Diff<BookItem>>(`${V1}/books/diff`);

export const ignoreOptions = (library: IgnoreLibrary, tmdbId: number) =>
    httpGet<IgnoreOptions>(
        `${V1}/${IGNORE_SEGMENT[library]}/ignore-options?tmdb_id=${tmdbId}`,
    );

export const applyIgnore = (
    library: IgnoreLibrary,
    tmdbId: number,
    selections: IgnoreSelection[],
) =>
    httpPost<IgnoreResult>(`${V1}/${IGNORE_SEGMENT[library]}/ignore`, {
        tmdb_id: tmdbId,
        selections,
    });

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
