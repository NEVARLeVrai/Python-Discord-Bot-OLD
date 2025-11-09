import discord
from discord.ext import commands

class Help_auto(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return  # Ignore les messages envoyés par le bot lui-même
        
        if isinstance(message.channel, discord.DMChannel):
            user = message.author
            content = message.content
            
            # Vérifie si le message est une commande ou une mention
            if content.startswith("=") or message.mention_everyone or self.client.user in message.mentions:
                return  # Ignore les messages de commande ou les mentions
            
            # Vérifier si c'est une réponse à un MP initié par la commande =mp
            mods_cog = self.client.get_cog('Mods')
            if mods_cog and hasattr(mods_cog, 'mp_conversations'):
                if user.id in mods_cog.mp_conversations:
                    # C'est une réponse à un MP initié par =mp
                    original_sender_id = mods_cog.mp_conversations[user.id]
                    original_sender = self.client.get_user(original_sender_id)
                    
                    if original_sender:
                        await original_sender.send(f"**Réponse de {user} ({user.mention}):**\n\n{content}")
                    return
            
            # Sinon, forwarder au target_user_id comme avant
            target_user = self.client.get_user(self.client.config['target_user_id'])
            
            if target_user:
                await target_user.send(f"Message privé de **{user}**: \n\n{content}")

async def setup(client):
    await client.add_cog(Help_auto(client))

