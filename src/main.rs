use serenity::all::ActivityData;
use serenity::prelude::*;

use twitch_handler::TwitchBot;

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
    TwitchBot::start().await;
}


#[tokio::main]
async fn main() {
    rustls::crypto::ring::default_provider().install_default().expect("Failed to install rustls crypto provider");

    join!(start_discord_bot(), start_twitch_bot());
}
