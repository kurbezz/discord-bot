use reqwest::Url;
use serenity::json::json;

use crate::config;


pub async fn send_to_discord(msg: &str) {
    let base_url = format!("https://discord.com/api/v10/channels/{}/messages", config::CONFIG.discord_channel_id);

    let url = Url::parse(&base_url.as_ref()).unwrap();

    reqwest::Client::new().post(url)
        .header("Authorization", format!("Bot {}", config::CONFIG.discord_bot_token))
        .json(&json!({
            "content": msg
        })).send().await.expect("Error sending message to Discord");
}
