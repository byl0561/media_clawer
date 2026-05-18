import type {MediaGroup} from "@/types";
import {animeLocalGaps, diffAnime} from "@/http/api";
import {buildGroup, buildLocalGapGroup, once} from "@/hooks/diffHelper";

export default function useAnime(): MediaGroup {
    const loadDiff = once(diffAnime);

    return {
        name: "动漫",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing)},
            {name: "续集", acquireData: () => buildLocalGapGroup(animeLocalGaps)},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };
}
