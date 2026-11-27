<template>
  <Dialog
    v-model:open="open"
    :title="__('Discount Approval Settings')"
    size="lg"
    :dismissible="!saving"
    :showCloseButton="!saving"
  >
    <form class="space-y-4" @submit.prevent="save">
      <ErrorMessage v-if="error" :message="error" />
      <p class="text-xs text-ink-gray-6">
        {{ __('Configure when Draft Quotations require manager approval before sending. Saved Quotations keep their existing state.') }}
      </p>
      <label class="flex items-center gap-2 text-sm text-ink-gray-8">
        <input v-model="form.enabled" type="checkbox" class="h-4 w-4" :disabled="saving || loading" />
        <span>{{ __('Require approval for discounts exceeding threshold') }}</span>
      </label>
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="flex flex-col gap-1 text-sm">
          {{ __('Threshold (%)') }}
          <TextInput v-model="form.thresholdPercent" type="number" min="0" max="100" step="any" :disabled="saving || loading || !form.enabled" />
        </label>
        <label class="flex flex-col gap-1 text-sm">
          {{ __('Threshold Amount (USD)') }}
          <TextInput v-model="form.thresholdAmount" type="number" min="0" step="0.01" :disabled="saving || loading || !form.enabled" />
        </label>
      </div>
      <div class="flex justify-end gap-2 border-t border-outline-gray-2 pt-3">
        <Button type="button" :label="__('Cancel')" :disabled="saving" @click="open = false" />
        <Button type="submit" variant="solid" :label="__('Save')" :loading="saving" :disabled="loading" />
      </div>
    </form>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, TextInput, call } from 'frappe-ui'
import { message } from '@/utils/quotation'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const open = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const form = reactive({
  enabled: false,
  thresholdPercent: 0,
  thresholdAmount: 0,
})

watch(open, async (visible) => {
  if (!visible) return
  loading.value = true
  error.value = ''
  try {
    const res = await call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.get_discount_approval_settings')
    form.enabled = Boolean(res?.enable_discount_approval)
    form.thresholdPercent = res?.discount_approval_threshold_percent ?? 0
    form.thresholdAmount = res?.discount_approval_threshold_amount ?? 0
  } catch (e) {
    error.value = message(e)
  } finally {
    loading.value = false
  }
})

async function save() {
  if (saving.value) return
  saving.value = true
  error.value = ''
  try {
    await call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.update_discount_approval_settings', {
      enable_discount_approval: form.enabled ? 1 : 0,
      discount_approval_threshold_percent: Number(form.thresholdPercent || 0),
      discount_approval_threshold_amount: Number(form.thresholdAmount || 0),
    })
    emit('saved')
    open.value = false
  } catch (e) {
    error.value = message(e)
  } finally {
    saving.value = false
  }
}
</script>
