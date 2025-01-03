import type {MediaGroup, MediaItem, MediaItemGroupData} from "@/types";
import {appendMovieCollection, diffMovie} from "@/http/api";

export default function () {
    function movieHttpToMedia(movie: any): MediaItem {
        return {
            title: movie.title,
            img: movie.poster,
            score: movie.score,
            link: movie.link,
        }
    }

    async function getLostMovie(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffMovie()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.missing_movies) {
            group.mediaItems.push(movieHttpToMedia(item))
        }

        return group
    }

    async function getContinuedMovie(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await appendMovieCollection()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const [key, value] of Object.entries(httpRes.data)) {
            const items = value as any[]
            for (const item of items) {
                const movie = movieHttpToMedia(item)
                movie.title = `[${key}] ${movie.title}`
                group.mediaItems.push(movie)
            }
        }

        return group
    }

    async function getOutdatedMovie(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffMovie()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.extra_movies) {
            group.mediaItems.push(movieHttpToMedia(item))
        }

        return group
    }

    const movie: MediaGroup = {
        name: "电影",
        mediaItemFunctionGroups: [
            {
                name: "最新",
                acquireData: getLostMovie,
            },
            {
                name: "续集",
                acquireData: getContinuedMovie,
            },
            {
                name: "过时",
                acquireData: getOutdatedMovie,
            }
        ]
    }

    return {movie}
}