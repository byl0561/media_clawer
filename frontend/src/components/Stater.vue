<script setup lang="ts">
const {state} = defineProps<{state:boolean}>()
</script>

<template>
  <div id="preloader">
    <div id="status">
        <img v-if="state" src="/images/success.png" alt="success"/>
        <img v-else src="/images/fail.png" alt="fail"/>
    </div>
  </div>
</template>

<style scoped>
#preloader {
  height: 100%;
  z-index: 99999;
  text-align: center;
}
#status {
  position: relative;
  width: 70px;
  height: 70px;
  top: 35%;
  margin: 0 auto;
  right: 35px;
}

#status img {
  position: absolute;
  width: 70px;
  height: 70px;
}
</style>