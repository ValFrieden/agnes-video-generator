<script setup lang="ts">
import { t } from '@/i18n'
import { FREE_TOKENS_GUIDE_URL, GITHUB_REPO } from '@/utils/feedback'
</script>

<template>
  <!-- 第三方供应商使用说明：免费模型支持范围 / AMD Radeon Cloud 推荐 / 图像视频暂不支持 -->
  <div class="rounded-lg bg-paper-3/60 p-4 text-xs leading-relaxed mb-4">
    <p class="font-medium text-ink-2 mb-2">{{ t('providerIntroTitle') }}</p>
    <!-- 官网教程导流：免费 Token / 供应商配置图文教程 -->
    <p class="mb-2">
      <a
        :href="FREE_TOKENS_GUIDE_URL"
        target="_blank"
        rel="noopener"
        class="text-accent hover:text-ink transition-colors underline decoration-dotted underline-offset-2"
      >{{ t('providerIntroGuide') }}</a>
    </p>
    <ul class="list-disc pl-4 space-y-1.5 text-muted">
      <li>{{ t('providerIntroFree') }}</li>
      <li>
        {{ t('providerIntroText') }}
        <ul class="list-disc pl-4 mt-1.5 space-y-1">
          <li>
            <a
              href="https://developer.amd.com.cn/radeon/modelapis"
              target="_blank"
              rel="noopener"
              class="underline decoration-dotted underline-offset-2 hover:text-ink transition-colors"
            >{{ t('providerIntroAmdEntry') }}</a>
          </li>
          <li>
            {{ t('providerIntroAmdEndpoint') }}
            <code class="font-mono text-ink-2 select-all">https://developer.amd.com.cn/radeon/api/v1</code>
          </li>
          <li>{{ t('providerIntroAmdModels') }}</li>
          <li>{{ t('providerIntroAmdNote') }}</li>
        </ul>
      </li>
      <li>
        {{ t('providerIntroMedia') }}{{ t('providerIntroMediaRecommend') }}
        <a
          :href="GITHUB_REPO + '/issues/new'"
          target="_blank"
          rel="noopener"
          class="text-accent hover:text-ink transition-colors"
        >GitHub Issue</a>
        <span class="mx-1">/</span>
        <a
          :href="GITHUB_REPO + '/discussions'"
          target="_blank"
          rel="noopener"
          class="text-accent hover:text-ink transition-colors"
        >GitHub Discussion</a>
      </li>
    </ul>
  </div>
</template>