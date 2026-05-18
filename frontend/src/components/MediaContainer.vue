<script setup lang="ts">
import MediaItemsGroup from "@/components/MediaItemsGroup.vue";
import useMovie from "@/hooks/useMovie";
import useTV from "@/hooks/useTV";
import useAnime from "@/hooks/useAnime";
import useBook from "@/hooks/useBook";
import useAlbum from "@/hooks/useAlbum";

const groups = [useMovie(), useTV(), useAnime(), useBook(), useAlbum()];
</script>

<template>
  <div class="movie-items">
    <div class="container">
      <div class="row ipad-width">
        <div class="col-md">
          <MediaItemsGroup
            v-for="group in groups"
            :key="group.name"
            :media-group="group"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.movie-items {
  padding: 180px 0 70px 0;
  background-color: #020d18;
}

.row {
  margin-left: -15px;
  margin-right: -15px;
}

@media (max-width: 767px) {
  .ipad-width {
    max-width: 550px;
    margin: 0 auto;
  }
}

.col-md {
  position: relative;
  min-height: 1px;
  padding-left: 15px;
  padding-right: 15px;
}
@media (min-width: 992px) {
  .col-md {
    float: left;
    width: 100%;
  }
}
</style>
