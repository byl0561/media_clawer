import type {MediaGroup, MediaItemGroupData} from "@/types";
import {animeLocalGaps, diffAnime} from "@/http/api";
import {buildGroup, once, toMedia} from "@/hooks/diffHelper";

export default function () {
    const loadDiff = once(diffAnime);

    const getLostAnime = () => buildGroup(loadDiff, (d) => d.missing);
    const getOutdatedAnime = () => buildGroup(loadDiff, (d) => d.extra);

    async function getContinuedAnime(): Promise<MediaItemGroupData> {
        const group: MediaItemGroupData = {valid: true, mediaItems: []};
        const res = await animeLocalGaps();
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

    const anime: MediaGroup = {
        name: "动漫",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: getLostAnime},
            {name: "续集", acquireData: getContinuedAnime},
            {name: "过时", acquireData: getOutdatedAnime},
        ],
    };

    return {anime};
}
