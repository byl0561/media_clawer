<script setup lang="ts">
import type {MediaGroup, MediaItemGroupData} from "@/types";
import {onMounted, ref} from "vue";
import {Swiper, SwiperSlide} from 'swiper/vue'
import {Pagination} from 'swiper/modules'
import 'swiper/css';
import 'swiper/css/pagination'
import Loader from "@/components/Loader.vue";
import Stater from "@/components/Stater.vue";

const {mediaGroup} = defineProps<{mediaGroup:MediaGroup}>()
let loading = ref<boolean>(false);
let activeIndex = ref<Number>(0)
let successEmpty = ref<boolean>(false);
let activeData = ref<MediaItemGroupData>({
  valid: false,
  mediaItems: [],
})

const swiperBreakpoint:any = {}
for (let i = 0; i < 20; i++) {
  swiperBreakpoint[i * 384] = {
    slidesPerView: i + 1,
    slidesPerGroup: i + 1,
  }
}

async function onActive(index: number) {
  activeIndex.value = index
  loading.value = true
  try {
    activeData.value = await mediaGroup.mediaItemFunctionGroups[index].acquireData();
  } catch (error) {
    activeData.value = {
      valid: false,
      mediaItems: [],
    };
  } finally {
    loading.value = false;
  }
}

function getImgUrl(url: string | null): string {
  if (url == null)
    return "/images/404.png"

  if (url.startsWith('/api')) {
    return url;
  }
  if (url.startsWith('/')) {
    return `/api${url}`
  }

  return `https://images.weserv.nl/?url=${url}`
}

onMounted(async () => {
  for (let i = 0; i < mediaGroup.mediaItemFunctionGroups.length; i++) {
    await onActive(0)
    if (!activeData.value.valid || activeData.value.mediaItems.length > 0) {
      break
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
    mediaGroup.mediaItemFunctionGroups.splice(i, 1);
    i--
  }
  if (mediaGroup.mediaItemFunctionGroups.length == 0) {
    successEmpty.value = true;
  }
})
</script>

<template>
  <div class="title-hd">
    <h2>{{mediaGroup.name}}</h2>
  </div>
  <div class="tabs">
    <ul class="tab-links" v-show="!successEmpty">
      <li v-for="(itemGroup, index) in mediaGroup.mediaItemFunctionGroups" :key="itemGroup.name"
          :class="{active: activeIndex === index}"><a href="javascript:void(0)" @click="onActive(index)">{{itemGroup.name}}</a></li>
    </ul>
    <div class="tab-content">
      <div class="tab">
        <div class="row">
          <template v-if="loading">
            <Loader/>
          </template>
          <template v-else-if="successEmpty">
            <Stater :state="true" />
          </template>
          <template v-else-if="!activeData.valid">
            <Stater :state="false" />
          </template>
          <template v-else-if="activeData.mediaItems.length == 0">
            <Stater :state="true" />
          </template>
          <template v-else>
            <swiper
              :modules = "[Pagination]"
              :breakpoints="swiperBreakpoint"
              :space-between="20"
              :pagination="{
                el: '.swiper-pagination',
                clickable: true,
                bulletElement: 'div',
              }"
          >
            <div class="swiper-pagination" />
            <swiper-slide v-for="(mediaItem, index) in activeData.mediaItems" :key="index">
              <div class="movie-item">
                <div class="mv-img">
                  <img :src="getImgUrl(mediaItem.img)" alt="" />
                </div>
                <div class="title-in">
                  <h6><a :href="mediaItem.link == null ? '#' : mediaItem.link" target="_blank">{{mediaItem.title}}</a></h6>
                  <p v-show="mediaItem.score"><i class="ion-android-star"></i><span>{{mediaItem.score}}</span> /10</p>
                </div>
              </div>
            </swiper-slide>
          </swiper>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.title-hd {
  display: -webkit-flex;
  display: -moz-box;
  display: -ms-flexbox;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 25px;
}
.title-hd h2 {
  font-family: 'Dosis', sans-serif;
  font-size: 24px;
  color: #ffffff;
  font-weight: bold;
  text-transform: uppercase;
}
@media (max-width: 767px) {
  .title-hd h2 {
    margin: 0;
  }
}

.tabs {
  margin-bottom: 20px;
  overflow: hidden;
}
.tabs ul.tab-links {
  display: -webkit-flex;
  display: -moz-box;
  display: -ms-flexbox;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 25px;
}
.tabs ul.tab-links li {
  margin-right: 20px;
  font-family: 'Dosis', sans-serif;
  font-size: 14px;
  color: #abb7c4;
  font-weight: bold;
  text-transform: uppercase;
}
.tabs ul.tab-links li a:hover {
  color: #dcf836;
}
.tabs ul.tab-links li.active a {
  color: #dcf836;
}

.tab-links {
  position: relative;
}

.row {
  margin-left: -15px;
  margin-right: -15px;
  height: 360px;
}

.movie-item {
  position: relative;
  margin-right: 30px;
  -webkit-border-radius: 5px;
  -moz-border-radius: 5px;
  border-radius: 5px;
}
@media (max-width: 767px) {
  .movie-item {
    display: inherit;
    margin-right: 0px;
  }
}
.movie-item .mv-img {
  position: relative;
  max-height: 300px;
  width: 100%;
  aspect-ratio: 7 / 10;
  overflow: hidden;
}
.movie-item .mv-img:after {
  box-shadow: inset -5px -50px 100px -15px #000000;
  -webkit-box-shadow: inset -5px -50px 100px -15px #000000;
  -moz-box-shadow: inset -5px -50px 100px -15px #000000;
  -o-box-shadow: inset -5px -50px 100px -15px #000000;
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  content: "";
}
.movie-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  -webkit-transition: all 0.5s ease-out;
  -moz-transition: all 0.5s ease-out;
  -o-transition: all 0.5s ease-out;
  transition: all 0.5s ease-out;
}
.movie-item .title-in {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-left: 30px;
  margin-bottom: 20px;
  bottom: 0;
  left: 0;
  position: absolute;
}
@media (max-width: 767px) {
  .movie-item .title-in {
    margin-left: 60px;
  }
}
.movie-item .title-in h6 a {
  font-family: 'Dosis', sans-serif;
  font-size: 14px;
  color: #ffffff;
  font-weight: bold;
  text-transform: uppercase;
}
.movie-item .title-in p {
  font-size: 12px;
  color: #ffffff;
}
.movie-item .title-in p i {
  color: #f5b50a;
  font-size: 22px;
}
.movie-item .title-in p span {
  font-weight: 400;
  font-size: 18px;
}
.movie-item:hover img {
  -webkit-transition: all 0.5s ease-out;
  -moz-transition: all 0.5s ease-out;
  -o-transition: all 0.5s ease-out;
  transition: all 0.5s ease-out;
  -moz-opacity: 0.25;
  -khtml-opacity: 0.25;
  -webkit-opacity: 0.25;
  opacity: 0.25;
  -ms-filter: progid:DXImageTransform.Microsoft.Alpha(opacity=25);
  filter: alpha(opacity=25);
}
.movie-items .movie-item:hover h6 a {
  color: #dcf836;
}

@font-face {
  font-family: "Ionicons";
  src: url("https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.0/fonts/ionicons.eot");
  src: url("https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.0/fonts/ionicons.eot") format("embedded-opentype"), url("https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.0/fonts/ionicons.ttf") format("truetype"), url("https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.0/fonts/ionicons.woff") format("woff"), url("https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.0/fonts/ionicons.svg") format("svg");
  font-weight: normal;
  font-style: normal;
}
.ion-android-star:before {
  content: "\f2fc";
  display: inline-block;
  font-family: "Ionicons";
  font-style: normal;
  font-weight: normal;
  font-variant: normal;
  text-transform: none;
  text-rendering: auto;
  line-height: 1;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>

<style>
.swiper-pagination {
  position: static;
  margin-top: 15px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center
}
.swiper-pagination-bullet {
  background-color: white;
  opacity: 1;
}
.swiper-pagination-bullet-active {
  background-color: #dcf836;
  opacity: 1;
}
</style>