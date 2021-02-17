import json
import aiohttp
from discord.ext import commands


class Suggest(commands.Cog):

    def __init__(self, github_token: str, project_column_id: str):
        self.github_token = github_token
        self.project_column_id = project_column_id

    @commands.command(aliases=["segges"])
    async def suggest(self, context: commands.Context, *, text: str):
        '''Suggest a new feature. Existing suggestions can be seen
        at https://github.com/ropc/meme-bot/projects/1#column-12267170
        '''
        headers = {
            'Authorization': f'Bearer {self.github_token}'
        }
        payload = {
            "query": f'''mutation {{
                addProjectCard(input: {{projectColumnId: "{self.project_column_id}", note:"{text}\n\n_Suggested by {context.author.name}_"}}) {{
                    cardEdge {{
                        node {{
                            url
                        }}
                    }}
                }}
            }}'''
        }
        async with context.typing():
            async with aiohttp.ClientSession() as s:
                async with s.post('https://api.github.com/graphql', data=json.dumps(payload), headers=headers) as r:
                    body = await r.json()
                    suggestion_url = body['data']['addProjectCard']['cardEdge']['node']['url']
                    await context.send(f'Got it! {suggestion_url}')
