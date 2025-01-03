import type {MediaGroup, MediaItem, MediaItemGroupData} from "@/types";
import {appendTVEpisode, appendTVSeason, diffTV} from "@/http/api";

export default function () {
    function tvHttpToMedia(tv: any): MediaItem {
        return {
            title: tv.title,
            img: tv.poster,
            score: tv.score,
            link: tv.link,
        }
    }

    async function getLostTV(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffTV()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.missing_tv_shows) {
            group.mediaItems.push(tvHttpToMedia(item))
        }

        return group
    }

    async function getContinuedTV(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const [httpSeasonRes, httpEpisodeRes] = await Promise.all([appendTVSeason(), appendTVEpisode()])
        if (!httpSeasonRes.success || !httpEpisodeRes.success) {
            group.valid = false
            return group
        }

        if (httpSeasonRes.data == null || httpEpisodeRes.data == null) {
            return group
        }

        const tvMap = new Map<string, any>()
        const lostSeasonMap = new Map<string, Set<number>>()
        for (const [key, value] of Object.entries(httpSeasonRes.data)) {
            const v = value as any
            tvMap.set(key, v.tv_show)

            const seasons = new Set<number>()
            const items = v.missing_seasons as any[]
            for (const season of items) {
                seasons.add(season.num as number)
            }
            lostSeasonMap.set(key, seasons)
        }
        for (const [key, value] of Object.entries(httpEpisodeRes.data)) {
            const v = value as any
            tvMap.set(key, v.tv_show)
            if (!lostSeasonMap.has(key)) {
                lostSeasonMap.set(key, new Set<number>())
            }

            const seasons = lostSeasonMap.get(key) as Set<number>
            const items = v.missing_seasons as any[]
            for (const season of items) {
                seasons.add(season.season_num as number)
            }
        }

        for (const [key, value] of tvMap) {
            const tv = tvHttpToMedia(value)
            const lostSeasons = Array.from(lostSeasonMap.get(key) as Set<number>)
            lostSeasons.sort((a, b) => a - b)
            tv.title = `${tv.title} - ${lostSeasons.map(num => `S${num}`).join(',')}`
            group.mediaItems.push(tv)
        }

        return group
    }

    async function getOutdatedTV(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffTV()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.extra_tv_shows) {
            group.mediaItems.push(tvHttpToMedia(item))
        }

        return group
    }

    const tv: MediaGroup = {
        name: "电视剧",
        mediaItemFunctionGroups: [
            {
                name: "最新",
                acquireData: getLostTV,
            },
            {
                name: "续集",
                acquireData: getContinuedTV,
            },
            {
                name: "过时",
                acquireData: getOutdatedTV,
            }
        ]
    }

    return {tv}
}