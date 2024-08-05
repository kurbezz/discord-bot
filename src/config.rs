use once_cell::sync::Lazy;


fn get_env(env: &'static str) -> String {
    std::env::var(env).unwrap_or_else(|_| panic!("Cannot get the {} env variable", env))
}


pub struct Config {
    pub discord_bot_token: String,

    pub discord_guild_id: u64,
    pub discord_channel_id: u64,

    pub discord_bot_activity: String,

    pub discord_game_list_channel_id: u64,
    pub discord_game_list_message_id: u64,

    pub telegram_bot_token: String,
    pub telegram_channel_id: i128,

    pub twitch_client_id: String,
    pub twitch_client_secret: String,
    pub twitch_channel_id: String,
}


impl Config {
    pub fn load() -> Config {
        Config {
            discord_bot_token: get_env("DISCORD_BOT_TOKEN"),
            discord_guild_id: get_env("DISCORD_GUILD_ID").parse().unwrap(),
            discord_channel_id: get_env("DISCORD_CHANNEL_ID").parse().unwrap(),
            discord_bot_activity: get_env("DISCORD_BOT_ACTIVITY"),
            discord_game_list_channel_id: get_env("DISCORD_GAME_LIST_CHANNEL_ID").parse().unwrap(),
            discord_game_list_message_id: get_env("DISCORD_GAME_LIST_MESSAGE_ID").parse().unwrap(),
            telegram_bot_token: get_env("TELEGRAM_BOT_TOKEN"),
            telegram_channel_id: get_env("TELEGRAM_CHANNEL_ID").parse().unwrap(),
            twitch_client_id: get_env("TWITCH_CLIENT_ID"),
            twitch_client_secret: get_env("TWITCH_CLIENT_SECRET"),
            twitch_channel_id: get_env("TWITCH_CHANNEL_ID"),
        }
    }
}


pub static CONFIG: Lazy<Config> = Lazy::new(Config::load);
