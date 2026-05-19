/** UI-facing view models (server shapes live in `@/types/api`). */

import type {IgnoreLibrary} from "@/types/api";

/** Set only on TV/anime 续集 items: enables the per-poster ignore action. */
export interface IgnoreRef {
    library: IgnoreLibrary;
    tmdbId: number;
}

export interface MediaItem {
    title: string;
    img: string | null;
    score: number | null;
    link: string | null;
    ignore?: IgnoreRef;
}

export interface MediaItemGroupData {
    valid: boolean;
    mediaItems: MediaItem[];
}

export interface MediaItemFunctionGroup {
    name: string;
    acquireData: () => Promise<MediaItemGroupData>;
}

export interface MediaGroup {
    name: string;
    mediaItemFunctionGroups: MediaItemFunctionGroup[];
}
