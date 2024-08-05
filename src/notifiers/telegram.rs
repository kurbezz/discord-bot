use reqwest::Url;

use crate::config;


pub async fn send_to_telegram(msg: &str) {
    let base_url = format!("https://api.telegram.org/bot{}/sendMessage", config::CONFIG.telegram_bot_token);

    let url = Url::parse_with_params(
        base_url.as_ref(),
        &[
            ("chat_id", &config::CONFIG.telegram_channel_id.to_string().as_ref()),
            ("text", &msg)
        ]
    ).unwrap();

    reqwest::Client::new().post(url)
        .send().await.expect("Error sending message to Telegram");
}
