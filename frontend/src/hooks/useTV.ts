import type {MediaGroup} from "@/types";
import {diffTV, tvLocalGaps} from "@/http/api";
import {buildGroup, buildLocalGapGroup, once} from "@/hooks/diffHelper";

export default function useTV(): MediaGroup {
    const loadDiff = once(diffTV);
    // Memoized like loadDiff so the Overview card re-mount doesn't re-hit
    // local-gaps on every navigation; catalog.refresh() still forces a reload.
    const loadGaps = once(tvLocalGaps);

    return {
        name: "电视剧",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing, "tv")},
            {name: "续集", acquireData: () => buildLocalGapGroup(loadGaps, "tv")},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };
}
