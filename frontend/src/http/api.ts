import {httpGet, httpPost} from "@/http/client";
import type {
    AlbumItem,
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
} from "@/types/api";

// RESTful, versioned API. Nginx proxies `/api/` to the Django backend.
const V1 = "/api/v1";

// Maps a library to its REST URL segment (tv -> tv-shows).
const IGNORE_SEGMENT: Record<IgnoreLibrary, string> = {
    tv: "tv-shows",
    anime: "anime",
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
