use num_prime::nt_funcs::is_prime;
use serenity::async_trait;
use serenity::model::channel::Message;
use serenity::prelude::*;

pub(crate) struct PrimesHandler;

#[async_trait]
impl EventHandler for PrimesHandler {
    async fn message(&self, ctx: Context, msg: Message) {
        if msg.author.bot {
            return;
        }

        let message_has_prime = msg
            .content_safe(&ctx.cache)
            .split_ascii_whitespace()
            .filter_map(|word| word.parse::<u64>().ok())
            .filter(|&num| num > 10)
            .any(|num| is_prime(&num, Option::None).probably());

        if !message_has_prime {
            return;
        }

        let result = msg.reply(&ctx.http, "nice prime").await;
        if let Err(why) = result {
            println!("error sending message {why:?}");
        }
    }
}
