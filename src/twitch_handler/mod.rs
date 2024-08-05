pub mod eventsub;
pub mod helix;
pub mod auth;

use futures::StreamExt;
use async_trait::async_trait;
use auth::Token;

use crate::config;


pub struct TokenStorage {
    pub filepath: String,
}

#[async_trait]
impl auth::TokenStorage for TokenStorage {
    async fn save(&mut self, token: &Token) -> anyhow::Result<()> {
        let token_json = serde_json::to_string(&token).unwrap();

        std::fs::write(&self.filepath, token_json).unwrap();

        Ok(())
    }
}

impl TokenStorage {
    pub async fn load(&self) -> anyhow::Result<Token> {
        let token_json = std::fs::read_to_string(&self.filepath).unwrap();

        let token: Token = serde_json::from_str(&token_json).unwrap();

        Ok(token)
    }
}


pub struct TwitchBot {}


impl TwitchBot {
    pub async fn start() {
        println!("Starting Twitch bot...");

        let token_storage = TokenStorage {
            filepath: "/secrets/twitch_token.json".to_string()
        };
        let token = token_storage.load().await.unwrap();

        let mut client = helix::Client::from_token(
            config::CONFIG.twitch_client_id.clone(),
            config::CONFIG.twitch_client_secret.clone(),
            token_storage,
            token
        ).await.unwrap();

        let mut eventsub_client = client.connect_eventsub(
            vec![
                ("stream.online".to_string(), "1".to_string()),
                ("stream.offline".to_string(), "1".to_string()),
                ("channel.update".to_string(), "2".to_string())
            ],
            config::CONFIG.twitch_channel_id.clone()
        ).await.unwrap();

        println!("Connected to Twitch EventSub...");
        client.refresh_token().await.unwrap();

        loop {
            if let Some(event) = eventsub_client.next().await {
                println!("{:?}", event);
            }

            client.validate_token().await.unwrap();
        }
    }
}
