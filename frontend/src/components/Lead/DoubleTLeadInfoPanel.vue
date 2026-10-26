<template>
  <div class="flex flex-col overflow-y-auto">

    <!-- DETAILS -->
    <details open class="border-b">
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4
               text-sm font-semibold text-ink-gray-9"
      >
        {{ __('Details') }}
      </summary>

      <div class="space-y-4 px-5 pb-5">
        <InfoRow
          :label="__('Company')"
          :value="lead.company_name"
        />

        <InfoRow
          :label="__('Source')"
          :value="lead.source"
        />

        <InfoRow
          :label="__('Status')"
          :value="lead.status"
        />

        <InfoRow
          :label="__('Lead Owner')"
          :value="lead.lead_owner"
        />
      </div>
    </details>

    <!-- PERSON -->
    <details open class="border-b">
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4
               text-sm font-semibold text-ink-gray-9"
      >
        {{ __('Person') }}
      </summary>

      <div class="space-y-4 px-5 pb-5">
        <InfoRow
          :label="__('First Name')"
          :value="lead.first_name"
        />

        <InfoRow
          :label="__('Last Name')"
          :value="lead.last_name"
        />

        <InfoRow
          :label="__('Email')"
          :value="lead.email"
        />

        <InfoRow
          :label="__('Phone')"
          :value="lead.phone"
        />
      </div>
    </details>

    <!-- CONVERSION -->
    <details
      v-if="isConverted"
      open
      class="border-b"
    >
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4
               text-sm font-semibold text-ink-gray-9"
      >
        {{ __('Conversion') }}
      </summary>

      <div class="space-y-4 px-5 pb-5">
        <InfoRow
          :label="__('Contact')"
          :value="lead.converted_contact"
        />

        <InfoRow
          :label="__('Company')"
          :value="lead.converted_company"
        />

        <InfoRow
          :label="__('Deal')"
          :value="lead.converted_deal"
        />

        <InfoRow
          :label="__('Converted On')"
          :value="lead.converted_on"
        />
      </div>
    </details>

    <!-- NOTES -->
    <details
      v-if="lead.notes"
      class="border-b"
    >
      <summary
        class="flex cursor-pointer items-center justify-between px-5 py-4
               text-sm font-semibold text-ink-gray-9"
      >
        {{ __('Notes') }}
      </summary>

      <div
        class="whitespace-pre-wrap px-5 pb-5 text-sm text-ink-gray-7"
      >
        {{ lead.notes }}
      </div>
    </details>

  </div>
</template>

<script setup>
import {
  computed,
  defineComponent,
  h,
} from 'vue'

const props = defineProps({
  lead: {
    type: Object,
    required: true,
  },
})

const isConverted = computed(() => {
  return (
    props.lead?.status === 'CONVERTED' ||
    Boolean(props.lead?.converted_contact)
  )
})

const InfoRow = defineComponent({
  props: {
    label: String,
    value: [String, Number],
  },

  setup(props) {
    return () =>
      h(
        'div',
        {
          class:
            'grid grid-cols-[110px_minmax(0,1fr)] gap-3 text-sm',
        },
        [
          h(
            'div',
            {
              class: 'text-ink-gray-5',
            },
            props.label
          ),

          h(
            'div',
            {
              class:
                'break-words text-ink-gray-9',
            },
            props.value === null ||
              props.value === undefined ||
              props.value === ''
              ? '-'
              : String(props.value)
          ),
        ]
      )
  },
})
</script>

