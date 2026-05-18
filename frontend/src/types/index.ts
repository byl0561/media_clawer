/** UI-facing view models (server shapes live in `@/types/api`). */

export interface MediaItem {
    title: string;
    img: string | null;
    score: number | null;
    link: string | null;
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
