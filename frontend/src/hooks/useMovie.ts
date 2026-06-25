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
            {name: "最新", acquireData: (p) => buildGroup(loadDiff, (d) => d.missing, "movie", p)},
            {name: "续集", acquireSeries: (p) => buildMovieSeries(loadSeries, p)},
            {name: "过时", acquireData: (p) => buildGroup(loadDiff, (d) => d.extra, undefined, p)},
            {
                name: "字幕",
                overviewLabel: "缺失字幕",
                acquireData: (p) => buildMovieSubtitleGroup(loadSubtitle, p),
            },
        ],
    };
}
