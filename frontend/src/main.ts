import { createApp } from 'vue'

import App from './App.vue'
import { router } from './router'
import './assets/main.css'

// Importing '@/api' (transitively via the router/auth store) configures the
// shared client with credentials + the CSRF interceptor before any request.
createApp(App).use(router).mount('#app')
