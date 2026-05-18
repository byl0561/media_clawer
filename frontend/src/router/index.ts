import {createRouter, createWebHistory} from "vue-router";

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

export default router;
