import { ref } from 'vue'

const settings =
  typeof window !== 'undefined' ? window.doublet_crm_settings || {} : {}

export const whatsappEnabled = ref(Boolean(settings.whatsapp_enabled))
export const isWhatsappInstalled = ref(Boolean(settings.whatsapp_installed))
