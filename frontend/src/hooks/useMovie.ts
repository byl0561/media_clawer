import type {MediaGroup} from "@/types";
import {diffMovie, movieSeriesGaps, movieSubtitleGaps} from "@/http/api";
import {
    buildGroup,
    buildMovieSeries,
    buildMovieSubtitleGroup,
    once,
} from "@/hooks/diffHelper";

export default function useMovie(): MediaGroup {
    const loadDiff = once(diffMovie);
    // Memoized like loadDiff so re-mounting the Overview card (the router has
    // no keep-alive) doesn't re-hit series-gaps on every navigation; a real
    // reload still goes through catalog.refresh().
    const loadSeries = once(movieSeriesGaps);
    const loadSubtitle = once(movieSubtitleGaps);

    return {
        name: "电影",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing, "movie")},
            {name: "续集", acquireSeries: () => buildMovieSeries(loadSeries)},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
            {
                name: "字幕",
                overviewLabel: "缺失字幕",
                acquireData: () => buildMovieSubtitleGroup(loadSubtitle),
            },
        ],
    };
}
