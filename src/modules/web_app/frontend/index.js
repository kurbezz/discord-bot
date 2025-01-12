import { createApp, ref, onMounted } from 'vue';
import { createRouter, createWebHistory, RouterView, useRouter } from 'vue-router';

import { jwtDecode } from "jwt-decode";


class TokenManager {
    static TOKEN_KEY = "token";

    static getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    static getAndValidate() {
        const token = this.getToken();

        if (token === null) {
            return null;
        }

        let decoded;

        try {
            decoded = jwtDecode(token);
        } catch (e) {
            return null;
        }

        if (decoded.exp < Date.now() / 1000) {
            this.removeToken();
            return null;
        }

        return token;
    }

    static setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    }

    static removeToken() {
        localStorage.removeItem(this.TOKEN_KEY);
    }
}


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
        <div class="flex__container__center">
            <a v-if="loginLink" :href="loginLink" class="authorize__twitch_btn">Login with Twitch</a>
            <div v-else>Loading...</div>
        </div>
    `
}


const Settings = {
    setup() {
        const router = useRouter();

        const logout = () => {
            TokenManager.removeToken();
            router.push('/');
        }

        return {
            logout,
        };
    },
    template: `
        <div class="settings__container">
            <div class="settings__header">
                <button @click="logout">Logout</button>
            </div>
        </div>
    `
}


const Main = {
    components: {
        Authorize,
        Settings
    },
    setup() {
        const authorized = TokenManager.getAndValidate() !== null;

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
        const router = useRouter();

        onMounted(() => {
            fetch('/api/auth/callback/twitch/' + window.location.search)
                .then(response => response.json())
                .then(data => {
                    localStorage.setItem(TOKEN_KEY, data.token);

                    router.push('/');
                });
        });
    },
    template: `
        <div class="flex__container__center">
            <div>Loading...</div>
        </div>
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
