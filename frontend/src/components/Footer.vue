<script setup lang="ts">
const year = new Date().getFullYear();
</script>

<template>
  <!-- footer section-->
  <footer class="ht-footer">
    <div class="ft-copyright">
      <p>Copyright &nbsp;©&nbsp;Lava&nbsp;{{year}}</p>
    </div>
  </footer>
  <!-- end of footer section-->
</template>

<style scoped>
footer {
  background: url('/images/bg.jpg') no-repeat center;
  background-size: cover;
}

footer .ft-copyright {
  display: -webkit-flex;
  display: -moz-box;
  display: -ms-flexbox;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #405266;
  padding-top: 10px;
  padding-bottom: 10px;
  background-color: #020d18;
  -moz-opacity: 0.7;
  -khtml-opacity: 0.7;
  -webkit-opacity: 0.7;
  opacity: 0.7;
  -ms-filter: progid:DXImageTransform.Microsoft.Alpha(opacity=70);
  filter: alpha(opacity=70);
  padding-left: 380px;
  padding-right: 380px;
  text-align: center;
}
footer .ft-copyright p {
  margin: 0 auto;
}
@media (max-width: 1200px) {
  footer .ft-copyright {
    padding-left: 125px;
    padding-right: 125px;
  }
}
@media (max-width: 767px) {
  footer .ft-copyright {
    padding: 15px;
    display: flex;
    flex-direction: column;
    align-items: inherit;
  }
}
</style>