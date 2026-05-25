import type {MediaGroup} from "@/types";
import {animeLocalGaps, diffAnime} from "@/http/api";
import {buildGroup, buildLocalGapGroup, once} from "@/hooks/diffHelper";

export default function useAnime(): MediaGroup {
    const loadDiff = once(diffAnime);
    // Memoized like loadDiff so the Overview card re-mount doesn't re-hit
    // local-gaps on every navigation; catalog.refresh() still forces a reload.
    const loadGaps = once(animeLocalGaps);

    return {
        name: "动漫",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing, "anime")},
            {name: "续集", acquireData: () => buildLocalGapGroup(loadGaps, "anime")},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };
}
