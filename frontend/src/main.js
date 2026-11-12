import { mount } from 'svelte';
import App from './pages/DashboardPage.svelte';
import { configureApi } from './lib/api.js';
import '../painel.css';

const target = document.getElementById('dashboard');
const config = JSON.parse(document.getElementById('dashboard-config').textContent);
configureApi(config.apiPort);
target.replaceChildren();
mount(App, { target, props: config });
