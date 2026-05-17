import type {ResponseWrapper} from "@/http/httpInstance";
import instance from "@/http/httpInstance";

// RESTful, versioned API. Nginx proxies `/api/` to the Django backend.
const V1 = "/api/v1";

export async function diffMovie(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/movies/diff`)
}

export async function movieCollectionGaps(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/movies/collection-gaps`)
}

export async function diffTV(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/tv-shows/diff`)
}

export async function tvLocalGaps(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/tv-shows/local-gaps`)
}

export async function diffAnime(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/anime/diff`)
}

export async function animeLocalGaps(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/anime/local-gaps`)
}

export async function diffAlbum(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/albums/diff`)
}

export async function diffBook(): Promise<ResponseWrapper> {
    return await instance.get(`${V1}/books/diff`)
}
