<template>
  <Popover placement="bottom-end">
    <template #target="{ togglePopover }">
      <div class="flex items-center" @click="togglePopover">
        <component
          :is="assignees?.length == 1 ? 'Button' : 'div'"
          v-if="assignees?.length"
        >
          <MultipleAvatar :avatars="assignees" />
        </component>

        <Button
          v-else
          :label="__('Assign To')"
        />
      </div>
    </template>

    <template #body="{ isOpen }">
      <AssignToBody
        v-show="isOpen"
        v-model="assignees"
        :docname="docname"
        :doctype="doctype"
        :open="isOpen"
      />
    </template>
  </Popover>
</template>

<script setup>
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AssignToBody from '@/components/AssignToBody.vue'
import { Popover } from 'frappe-ui'

defineProps({
  doctype: {
    type: String,
    default: '',
  },

  docname: {
    type: String,
    default: '',
  },
})

/*
 * IMPORTANT:
 *
 * AssignTo chỉ quản lý collaborator / assignee.
 *
 * Nó KHÔNG được cập nhật:
 * - lead_owner
 * - deal_owner
 *
 * Primary Owner và AssignTo là hai khái niệm độc lập.
 */
const assignees = defineModel({
  type: Array,
  default: () => [],
})
</script>