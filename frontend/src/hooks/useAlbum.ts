import type {MediaGroup} from "@/types";
import {diffAlbum} from "@/http/api";
import {buildGroup, once} from "@/hooks/diffHelper";

export default function () {
    const loadDiff = once(diffAlbum);

    const album: MediaGroup = {
        name: "专辑",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing)},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };

    return {album};
}
