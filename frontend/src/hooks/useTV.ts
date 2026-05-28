import type {MediaGroup} from "@/types";
import {diffTV, tvSeriesGaps} from "@/http/api";
import {buildGroup, buildShowSeries, once} from "@/hooks/diffHelper";

export default function useTV(): MediaGroup {
    const loadDiff = once(diffTV);
    // Memoized like loadDiff so the Overview card re-mount doesn't re-hit
    // series-gaps on every navigation; catalog.refresh() still forces a reload.
    const loadSeries = once(tvSeriesGaps);

    return {
        name: "电视剧",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing, "tv")},
            {name: "续集", acquireSeries: () => buildShowSeries(loadSeries, "tv")},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };
}
