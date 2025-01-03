import type {MediaGroup, MediaItem, MediaItemGroupData} from "@/types";
import {diffAlbum} from "@/http/api";

export default function () {
    function albumHttpToMedia(album: any): MediaItem {
        return {
            title: album.title,
            img: album.poster,
            score: album.score,
            link: album.link,
        }
    }

    async function getLostAlbum(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffAlbum()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.missing_albums) {
            group.mediaItems.push(albumHttpToMedia(item))
        }

        return group
    }

    async function getOutdatedAlbum(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffAlbum()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.extra_albums) {
            group.mediaItems.push(albumHttpToMedia(item))
        }

        return group
    }

    const album: MediaGroup = {
        name: "专辑",
        mediaItemFunctionGroups: [
            {
                name: "最新",
                acquireData: getLostAlbum,
            },
            {
                name: "过时",
                acquireData: getOutdatedAlbum,
            }
        ]
    }

    return {album}
}