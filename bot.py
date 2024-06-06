import discord
from discord.ext import commands
import pandas as pd
import random
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CONFIGURED_ROLES = os.getenv('CONFIGURED_ROLES').split(',')
AUTHORIZED_ROLE_IDS = list(map(int, os.getenv('AUTHORIZED_ROLE_IDS').split(',')))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix='?', intents=intents)

codes = []  # List to store the codes from the CSV file
claimed_codes = {}  # Dictionary to track claimed codes

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='premiumsignup')
@commands.has_any_role(*AUTHORIZED_ROLE_IDS)
async def premium_signup(ctx, channel: discord.TextChannel):
    embed = discord.Embed(title="Server Subscriber Code Claim", description="Click the button to claim your code.", color=0x00ff00)
    button = discord.ui.Button(label="Claim Code", style=discord.ButtonStyle.primary)

    async def button_callback(interaction):
        user = interaction.user
        if user.id in claimed_codes:
            await interaction.response.send_message("You have already claimed a code.", ephemeral=True)
        elif not codes:
            await interaction.response.send_message("No more codes available.", ephemeral=True)
        else:
            code = codes.pop()
            claimed_codes[user.id] = code
            await interaction.response.send_message(f"Your code: {code}", ephemeral=True)

    button.callback = button_callback
    view = discord.ui.View()
    view.add_item(button)
    await channel.send(embed=embed, view=view)

@bot.command(name='uploadcsv')
@commands.has_any_role(*AUTHORIZED_ROLE_IDS)
async def upload_csv(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if attachment.filename.endswith('.csv'):
                await attachment.save(attachment.filename)

                # Read the CSV file and extract codes
                df = pd.read_csv(attachment.filename)
                global codes
                codes = df['code'].tolist()
                random.shuffle(codes)
                await ctx.send("Codes have been imported successfully.")

@bot.command(name='ranks')
@commands.has_any_role(*AUTHORIZED_ROLE_IDS)
async def ranks(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if attachment.filename.endswith('.csv'):
                await attachment.save(attachment.filename)

                # Read the CSV file and create a new column
                df = pd.read_csv(attachment.filename)
                df['Role'] = 'not found'

                # Check each user's roles
                for index, row in df.iterrows():
                    member = discord.utils.get(bot.get_all_members(), name=row['Discord Username'])
                    if member:
                        for role in member.roles:
                            if role.name in CONFIGURED_ROLES:
                                df.at[index, 'Role'] = role.name
                                break

                # Save the dataframe as a new CSV file
                new_filename = 'new_' + attachment.filename
                df.to_csv(new_filename, index=False)

                # Send the new CSV file
                await ctx.send(file=discord.File(new_filename))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send('You do not have the required role to use this command.')

bot.run(DISCORD_TOKEN)