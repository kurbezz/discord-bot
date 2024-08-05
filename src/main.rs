use futures::StreamExt;
use serenity::all::ActivityData;
use serenity::prelude::*;

use twitch_handler::{auth::{self}, helix};

use tokio::join;
use rustls;

pub mod config;
pub mod discord_handler;
pub mod twitch_handler;
pub mod utils;
pub mod notifiers;


async fn start_discord_bot() {
    println!("Starting Discord bot...");

    let intents = GatewayIntents::GUILD_MESSAGES
        | GatewayIntents::DIRECT_MESSAGES
        | GatewayIntents::MESSAGE_CONTENT;

    let mut client =
        Client::builder(&config::CONFIG.discord_bot_token, intents)
            .event_handler(discord_handler::Handler)
            .status(serenity::all::OnlineStatus::Online)
            .activity(ActivityData::playing(&config::CONFIG.discord_bot_activity))
            .await
            .expect("Err creating client");

    if let Err(why) = client.start().await {
        panic!("Client error: {why:?}");
    }
}

async fn start_twitch_bot() {
    println!("Starting Twitch bot...");

    let token_storage = auth::VoidStorage {};

    let mut client = helix::Client::from_get_app_token(
        config::CONFIG.twitch_client_id.clone(),
        config::CONFIG.twitch_client_secret.clone(),
        token_storage,
    ).await.unwrap();

    let mut t = client.connect_eventsub(vec![
        ("stream.online".to_string(), "1".to_string()),
        ("stream.offline".to_string(), "1".to_string()),
        ("channel.update".to_string(), "2".to_string())
    ], config::CONFIG.twitch_channel_id.clone()).await.unwrap();

    while let Some(event) = t.next().await {
        println!("{:?}", event);
    }
}


#[tokio::main]
async fn main() {
    rustls::crypto::ring::default_provider().install_default().expect("Failed to install rustls crypto provider");

    join!(start_discord_bot(), start_twitch_bot());
}
