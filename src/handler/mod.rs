use serenity::prelude::*;
use serenity::all::{AutocompleteChoice, CreateAutocompleteResponse, CreateInteractionResponse, CreateInteractionResponseMessage, EditMessage, GuildId, Interaction};
use serenity::async_trait;
use serenity::model::channel::Message;

use chrono::offset::FixedOffset;

use crate::config;
use crate::notifiers::telegram::send_to_telegram;
use crate::utils::{add_game, delete_game, format_games_list, parse_games_list};

pub mod commands;


pub struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn interaction_create(&self, ctx: Context, interaction: Interaction) {
        if let Interaction::Command(command) = interaction {
            if command.channel_id != config::CONFIG.discord_game_list_channel_id {
                return;
            }

            match command.data.name.as_str() {
                "add" => {
                    let mut message = command.channel_id.message(&ctx.http, config::CONFIG.discord_game_list_message_id).await.unwrap();

                    let utc_offset = FixedOffset::east_opt(3 * 3600); // UTC+3 offset in seconds
                    let current_time = chrono::Local::now().with_timezone(&utc_offset.unwrap());

                    let mut categories = parse_games_list(&message.content).await;

                    categories = add_game(
                        categories,
                        command.data.options[0].value.as_str().unwrap(),
                        &format!(
                            "* {} ({}) | {}",
                            command.data.options[2].value.as_str().unwrap(),
                            command.data.options[1].value.as_str().unwrap(),
                            match command.data.options.get(3) {
                                Some(v) => v.value.as_str().unwrap().to_string(),
                                None => format!("{}", current_time.format("%d.%m.%Y")),
                            },
                        )
                    ).await;

                    let new_content = format_games_list(categories).await;

                    message.edit(&ctx.http, EditMessage::new().content(new_content)).await.unwrap();

                    let data = CreateInteractionResponseMessage::new().content("Игра добавлена!").ephemeral(true);
                    let builder = CreateInteractionResponse::Message(data);
                    if let Err(why) = command.create_response(&ctx.http, builder).await {
                        println!("Cannot respond to slash command: {why}");
                    }
                },
                "delete" => {
                    let mut message = command.channel_id.message(&ctx.http, config::CONFIG.discord_game_list_message_id).await.unwrap();

                    let mut categories = parse_games_list(&message.content).await;

                    categories = delete_game(
                        categories,
                        command.data.options[0].value.as_str().unwrap()
                    ).await;

                    let new_content = format_games_list(categories).await;

                    message.edit(&ctx.http, EditMessage::new().content(new_content)).await.unwrap();

                    let data = CreateInteractionResponseMessage::new().content("Игра удалена!").ephemeral(true);
                    let builder = CreateInteractionResponse::Message(data);
                    if let Err(why) = command.create_response(&ctx.http, builder).await {
                        println!("Cannot respond to slash command: {why}");
                    }
                },
                _ => (),
            };
        } else if let Interaction::Autocomplete(interaction) = interaction {
            if interaction.channel_id != config::CONFIG.discord_game_list_channel_id {
                return;
            }

            if interaction.data.name.as_str() == "delete" {
                let message = interaction.channel_id.message(&ctx.http, config::CONFIG.discord_game_list_message_id).await.unwrap();
                let categories = parse_games_list(&message.content).await;
                let games = categories.iter().flat_map(|category| category.games.iter()).collect::<Vec<&String>>();

                let query = interaction.data.options[0].value.as_str().unwrap();

                let autocompolete_response = CreateAutocompleteResponse::new().set_choices(
                    games
                        .iter()
                        .filter(|game| game.to_lowercase().contains(&query.to_lowercase()))
                        .take(25)
                        .map(|game| {
                            AutocompleteChoice::new(game.to_string(), game.to_string())
                        })
                        .collect()
                );

                let _ = interaction.create_response(&ctx.http, serenity::builder::CreateInteractionResponse::Autocomplete(autocompolete_response)).await.unwrap();
            };
        }
    }

    async fn message(&self, _ctx: Context, msg: Message) {
        if msg.guild_id != Some(config::CONFIG.discord_guild_id.into()) {
            return;
        }

        if msg.channel_id == config::CONFIG.discord_channel_id {
            send_to_telegram(&msg.content).await;
            return;
        }
    }

    async fn ready(&self, ctx: Context, _ready: serenity::model::gateway::Ready) {
        let guild_id = GuildId::new(config::CONFIG.discord_guild_id);

        let _ = guild_id
            .set_commands(
                &ctx.http,
                vec![
                    commands::add_game::register(),
                    commands::delete_game::register(),
                ]
            ).await.unwrap();
    }
}
