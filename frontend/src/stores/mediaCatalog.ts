import {computed, shallowRef} from "vue";
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

// Count of data acquisitions currently in flight. Pages/cards wrap their
// loads in track(); the AppBar uses `refreshing` to spin + disable the
// refresh button (and stop it being spammed mid-reload).
const inFlight = shallowRef(0);
const refreshing = computed(() => inFlight.value > 0);

function track<T>(p: Promise<T>): Promise<T> {
    inFlight.value += 1;
    return p.finally(() => {
        inFlight.value -= 1;
    });
}

export function useMediaCatalog() {
    return {
        entries,
        version,
        refreshing,
        track,
        find: (key: string): CatalogEntry | undefined =>
            entries.value.find((entry) => entry.key === key),
        /** Drop cached responses and force every view to reload. */
        refresh(): void {
            entries.value = build();
            version.value += 1;
        },
        /**
         * Rebuild a single entry (fresh memoized loaders) so one failed
         * media type can retry without re-fetching the other four.
         */
        refreshEntry(key: string): void {
            const idx = FACTORIES.findIndex(([k]) => k === key);
            if (idx < 0) return;
            const [k, icon, factory] = FACTORIES[idx];
            const group = factory();
            const next = entries.value.slice();
            next[idx] = {key: k, icon, label: group.name, group};
            entries.value = next;
        },
    };
}
