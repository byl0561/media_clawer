import type {MediaGroup, MediaItemGroupData} from "@/types";
import {diffTV, tvLocalGaps} from "@/http/api";
import {buildGroup, once, toMedia} from "@/hooks/diffHelper";

export default function () {
    const loadDiff = once(diffTV);

    const getLostTV = () => buildGroup(loadDiff, (d) => d.missing);
    const getOutdatedTV = () => buildGroup(loadDiff, (d) => d.extra);

    async function getContinuedTV(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {valid: true, mediaItems: []};
        const res = await tvLocalGaps();
        if (!res.success) {
            group.valid = false;
            return group;
        }
        if (res.data == null) return group;
        for (const entry of res.data) {
            const seasons = new Set<number>();
            for (const s of entry.missing_seasons) seasons.add(s.num);
            for (const s of entry.incomplete_seasons) seasons.add(s.season_num);
            const sorted = Array.from(seasons).sort((a, b) => a - b);
            const media = toMedia(entry.show);
            media.title = `${media.title} - ${sorted.map((n) => `S${n}`).join(",")}`;
            group.mediaItems.push(media);
        }
        return group;
    }

    const tv: MediaGroup = {
        name: "电视剧",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: getLostTV},
            {name: "续集", acquireData: getContinuedTV},
            {name: "过时", acquireData: getOutdatedTV},
        ],
    };

    return {tv};
}
