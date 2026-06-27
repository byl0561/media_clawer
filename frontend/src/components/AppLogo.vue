<template>
  <!--
    MediaGap 品牌图标：两张媒体卡片 + 中间的缺口
    左边实心（已有）、右边虚线轮廓（缺失），三点代表 gap
    ViewBox 32×32，白色描边，容器提供紫色背景
  -->
  <svg
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style="display:block;width:100%;height:100%"
    aria-hidden="true"
  >
    <!-- 已有的媒体卡（实心）-->
    <rect x="2" y="6" width="11" height="20" rx="2.5" fill="white" opacity="0.92"/>
    <!-- 卡内内容暗纹（用 accent 色，让卡片有层次）-->
    <line x1="4.5" y1="12" x2="11" y2="12" stroke="#8B7CF6" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="4.5" y1="15.5" x2="9.5" y2="15.5" stroke="#8B7CF6" stroke-width="1.5" stroke-linecap="round"/>
    <!-- 缺口三点 -->
    <circle cx="15"  cy="16" r="1.1" fill="white" opacity="0.45"/>
    <circle cx="18"  cy="16" r="1.1" fill="white" opacity="0.45"/>
    <circle cx="21"  cy="16" r="1.1" fill="white" opacity="0.45"/>
    <!-- 缺失的媒体卡（虚线轮廓）-->
    <rect x="24" y="6" width="7" height="20" rx="2" stroke="white" stroke-width="1.8"
      stroke-dasharray="3 2.5" fill="none" opacity="0.55"/>
  </svg>
</template>
