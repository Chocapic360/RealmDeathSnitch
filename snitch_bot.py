import discord
import asyncio
import image_downloader as imd
import guild_graveyard as gg
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import Realm_image_parser as RIP
from discord.ext import commands
import player_characters

load_dotenv(Path('keys.env'))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
channel_id = int(os.getenv("CHANNEL_ID"))
channel = None
guild = os.getenv("GUILD_NAME")

imd.Download_Images()
with open('last death.json', 'w') as f:
    last_death = gg.guild_graveyard(guild, 0)
    i = 1
    while last_death['player-name'] == "Private":
        print("private death")
        last_death = gg.guild_graveyard(guild, i)
        i += 1
    json.dump(last_death, f)
f.close()

async def run_guild_graveyard():
    while True:
        latest_death = gg.guild_graveyard(guild, 0)
        if latest_death != json.load(open('last death.json')) and latest_death['player-name'] != "Private":
            print("someone died")
            # Refresh sprite sources when a new death is detected so item renders stay current.
            imd.Download_Images()
            with open('last death.json', 'w') as f:
                json.dump(latest_death, f)
            f.close()
            RIP.death_image_combiner(latest_death)
            death_image = discord.File("./images/output.png")
            channel = client.get_channel(int(channel_id))
            await channel.send(f"**{latest_death['player-name']}** died on **{latest_death['time'].split('T')[0]} at {latest_death['time'].split('T')[1].split('Z')[0]}**\n"
                               f"**Killed by:** {latest_death['killed_by']}\n**Base Fame:** {latest_death['base_fame']} **Total Fame:** {latest_death['total_fame']}\n"
                               f"**Stats:** {latest_death['stats']}", file=death_image)
            RIP.delete_all_files_in_folder("./itempics")
            RIP.delete_all_files_in_folder("./skinpics")

        await asyncio.sleep(60)  # Wait for 60 seconds

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    bot.loop.create_task(run_guild_graveyard())

@bot.command(name = "characters")
async def characters(ctx, player_name):
    print("characters command")
    player_character_list = player_characters.get_player_characters(player_name)
    index = 0
    if len(player_character_list) < 6:
        index = len(player_character_list)
    else:
        index = 6
    for i in range(index):
        RIP.skin_image_parser(player_character_list[i]['skindata']['x'], player_character_list[i]['skindata']['y'], f"{player_character_list[i]['class']}_{i}")
        for item in player_character_list[i]['equipment']:
            RIP.item_image_parser(item['x'], item['y'], item['name'])
        RIP.character_image_combiner(player_character_list[i], i)
        await ctx.send(file=discord.File("./images/alive_output.png"))
    RIP.delete_all_files_in_folder("./itempics")
    RIP.delete_all_files_in_folder("./skinpics")


discord_key = os.getenv("DISCORD_KEY")
bot.run(discord_key)
