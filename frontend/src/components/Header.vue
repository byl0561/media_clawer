<script setup lang="ts" />

<template>
  <header class="ht-header">
    <div class="container">
      <nav class="navbar navbar-default navbar-custom">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="navbar-header logo">
          <div><img class="logo" src="/images/logo.png" alt="" width="119" height="58"></div>
        </div>
        <!-- /.navbar-collapse -->
      </nav>
    </div>
  </header>
</template>

<style scoped>
header {
  position: absolute;
  z-index: 100;
  width: 100%;
  background: transparent url('/images/bg.jpg') no-repeat center;
  background-size: cover;
  -webkit-transition: all 0.5s ease-out;
  -moz-transition: all 0.5s ease-out;
  -o-transition: all 0.5s ease-out;
  transition: all 0.5s ease-out;
}
@media (max-width: 991px) {
  header {
    background-color: #0f2133;
  }
}

.ht-header {
  background-color: #0f2133;
}

.navbar {
  position: relative;
  min-height: 50px;
  margin-bottom: 20px;
  border: 1px solid transparent;
}
@media (min-width: 768px) {
  .navbar {
    border-radius: 0;
  }
}

.navbar-default {
  background-color: #f8f8f8;
}
header .navbar-default {
  margin-bottom: 0;
  padding: 30px 0;
  background-color: transparent;
  border: none;
  position: relative;
  -webkit-transition: all 0.5s ease-out;
  -moz-transition: all 0.5s ease-out;
  -o-transition: all 0.5s ease-out;
  transition: all 0.5s ease-out;
}
header#header-light .navbar-default {
  padding: 15px 0;
}
@media (min-width: 768px) {
  header .navbar-default {
    display: -webkit-flex;
    display: -moz-box;
    display: -ms-flexbox;
    display: flex;
    align-items: center;
    justify-content: flex-start;
  }
}
@media (max-width: 767px) {
  header .navbar-default {
    padding: 10px 0;
  }
}

@media (min-width: 768px) {
  .navbar-header {
    float: left;
  }
}
@media (max-width: 991px) {
  header .navbar-header {
    width: 100%;
  }
}
@media (max-width: 767px) {
  header .navbar-header {
    text-align: center;
    margin: 0 auto;
  }
}
</style>