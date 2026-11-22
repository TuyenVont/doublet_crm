<template>
  <div>
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <Avatar
          :image="call._caller.image"
          :label="call._caller.label"
          size="md"
        />
        <span class="font-medium text-ink-gray-8 ml-1">
          {{ call._caller.label }}
        </span>
        <span>{{
          call.type == 'Incoming'
            ? __('has reached out')
            : __('has made a call')
        }}</span>
      </div>
      <div class="ml-auto whitespace-nowrap">
        <TimelineTimestamp :date="call.creation" />
      </div>
    </div>
    <RouterLink
      :to="{ name: 'CallDetail', params: { callId: call.name }, query: { from: 'customer' } }"
      class="flex flex-col gap-2 rounded-md border border-outline-elevation-2 bg-surface-elevation-1 px-3 py-2.5 text-ink-gray-9"
    >
      <div class="flex items-center justify-between">
        <div class="inline-flex gap-2 items-center text-base-medium">
          <div>
            {{
              call.type == 'Incoming' ? __('Inbound Call') : __('Outbound Call')
            }}
          </div>
        </div>
        <div>
          <MultipleAvatar
            :avatars="[
              {
                image: call._caller.image,
                label: call._caller.label,
                name: call._caller.label,
              },
              {
                image: call._receiver.image,
                label: call._receiver.label,
                name: call._receiver.label,
              },
            ]"
            size="sm"
          />
        </div>
      </div>
      <div class="flex items-center flex-wrap gap-2">
        <Badge :label="formatDate(call.creation, 'MMM D, dddd')">
          <template #prefix>
            <CalendarIcon class="size-3" />
          </template>
        </Badge>
        <Badge v-if="call.status == 'Completed'" :label="call._duration">
          <template #prefix>
            <DurationIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          :label="__(call.status)"
          :theme="['Missed', 'No Answer'].includes(call.status) ? 'red' : 'gray'"
        />
      </div>
    </RouterLink>
  </div>
</template>
<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { formatDate } from '@/utils'
import { Avatar, Badge } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
})

const call = computed(() => props.activity)
</script>
