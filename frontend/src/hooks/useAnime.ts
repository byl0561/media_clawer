import type {MediaGroup} from "@/types";
import {animeSeriesGaps, animeSubtitleGaps, diffAnime} from "@/http/api";
import {
    buildGroup,
    buildShowSeries,
    buildShowSubtitleSeries,
    once,
} from "@/hooks/diffHelper";

export default function useAnime(): MediaGroup {
    const loadDiff = once(diffAnime);
    // Memoized like loadDiff so the Overview card re-mount doesn't re-hit
    // series-gaps on every navigation; catalog.refresh() still forces a reload.
    const loadSeries = once(animeSeriesGaps);
    const loadSubtitle = once(animeSubtitleGaps);

    return {
        name: "动漫",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: (p) => buildGroup(loadDiff, (d) => d.missing, "anime", p)},
            {name: "续集", acquireSeries: (p) => buildShowSeries(loadSeries, "anime", p)},
            {name: "过时", acquireData: (p) => buildGroup(loadDiff, (d) => d.extra, undefined, p)},
            {
                name: "字幕",
                overviewLabel: "缺失字幕",
                acquireSeries: (p) => buildShowSubtitleSeries(loadSubtitle, "anime", p),
            },
        ],
    };
}
