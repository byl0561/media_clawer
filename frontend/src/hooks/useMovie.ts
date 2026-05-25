import type {MediaGroup, MediaItemGroupData} from "@/types";
import {diffMovie, movieCollectionGaps} from "@/http/api";
import {buildGroup, once, toMedia} from "@/hooks/diffHelper";

export default function useMovie(): MediaGroup {
    const loadDiff = once(diffMovie);
    // Memoized like loadDiff so re-mounting the Overview card (the router has
    // no keep-alive) doesn't re-hit collection-gaps on every navigation; a
    // real reload still goes through catalog.refresh().
    const loadGaps = once(movieCollectionGaps);

    async function getContinued(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {valid: true, mediaItems: []};
        const res = await loadGaps();
        if (!res.success) {
            group.valid = false;
            return group;
        }
        if (res.data == null) return group;
        for (const gap of res.data) {
            for (const item of gap.missing) {
                const media = toMedia(item);
                media.title = `[${gap.collection}] ${media.title}`;
                group.mediaItems.push(media);
            }
        }
        return group;
    }

    return {
        name: "电影",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing, "movie")},
            {name: "续集", acquireData: getContinued},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };
}
