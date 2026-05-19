import {createRouter, createWebHistory} from "vue-router";
import {useMediaCatalog} from "@/stores/mediaCatalog";

const BRAND = "MediaGap";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: "/",
            name: "overview",
            component: () => import("@/pages/OverviewPage.vue"),
        },
        {
            path: "/library/:type",
            name: "library",
            component: () => import("@/pages/LibraryPage.vue"),
        },
        {path: "/:pathMatch(.*)*", redirect: "/"},
    ],
    scrollBehavior() {
        return {top: 0};
    },
});

// Keep the document title in sync so browser history / tabs are legible.
router.afterEach((to) => {
    if (to.name === "library") {
        const entry = useMediaCatalog().find(String(to.params.type));
        document.title = entry ? `${entry.label} · ${BRAND}` : BRAND;
    } else if (to.name === "overview") {
        document.title = `概览 · ${BRAND}`;
    } else {
        document.title = BRAND;
    }
});

export default router;
