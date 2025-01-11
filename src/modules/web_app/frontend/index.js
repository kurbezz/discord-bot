import { createApp, ref, onMounted } from 'vue';
import { createRouter, createWebHistory, RouterView } from 'vue-router';


const Authorize = {
    setup() {
        const loginLink = ref(null);

        onMounted(() => {
            fetch('/api/auth/get_authorization_url/twitch/')
                .then(response => response.json())
                .then(data => {
                    loginLink.value = data.authorization_url;
                })
        });

        return {
            loginLink
        }
    },
    template: `
        <div class="authorize__container">
            <a v-if="loginLink" :href="loginLink" class="authorize__twitch_btn">Login with Twitch</a>
            <div v-else>Loading...</div>
        </div>
    `
}


const Settings = {
    template: `
        <div>Settings</div>
    `
}


const Main = {
    components: {
        Authorize,
        Settings
    },
    setup() {
        const authorized = localStorage.getItem('token') !== null;

        return {
            authorized
        };
    },
    template: `
        <div>
            <Settings v-if="authorized" />
            <Authorize v-else />
        </div>
    `
};


const AuthCallbackTwitch = {
    setup() {
        onMounted(() => {
            fetch('/api/auth/callback/twitch/' + window.location.search)
                .then(response => response.json())
                .then(data => {
                    localStorage.setItem('token', data.token);

                    this.$router.push('/');
                });
        });
    },
    template: `
        <div>AuthCallbackTwitch</div>
    `
};


const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '', component: Main },
        { path: '/auth/callback/twitch/', component: AuthCallbackTwitch },
    ]
});


const App = {
    components: {
        RouterView,
    },
    template: `
        <RouterView />
    `,
};


createApp(App)
    .use(router)
    .mount('#app');
