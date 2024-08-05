use serenity::all::ActivityData;
use serenity::prelude::*;

pub mod config;
pub mod handler;
pub mod utils;
pub mod notifiers;


async fn start_discord_bot() {
    let intents = GatewayIntents::GUILD_MESSAGES
        | GatewayIntents::DIRECT_MESSAGES
        | GatewayIntents::MESSAGE_CONTENT;

    let mut client =
        Client::builder(&config::CONFIG.discord_bot_token, intents)
            .event_handler(handler::Handler)
            .status(serenity::all::OnlineStatus::Online)
            .activity(ActivityData::playing(&config::CONFIG.discord_bot_activity))
            .await
            .expect("Err creating client");

    if let Err(why) = client.start().await {
        panic!("Client error: {why:?}");
    }
}


#[tokio::main]
async fn main() {
    start_discord_bot().await;
}
