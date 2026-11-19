import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const whatsappSource = readFileSync(
  new URL('../src/composables/whatsapp.js', import.meta.url),
  'utf8',
)
const viewsSource = readFileSync(
  new URL('../src/stores/views.js', import.meta.url),
  'utf8',
)

test('WhatsApp state comes from DoubleT boot without legacy CRM requests', () => {
  assert.doesNotMatch(whatsappSource, /crm\.api\.whatsapp/)
  assert.match(whatsappSource, /window\.doublet_crm_settings/)
  assert.match(whatsappSource, /settings\.whatsapp_enabled/)
  assert.match(whatsappSource, /settings\.whatsapp_installed/)
})

test('views use permission-aware Framework listing scoped to the session user', () => {
  assert.doesNotMatch(viewsSource, /crm\.api\.views\.get_views/)
  assert.match(viewsSource, /url: 'frappe\.client\.get_list'/)
  assert.match(viewsSource, /doctype: 'CRM View Settings'/)
  assert.match(viewsSource, /filters: \[\['user', 'in', \['', session\.user\]\]\]/)
})
