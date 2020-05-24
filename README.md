# meme-bot
A discord bot for generating memes.

## Features
- [Declarative definitions for memes](meme_generator/allmemes.py)
- Extensible through [composable plugins](meme_generator/plugins)
- Run with docker 🐳

## Example

![this is a great use of my time](docs/example.png)


## Developing

### Run meme generator locally

When adding a new meme to [allmemes.py](meme_generator/allmemes.py), you can test it out
from the terminal by running:

```
poetry run meme {meme alias} {input text}
```

this will open your generated meme in a new window.
