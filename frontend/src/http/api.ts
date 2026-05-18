import {httpGet} from "@/http/client";
import type {
    AlbumItem,
    BookItem,
    CollectionGap,
    Diff,
    LocalGap,
    MovieItem,
    ShowItem,
} from "@/types/api";

// RESTful, versioned API. Nginx proxies `/api/` to the Django backend.
const V1 = "/api/v1";

export const diffMovie = () => httpGet<Diff<MovieItem>>(`${V1}/movies/diff`);
export const movieCollectionGaps = () =>
    httpGet<CollectionGap[]>(`${V1}/movies/collection-gaps`);

export const diffTV = () => httpGet<Diff<ShowItem>>(`${V1}/tv-shows/diff`);
export const tvLocalGaps = () => httpGet<LocalGap[]>(`${V1}/tv-shows/local-gaps`);

export const diffAnime = () => httpGet<Diff<ShowItem>>(`${V1}/anime/diff`);
export const animeLocalGaps = () => httpGet<LocalGap[]>(`${V1}/anime/local-gaps`);

export const diffAlbum = () => httpGet<Diff<AlbumItem>>(`${V1}/albums/diff`);
export const diffBook = () => httpGet<Diff<BookItem>>(`${V1}/books/diff`);
