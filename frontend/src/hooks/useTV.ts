import type {MediaGroup} from "@/types";
import {diffTV, tvLocalGaps} from "@/http/api";
import {buildGroup, buildLocalGapGroup, once} from "@/hooks/diffHelper";

export default function useTV(): MediaGroup {
    const loadDiff = once(diffTV);

    return {
        name: "电视剧",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing)},
            {name: "续集", acquireData: () => buildLocalGapGroup(tvLocalGaps)},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };
}
