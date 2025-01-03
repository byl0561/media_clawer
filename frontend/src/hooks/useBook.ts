import type {MediaGroup, MediaItem, MediaItemGroupData} from "@/types";
import {diffBook} from "@/http/api";

export default function () {
    function bookHttpToMedia(book: any): MediaItem {
        return {
            title: book.title,
            img: book.poster,
            score: book.score,
            link: book.link,
        }
    }

    async function getLostBook(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffBook()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.missing_books) {
            group.mediaItems.push(bookHttpToMedia(item))
        }

        return group
    }

    async function getOutdatedBook(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {
            valid: true,
            mediaItems: [],
        }
        const httpRes = await diffBook()
        if (!httpRes.success) {
            group.valid = false
            return group
        }

        if (httpRes.data == null) {
            return group
        }

        for (const item of httpRes.data.extra_books) {
            group.mediaItems.push(bookHttpToMedia(item))
        }

        return group
    }

    const book: MediaGroup = {
        name: "书籍",
        mediaItemFunctionGroups: [
            {
                name: "最新",
                acquireData: getLostBook,
            },
            {
                name: "过时",
                acquireData: getOutdatedBook,
            }
        ]
    }

    return {book}
}