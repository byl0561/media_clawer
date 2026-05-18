import {shallowRef} from "vue";
import type {MediaGroup} from "@/types";
import useMovie from "@/hooks/useMovie";
import useTV from "@/hooks/useTV";
import useAnime from "@/hooks/useAnime";
import useBook from "@/hooks/useBook";
import useAlbum from "@/hooks/useAlbum";

export interface CatalogEntry {
    /** route param + stable id */
    key: string;
    /** display name (from the group) */
    label: string;
    /** emoji glyph for the overview card */
    icon: string;
    group: MediaGroup;
}

const FACTORIES: Array<[string, string, () => MediaGroup]> = [
    ["movie", "🎬", useMovie],
    ["tv", "📺", useTV],
    ["anime", "🌸", useAnime],
    ["book", "📚", useBook],
    ["album", "💿", useAlbum],
];

function build(): CatalogEntry[] {
    return FACTORIES.map(([key, icon, factory]) => {
        const group = factory();
        return {key, icon, label: group.name, group};
    });
}

// Singleton: hooks (and their memoized loaders) are created once so the
// Overview and Library routes share the same in-flight/resolved requests.
const entries = shallowRef<CatalogEntry[]>(build());
// Bumped on refresh; pages watch it to re-fetch.
const version = shallowRef(0);

export function useMediaCatalog() {
    return {
        entries,
        version,
        find: (key: string): CatalogEntry | undefined =>
            entries.value.find((entry) => entry.key === key),
        /** Drop cached responses and force every view to reload. */
        refresh(): void {
            entries.value = build();
            version.value += 1;
        },
    };
}
