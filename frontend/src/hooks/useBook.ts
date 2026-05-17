import type {MediaGroup} from "@/types";
import {diffBook} from "@/http/api";
import {buildGroup, once} from "@/hooks/diffHelper";

export default function () {
    const loadDiff = once(diffBook);

    const book: MediaGroup = {
        name: "书籍",
        mediaItemFunctionGroups: [
            {name: "最新", acquireData: () => buildGroup(loadDiff, (d) => d.missing)},
            {name: "过时", acquireData: () => buildGroup(loadDiff, (d) => d.extra)},
        ],
    };

    return {book};
}
