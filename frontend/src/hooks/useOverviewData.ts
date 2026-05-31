/**
 * Drives the Overview page: loads every catalog entry's tab counts once and
 * exposes both the per-card breakdown and the cross-library aggregate the
 * hero band shows. Loading is centralised here (instead of each card fetching
 * itself) so the totals are derivable; the per-entry loaders are still
 * once()-memoized, so revisiting the page is cheap.
 */
import {computed, onMounted, ref, watch} from "vue";
import type {Ref} from "vue";
import {useMediaCatalog} from "@/stores/mediaCatalog";
import type {CatalogEntry} from "@/stores/mediaCatalog";

export interface CardCount {
    name: string;
    value: number | null;
}

export interface CardState {
    entry: CatalogEntry;
    status: "loading" | "ok" | "error";
    counts: CardCount[];
}

export interface OverviewTotals {
    /** 最新 + 续集 + 过时 across every library. */
    all: number;
    latest: number;
    sequel: number;
    outdated: number;
}

export function useOverviewData(): {
    cards: Ref<CardState[]>;
    totals: Ref<OverviewTotals>;
    anyLoading: Ref<boolean>;
} {
    const catalog = useMediaCatalog();
    const cards = ref<CardState[]>([]);

    async function loadEntry(entry: CatalogEntry): Promise<CardState> {
        const tabs = entry.group.mediaItemFunctionGroups;
        const results = await Promise.all(
            tabs.map((tab) => {
                // 续集 tabs return a series payload (rows); everything else
                // returns the legacy flat items group. Reduce both to a count.
                if (tab.acquireSeries) {
                    return tab
                        .acquireSeries()
                        .then((d) => (d.valid ? d.rows.length : null))
                        .catch(() => null);
                }
                if (tab.acquireData) {
                    return tab
                        .acquireData()
                        .then((d) => (d.valid ? d.mediaItems.length : null))
                        .catch(() => null);
                }
                return Promise.resolve<number | null>(null);
            }),
        );
        const counts: CardCount[] = tabs.map((tab, i) => ({
            // Use the tab's overview-specific label when set (e.g. tab name
            // "字幕" displays as "缺失字幕" on the overview).
            name: tab.overviewLabel ?? tab.name,
            value: results[i],
        }));
        const status = results.every((r) => r == null) ? "error" : "ok";
        return {entry, status, counts};
    }

    async function load(): Promise<void> {
        const list = catalog.entries.value;
        cards.value = list.map((entry) => ({
            entry,
            status: "loading",
            counts: [],
        }));
        // Resolve each card independently so they fill in progressively;
        // reassigning the array (not mutating an index) keeps it reactive.
        await Promise.all(
            list.map(async (entry, i) => {
                const next = await loadEntry(entry);
                const copy = cards.value.slice();
                copy[i] = next;
                cards.value = copy;
            }),
        );
    }

    onMounted(() => catalog.track(load()));
    // refresh() rebuilds entries and refreshEntry() replaces one — both swap
    // the entries array identity, so watching it covers every reload path
    // (and fires exactly once per reload).
    watch(catalog.entries, () => catalog.track(load()));

    function sumWhere(pred: (c: CardCount) => boolean): number {
        return cards.value.reduce(
            (acc, card) =>
                acc +
                card.counts.reduce(
                    (a, c) => a + (pred(c) && c.value != null ? c.value : 0),
                    0,
                ),
            0,
        );
    }

    const totals = computed<OverviewTotals>(() => {
        const latest = sumWhere((c) => c.name === "最新");
        const sequel = sumWhere((c) => c.name === "续集");
        const outdated = sumWhere((c) => c.name === "过时");
        return {latest, sequel, outdated, all: latest + sequel + outdated};
    });

    // Empty == not yet loaded (before onMounted), so the hero shows its
    // skeleton from first paint instead of flashing zeros for a frame.
    const anyLoading = computed(
        () =>
            cards.value.length === 0 ||
            cards.value.some((c) => c.status === "loading"),
    );

    return {cards, totals, anyLoading};
}
