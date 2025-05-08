use std::env;

use serenity::async_trait;
use serenity::model::channel::Message;
use serenity::prelude::*;

use primes::is_prime;

struct PrimesHandler;

#[async_trait]
impl EventHandler for PrimesHandler {
    async fn message(&self, ctx: Context, msg: Message) {
        if msg.author.bot {
            return;
        }

        let message_has_prime = msg.content_safe(&ctx.cache).split_ascii_whitespace()
            .filter_map(|word| Some(word.parse::<u64>().ok()).unwrap())
            .filter(|&num| num > 10)
            .any(|num| is_prime(num));

        if !message_has_prime {
            return
        }

        let result = msg.reply(&ctx.http, "nice prime").await;
        if let Err(why) = result {
            println!("error sending message {why:?}");
        }
    }
}

#[tokio::main]
async fn main() {
    let token = env::var("MEME_BOT_TOKEN").expect("Expected MEME_BOT_TOKEN in env");
    let intents = GatewayIntents::GUILD_MESSAGES
        | GatewayIntents::DIRECT_MESSAGES
        | GatewayIntents::MESSAGE_CONTENT;

    let mut client = Client::builder(&token, intents)
        .event_handler(PrimesHandler)
        .await
        .expect("Err creating client");

    println!("starting discord client");
    
    if let Err(why) = client.start().await {
        println!("Client error: {why:?}");
    }
}
