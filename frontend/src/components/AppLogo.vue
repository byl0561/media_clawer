<template>
  <!--
    MediaGap 图标：断口圆环（顶部 80° 缺口 = "gap"）+ 播放三角形（= "media"）
    ViewBox 36×36，白色描边，容器提供紫色背景
    缺口角度：从 SVG 220° 到 320°，对称于 270°（顶部）
  -->
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style="display:block;width:100%;height:100%"
    aria-hidden="true"
  >
    <!--
      圆弧：center(18,18) r=12
      220° → x=18+12cos(220°)=8.81, y=18+12sin(220°)=10.28
      320° → x=18+12cos(320°)=27.19, y=10.28
      从 320° 顺时针（sweep=1）走大弧（large=1）到 220° = 260° 弧，顶部留 80° 缺口
    -->
    <path
      d="M 27.19,10.28 A 12,12 0 1,1 8.81,10.28"
      stroke="white"
      stroke-width="2.8"
      stroke-linecap="round"
      fill="none"
    />
    <!-- 缺口中心的小强调点（顶部，y=6） -->
    <circle cx="18" cy="6" r="1.6" fill="white" opacity="0.45"/>
    <!--
      播放三角形：tip(26,18), left-top(13,11), left-bottom(13,25)
      所有顶点距中心 < 10.6（圆弧内径），确保不溢出环内
    -->
    <path d="M 13,11 L 26,18 L 13,25 Z" fill="white" opacity="0.92"/>
  </svg>
</template>
