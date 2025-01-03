export interface MediaItem {
    title: string;
    img: string;
    score: number;
    link: string;
}

export interface MediaItemGroupData {
    valid: boolean,
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