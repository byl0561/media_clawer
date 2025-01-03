import type {ResponseWrapper} from "@/http/httpInstance";
import instance from "@/http/httpInstance";

export async function diffMovie(): Promise<ResponseWrapper> {
    return await instance.get("/api/movie/douban250/diff")
}

export async function appendMovieCollection(): Promise<ResponseWrapper> {
    return await instance.get("/api/movie/local/collection/complete")
}

export async function diffTV(): Promise<ResponseWrapper> {
    return await instance.get("/api/tv/douban100/diff")
}

export async function appendTVSeason(): Promise<ResponseWrapper> {
    return await instance.get("/api/tv/local/season/missing")
}

export async function appendTVEpisode(): Promise<ResponseWrapper> {
    return await instance.get("/api/tv/local/episode/missing")
}

export async function diffAnime(): Promise<ResponseWrapper> {
    return await instance.get("/api/anime/bangumi/diff")
}

export async function appendAnimeSeason(): Promise<ResponseWrapper> {
    return await instance.get("/api/anime/local/season/missing")
}

export async function appendAnimeEpisode(): Promise<ResponseWrapper> {
    return await instance.get("/api/anime/local/episode/missing")
}

export async function diffAlbum(): Promise<ResponseWrapper> {
    return await instance.get("/api/album/douban250/diff")
}

export async function diffBook(): Promise<ResponseWrapper> {
    return await instance.get("/api/book/douban250/diff")
}