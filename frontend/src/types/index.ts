/** UI-facing view models (server shapes live in `@/types/api`). */

import type {BindLibrary, IgnoreLibrary} from "@/types/api";

/** Set only on TV/anime 续集 items: enables the per-poster ignore action. */
export interface IgnoreRef {
    library: IgnoreLibrary;
    tmdbId: number;
}

/** Set only on 最新 items: enables the per-poster bind-alias action. */
export interface BindRef {
    library: BindLibrary;
    /** The rank title that will be written as an alias on the chosen local. */
    alias: string;
}

export interface MediaItem {
    title: string;
    img: string | null;
    score: number | null;
    link: string | null;
    ignore?: IgnoreRef;
    bind?: BindRef;
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
