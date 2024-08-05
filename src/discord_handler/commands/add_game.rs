use serenity::builder::*;
use serenity::model::prelude::*;


pub fn register() -> CreateCommand {
    CreateCommand::new("add")
        .description("Добавить игру в список")
        .add_option(
            CreateCommandOption::new(
                CommandOptionType::String, "category", "Раздел"
            )
            .required(true)
            .add_string_choice("Заказ за баллы", "points")
            .add_string_choice("Проплачены", "paids")
            .add_string_choice("Подарки", "gifts")
        )
        .add_option(
            CreateCommandOption::new(
                CommandOptionType::String, "customer", "Кто заказал"
            )
            .required(true)
        )
        .add_option(
            CreateCommandOption::new(
                CommandOptionType::String, "game", "Игра"
            )
            .required(true)
        )
        .add_option(
            CreateCommandOption::new(
                CommandOptionType::String, "date", "Дата заказа"
            )
            .required(false)
        )
}
