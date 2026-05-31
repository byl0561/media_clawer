import type {MediaGroup} from "@/types";
import {diffTV, tvSeriesGaps, tvSubtitleGaps} from "@/http/api";
import {
    buildGroup,
    buildShowSeries,
    buildShowSubtitleSeries,
    once,
} from "@/hooks/diffHelper";

export default function useTV(): MediaGroup {
    const loadDiff = once(diffTV);
    // Memoized like loadDiff so the Overview card re-mount doesn't re-hit
    // series-gaps on every navigation; catalog.refresh() still forces a reload.
    const loadSeries = once(tvSeriesGaps);
    const loadSubtitle = once(tvSubtitleGaps);

    return {
        name: "电视剧",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing, "tv")},
            {name: "续集", acquireSeries: () => buildShowSeries(loadSeries, "tv")},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
            {
                name: "字幕",
                overviewLabel: "缺失字幕",
                acquireSeries: () => buildShowSubtitleSeries(loadSubtitle, "tv"),
            },
        ],
    };
}
