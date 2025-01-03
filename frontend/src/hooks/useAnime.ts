import type {MediaGroup, MediaItem, MediaItemGroupData} from "@/types";
import {appendAnimeEpisode, appendAnimeSeason, diffAnime} from "@/http/api";

export default function () {
    function animeHttpToMedia(anime: any): MediaItem {
        return {
            title: anime.title,
            img: anime.poster,
            score: anime.score,
            link: anime.link,
        }
    }

    async function getLostAnime(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffAnime()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.missing_animates) {
            group.mediaItems.push(animeHttpToMedia(item))
        }

        return group
    }

    async function getContinuedAnime(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const [httpSeasonRes, httpEpisodeRes] = await Promise.all([appendAnimeSeason(), appendAnimeEpisode()])
        if (!httpSeasonRes.success || !httpEpisodeRes.success) {
            group.valid = false
            return group
        }

        if (httpSeasonRes.data == null || httpEpisodeRes.data == null) {
            return group
        }

        const animeMap = new Map<string, any>()
        const lostSeasonMap = new Map<string, Set<number>>()
        for (const [key, value] of Object.entries(httpSeasonRes.data)) {
            const v = value as any
            animeMap.set(key, v.tv_show)

            const seasons = new Set<number>()
            const items = v.missing_seasons as any[]
            for (const season of items) {
                seasons.add(season.num as number)
            }
            lostSeasonMap.set(key, seasons)
        }
        for (const [key, value] of Object.entries(httpEpisodeRes.data)) {
            const v = value as any
            animeMap.set(key, v.tv_show)
            if (!lostSeasonMap.has(key)) {
                lostSeasonMap.set(key, new Set<number>())
            }

            const seasons = lostSeasonMap.get(key) as Set<number>
            const items = v.missing_seasons as any[]
            for (const season of items) {
                seasons.add(season.season_num as number)
            }
        }

        for (const [key, value] of animeMap) {
            const anime = animeHttpToMedia(value)
            const lostSeasons = Array.from(lostSeasonMap.get(key) as Set<number>)
            lostSeasons.sort((a, b) => a - b)
            anime.title = `${anime.title} - ${lostSeasons.map(num => `S${num}`).join(',')}`
            group.mediaItems.push(anime)
        }

        return group
    }

    async function getOutdatedAnime(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffAnime()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.extra_animates) {
            group.mediaItems.push(animeHttpToMedia(item))
        }

        return group
    }

    const anime: MediaGroup = {
        name: "动漫",
        mediaItemFunctionGroups: [
            {
                name: "最新",
                acquireData: getLostAnime,
            },
            {
                name: "续集",
                acquireData: getContinuedAnime,
            },
            {
                name: "过时",
                acquireData: getOutdatedAnime,
            }
        ]
    }

    return {anime}
}