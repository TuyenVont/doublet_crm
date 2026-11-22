import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import translationPlugin from './translation'

import {
  FrappeUI,
  Button,
  Input,
  TextInput,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  Tooltip,
  FeatherIcon,
  setConfig,
  frappeRequest,
  initSocket,
} from 'frappe-ui'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(FrappeUI)
app.use(router)
app.use(translationPlugin)

if (window.site_name) {
  app.config.globalProperties.$socket = initSocket({ port: window.socketio_port })
}

const globalComponents = {
  Button,
  TextInput,
  Input,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  Tooltip,
  FeatherIcon,
}

for (const key in globalComponents) {
  app.component(key, globalComponents[key])
}

app.mount('#app')
