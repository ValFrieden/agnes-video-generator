<script setup lang="ts">
import { ref, reactive } from 'vue'
import { t } from '@/i18n'
import { getCollapsePrefs, setCollapsePref } from '@/store'
import { useModalA11y } from '@/composables/useModalA11y'
import ProviderManager from '@/components/ProviderManager.vue'
import ModelSelector from '@/components/ModelSelector.vue'
import WorkspaceManager from '@/components/WorkspaceManager.vue'
import PrivacySettings from '@/components/PrivacySettings.vue'

const collapsed = reactive(getCollapsePrefs())
function toggleConfigPanel(section: string) {
  collapsed[section] = !collapsed[section]
  setCollapsePref(section, collapsed[section])
}

const providerManagerRef = ref<any>(null)
</script>

<template>
  <ProviderManager ref="providerManagerRef" :collapsed="collapsed.apikey" @toggle="toggleConfigPanel('apikey')" />

  <ModelSelector @add-provider="providerManagerRef?.openAddProvider()" />

  <WorkspaceManager />

  <PrivacySettings :collapsed="collapsed.privacy" @toggle="toggleConfigPanel('privacy')" />

</template>