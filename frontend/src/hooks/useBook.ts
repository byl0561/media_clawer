import type {MediaGroup} from "@/types";
import {diffBook} from "@/http/api";
import {buildGroup, once} from "@/hooks/diffHelper";

export default function useBook(): MediaGroup {
    const loadDiff = once(diffBook);

    return {
        name: "书籍",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing, "book")},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };
}
