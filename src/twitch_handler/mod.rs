pub mod eventsub;
pub mod helix;
pub mod auth;

use chrono::{DateTime, Utc};
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


#[derive(Clone)]
pub struct State {
    pub title: String,
    pub game: String,
    pub updated_at: DateTime<Utc>
}


pub struct TwitchBot {}


pub async fn notify_game_change(_title: String, old_game: String, new_game: String) {
    println!("Game changed: {} -> {}", old_game, new_game);
}

pub async fn notify_stream_online(title: String) {
    println!("Stream online: {}", title);
}


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

        let mut current_state: Option<State> = {
            let stream = client.get_stream(config::CONFIG.twitch_channel_id.clone()).await;

            match stream {
                Ok(stream) => {
                    Some(State {
                        title: stream.title,
                        game: stream.game_name,
                        updated_at: chrono::offset::Utc::now()
                    })
                },
                Err(_) => {
                    None
                }
            }
        };

        let mut eventsub_client = client.connect_eventsub(
            vec![
                ("stream.online".to_string(), "1".to_string()),
                ("stream.offline".to_string(), "1".to_string()),
                ("channel.update".to_string(), "2".to_string())
            ],
            config::CONFIG.twitch_channel_id.clone()
        ).await.unwrap();

        println!("Connected to Twitch EventSub...");
        client.validate_token().await.unwrap();

        loop {
            println!("Polling Twitch EventSub...");
            if let Some(event) = eventsub_client.next().await {
                match event {
                    eventsub::NotificationType::CustomRewardRedemptionAdd(_) => todo!(),
                    eventsub::NotificationType::StreamOffline(_) => {},
                    eventsub::NotificationType::ChannelUpdate(data) => {
                        if let Some(state) = current_state {
                            if state.game.to_lowercase().trim() != data.title.to_lowercase().trim() {
                                notify_game_change(
                                    data.title.clone(),
                                    state.game.clone(),
                                    data.category_name.clone()
                                ).await;
                            }
                        }

                        current_state = Some(State {
                            title: data.title,
                            game: data.category_name.clone(),
                            updated_at: chrono::offset::Utc::now()
                        });
                    },
                    eventsub::NotificationType::StreamOnline(_) => {
                        if (chrono::offset::Utc::now() - current_state.as_ref().unwrap().updated_at).num_seconds() > 15 * 60 {
                            notify_stream_online(current_state.as_ref().unwrap().title.clone()).await;
                        }

                        current_state.as_mut().unwrap().updated_at = chrono::offset::Utc::now();
                    },
                }
            }

            client.validate_token().await.unwrap();
        }
    }
}
