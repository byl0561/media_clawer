import type {MediaGroup} from "@/types";
import {albumLyricGaps, diffAlbum} from "@/http/api";
import {buildAlbumLyricGroup, buildGroup, once} from "@/hooks/diffHelper";

export default function useAlbum(): MediaGroup {
    const loadDiff = once(diffAlbum);
    const loadLyric = once(albumLyricGaps);

    return {
        name: "专辑",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: (p) => buildGroup(loadDiff, (d) => d.missing, "album", p)},
            {name: "过时", acquireData: (p) => buildGroup(loadDiff, (d) => d.extra, undefined, p)},
            {
                name: "歌词",
                overviewLabel: "缺失歌词",
                acquireData: (p) => buildAlbumLyricGroup(loadLyric, p),
            },
        ],
    };
}
