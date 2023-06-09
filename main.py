"""
MinigameBot: Discord bot with different mini-games.

Selena Zhou, May 2023
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from random import randint

"""CONFIGURATIONS"""

# .env
load_dotenv()

# Discord
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True  # important!!
intents.reactions = True
intents.guilds = True
client = commands.Bot(command_prefix='mini ', intents=intents)

TOKEN = os.environ.get('TOKEN')

# Firebase
PATH_TO_JSON = os.environ.get('PATH_TO_JSON')
cred = credentials.Certificate(PATH_TO_JSON)
firebase_admin.initialize_app(cred)

db = firestore.client()


"""FIRESTORE FUNCTIONS"""


# FIRESTORE: Count commands

def get_cmd_count(user):
    if not user.bot:
        doc_ref = db.collection('leaderboard').document(str(user.id))
        cmd_count_ref = doc_ref.get({'cmd_count'}).to_dict()
        if cmd_count_ref is not None:
            return cmd_count_ref.get('cmd_count')
        return 0


def update_cmd_count(user):
    if not user.bot:
        doc_ref = db.collection('leaderboard').document(str(user.id))
        curr_count = get_cmd_count(user)
        doc_ref.set({
            'cmd_count': curr_count + 1,
            'coins': get_coin_count(user)
        })


# FIRESTORE: Count coins

def get_coin_count(user):
    if not user.bot:
        doc_ref = db.collection('leaderboard').document('{}'.format(user.id))
        coin_count_ref = doc_ref.get({'coins'}).to_dict()
        if coin_count_ref.get('coins') is not None:
            return coin_count_ref.get('coins')
        return 0


def update_coin_count(user, addCoins):
    if not user.bot:
        doc_ref = db.collection('leaderboard').document('{}'.format(user.id))
        curr_coins = get_coin_count(user)
        doc_ref.set({
            'cmd_count': get_cmd_count(user),
            'coins': curr_coins + addCoins
        })


"""LOG-IN"""


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


"""COMMANDS"""


# mini help

class MiniHelp(commands.HelpCommand):

    async def send_bot_help(self, mapping):
        update_cmd_count(self.context.message.author)
        embed = embed_mini_help()
        await self.context.send(embed=embed)


client.help_command = MiniHelp()


def embed_mini_help():
    embed = discord.Embed(title=":dart: MinigameBot Command Guide",
                          description="Here is a complete list of all MinigameBot's commands!",
                          colour=discord.Colour.from_rgb(106, 13, 255))
    embed.add_field(name=":question: Need help?", value="`mini help`: A complete list of our features.", inline=False)
    embed.add_field(name=":zap: Get stats!", value="`mini cc`: How many commands have you sent?")
    embed.add_field(name=":coin: Your balance", value="`mini bal`: Tells you your coin balance.")
    embed.add_field(name=":trophy: Leaderboard", value="`mini lead`: See the top 10 richest users!")
    embed.add_field(name=":person_running: Endless Runner", value="`mini run`: The Endless Runner game.")
    embed.add_field(name=":black_joker: Blackjack", value="`mini bj`: Play Blackjack with us.")
    embed.add_field(name=':gift: Mystery box', value='`mini gift`: What prize can you win?')
    return embed


# mini cc

@client.command(name="cc")
async def mini_cc(ctx):
    update_cmd_count(ctx.message.author)
    embed = embed_mini_cc(ctx.message.author)
    await ctx.send(embed=embed)


def embed_mini_cc(user):
    embed = discord.Embed(title=f":computer: {user.name}'s command count",
                          description=f"You have sent me {get_cmd_count(user)} commands!",
                          colour=discord.Colour.from_rgb(106, 13, 255))
    return embed


# mini bal

@client.command(name="bal")
async def mini_bal(ctx):
    update_cmd_count(ctx.message.author)
    embed = embed_mini_coins(ctx.message.author)
    await ctx.send(embed=embed)


def embed_mini_coins(user):
    embed = discord.Embed(title=f":money_with_wings: {user.name}'s Bank Account",
                          description=f"{user.mention} - Earn more coins by playing mini games!",
                          colour=discord.Colour.from_rgb(106, 13, 255))
    embed.add_field(name="Your balance:", value=f"{get_coin_count(user)} :coin:", inline=False)
    return embed


# mini lead

@client.command(name="lead")
async def mini_lead(ctx):
    update_cmd_count(ctx.message.author)
    print(ctx.guild.id)
    embed = embed_leaderboard(ctx.guild.id)
    await ctx.send(embed=embed)


def embed_leaderboard(guild_id):
    guild = client.get_guild(guild_id)
    print(guild.name)
    embed = discord.Embed(title=f":trophy: {guild.name}'s Coin Leaderboard :trophy:",
                          description="",
                          color=discord.Colour.from_rgb(106, 13, 255))

    # sort members by their coin amount
    members_info = []
    for user in guild.members:
        if not user.bot:
            members_info.append((user, get_coin_count(user)))
    members_info.sort(key=lambda x: x[1], reverse=True)

    print(members_info)

    max_members = 10
    leaderboard_list = ""

    index = 0
    for user in members_info:
        # ensure only top 10 members are shown
        index += 1
        if index > max_members:
            break
        # number top three
        if index == 1:
            leaderboard_list += ":first_place: "
        elif index == 2:
            leaderboard_list += ":second_place: "
        elif index == 3:
            leaderboard_list += ":third_place: "
        # add info in format "**coin_bal** - username"
        else:
            leaderboard_list += ":bouquet: "
        leaderboard_list += f"**{user[1]}** - {user[0]}"

    if leaderboard_list == "":
        leaderboard_list = f"There are no active members in {guild.name}. Run `mini help` to earn coins!"

    embed.add_field(name="", value=leaderboard_list)
    return embed


# mini box

@client.command(name="gift")
@commands.cooldown(1, 3600, commands.BucketType.user)
async def mini_gift(ctx):
    update_cmd_count(ctx.message.author)
    embed = embed_mini_gift(ctx.message.author)
    await ctx.send(embed=embed)


def embed_mini_gift(user):
    embed = discord.Embed(title=f":gift: Opening mystery box... :gift:",
                          colour=discord.Colour.from_rgb(106, 13, 255))
    random_coin = randint(1, 50)
    embed.add_field(name="", value=f"{user.mention} your gift is: {random_coin} :coin:!")
    update_coin_count(user, random_coin)
    embed.add_field(name="Your new balance:", value=f"{get_coin_count(user)} :coin:", inline=False)
    return embed


"""GAMES"""


# mini run | Endless Runner

@client.command(name="run")
async def mini_run(ctx):
    update_cmd_count(ctx.message.author)
    embed = embed_mini_construction()
    await ctx.send(embed=embed)


# mini bj | Blackjack
@client.command(name="bj")
async def mini_bj(ctx):
    update_cmd_count(ctx.message.author)
    embed = embed_mini_construction()
    await ctx.send(embed=embed)


"""HELPER FUNCTIONS"""


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title=":ice_cube: Cooldown!",
                              description="Try again in {:.0f} minutes.".format(error.retry_after/60),
                              colour=discord.Colour.from_rgb(106, 13, 255))
        await ctx.send(embed=embed)


def embed_mini_construction():
    embed = discord.Embed(title=":construction: This command is under construction... :construction:",
                          description="Come back soon :)",
                          colour=discord.Colour.from_rgb(106, 13, 255))
    return embed


"""RUN CLIENT"""

client.run(TOKEN)
