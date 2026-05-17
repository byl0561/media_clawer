import type {MediaGroup, MediaItemGroupData} from "@/types";
import {diffMovie, movieCollectionGaps} from "@/http/api";
import {buildGroup, once, toMedia} from "@/hooks/diffHelper";

export default function () {
    const loadDiff = once(diffMovie);

    const getLostMovie = () => buildGroup(loadDiff, (d) => d.missing);
    const getOutdatedMovie = () => buildGroup(loadDiff, (d) => d.extra);

    async function getContinuedMovie(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {valid: true, mediaItems: []};
        const res = await movieCollectionGaps();
        if (!res.success) {
            group.valid = false;
            return group;
        }
        if (res.data == null) return group;
        for (const entry of res.data) {
            for (const item of entry.missing) {
                const media = toMedia(item);
                media.title = `[${entry.collection}] ${media.title}`;
                group.mediaItems.push(media);
            }
        }
        return group;
    }

    const movie: MediaGroup = {
        name: "电影",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: getLostMovie},
            {name: "续集", acquireData: getContinuedMovie},
            {name: "过时", acquireData: getOutdatedMovie},
        ],
    };

    return {movie};
}
