use serenity::prelude::*;
use std::env;
mod primes;

#[tokio::main]
async fn main() {
    let token = env::var("MEME_BOT_TOKEN").expect("Expected MEME_BOT_TOKEN in env");
    let intents = GatewayIntents::GUILD_MESSAGES
        | GatewayIntents::DIRECT_MESSAGES
        | GatewayIntents::MESSAGE_CONTENT;

    let mut client = Client::builder(&token, intents)
        .event_handler(primes::PrimesHandler)
        .await
        .expect("Err creating client");

    println!("starting discord client");

    if let Err(why) = client.start().await {
        println!("Client error: {why:?}");
    }
}
