use serenity::builder::*;
use serenity::model::prelude::*;


pub fn register() -> CreateCommand {
    CreateCommand::new("delete")
        .description("Удалить игру из списока")
        .add_option(
            CreateCommandOption::new(
                CommandOptionType::String, "game", "Игра"
            )
            .required(true)
            .set_autocomplete(true)
        )
}
