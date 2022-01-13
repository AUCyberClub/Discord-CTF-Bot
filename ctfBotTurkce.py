import discord
import os
import requests
import time
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from config import TOKEN, SCOREBOARD_CHANNEL_ID, CHALLENGES_CHANNEL_ID, DISCUSSION_CHANNEL_ID
from config import LOG_CHANNEL_ID, ADMIN_CHANNEL_ID
from config import HOST, USERNAME, PASSWORD,PORT, DATABASE,COMMAND_PREFIX
from databaseHelper import DB

client = commands.Bot(command_prefix=COMMAND_PREFIX)


database=DB(HOST, USERNAME, PASSWORD,PORT, DATABASE)


# Varsayılan help komutunu silip yerine kanala göre help mesajı atmak için yazılmıştır.
client.remove_command("help")
@client.command(name="help", description="Help mesajı")
async def help(ctx):
    helptext = "```"
    public_commands=["hi","rank","enterflag"]
    isAdminChannel= ctx.channel == client.get_channel(ADMIN_CHANNEL_ID)
    for command in client.commands:
        text=f"{client.command_prefix}{command.name.ljust(17)}  ----> {command.description}\n"
        if command.name in public_commands:
            helptext+=text
        elif isAdminChannel:
            helptext+=text
    helptext+="```"
    await ctx.send(helptext)

# Loglarda zamanı düzgün alması için
def getTime():
    date = None
    try:
        date = datetime.fromisoformat(requests.get('http://worldtimeapi.org/api/timezone/Europe/Istanbul').json()['datetime'])
    except:
        date = datetime.now()
    return str(date.strftime('%Y-%m-%d %H:%M:%S'))

# Logging için print wrapper
async def logPrint(message):
    log = f"{getTime()} -> {message}"
    print(log)
    await client.get_channel(LOG_CHANNEL_ID).send(log)



# Veritabanındaki kullanıcılara göre skorboard stringi üretir.
async def makeScoreboard():
    players,length,size=database.getScoreboard()

    scoreboard_string="""```\n╭──────┬──────────────────────┬────────╮\n│ SIRA │        OYUNCU        │ PUAN   │\n├──────┼──────────────────────┼────────┼\n"""
    for i,player in enumerate(players):
        fetched_user=await client.fetch_user(int(player["discord_id"]))
        player_username=fetched_user.name
        scoreboard_string+=f"│ {str(i+1).ljust(5)}│ {player_username.ljust(21)}│ {str(player['total_points']).ljust(7)}│\n"
    for i in range(length,size):
        scoreboard_string+=f"│ {str(i+1).ljust(5)}│ {'-'.ljust(21)}│ {str(0).ljust(7)}│\n"

    scoreboard_string+="""╰──────┴──────────────────────┴────────╯\n```"""
    return scoreboard_string
# Adminlerin skorboardı güncellemesi için kopmut
async def updateScoreBoard():
    scoreboard=await makeScoreboard()
    channel = client.get_channel(SCOREBOARD_CHANNEL_ID)
    scoreboard_message = await channel.history().find(lambda m: m.author.id == client.user.id)
    # Daha önce skorboard atılmamışsa
    if scoreboard_message is None:
        await channel.send(scoreboard)
        await logPrint(f"Scoreboard initialized.")
    # Daha önce skorboard atılmışsa
    else:
        await scoreboard_message.edit(content=scoreboard)
        await logPrint(f"Scoreboard updated.")

# Merhaba komutu
@client.command(description='Botumuza merhaba de!',brief='Botumuza merhaba de!')
async def hi(ctx):
    await ctx.send(f"Hi {ctx.author.name}")


# flag girme komutu
@client.command(name="enterflag",description=f'flagi özelden bana atmalsın, {client.command_prefix}enterflag <flag>',brief=f'flagi özelden bana atmalsın, {client.command_prefix}enterflag <flag>')
async def check_flag(ctx, flag):
    # DM'den atmış kontrol etme
    if flag and isinstance(ctx.channel, discord.channel.DMChannel):
        username=ctx.author.name
        await logPrint(f"`{username}` has send `{flag}` in dm.")
        challengeFlag_ret = database.isCorrectFlag(flag, ctx.author.id)
        if challengeFlag_ret[0]=="AlreadySolved":
            challenge_name=challengeFlag_ret[1]
            await ctx.send(f"`{challenge_name}` adlı challenge'i önceden zaten çözdün!")
        elif challengeFlag_ret[0]=="NotCorrect":
            await ctx.send("Üzgünüm:( Bu hiçbir challenge'ın flagı değil!")
        else:
            challengeInfo = challengeFlag_ret[1]
            challenge_name=challengeInfo['name']
            challenge_id=challengeInfo['id']
            user_id=ctx.author.id
            await logPrint(f"`{username}` , `{challenge_name}` adlı challenge için flagı buldu.")
            await ctx.send(f"Mükemmelsin! `{challenge_name}` adlı challenge için flagı buldun! Skorboarda bakmayı unutma!")
            await client.get_channel(DISCUSSION_CHANNEL_ID).send(f"{ctx.author.mention} , `{challenge_name}` adlı challenge için flagı buldu.")
            database.updateSolvedChallenge(user_id,challenge_id)
            await updateScoreBoard()
    else:
        await ctx.send(f"{ctx.author.mention} lütfen flagi bana özelden at. Flag formatı `{client.command_prefix}enterflag <flag>`")
        async for message in ctx.channel.history(limit=10):
            if message.author.id == ctx.author.id:
                await message.delete()
                break
@client.command(name="addChallenge",description=f'{client.command_prefix}addChallenge challengename flag point',brief=f'{client.command_prefix}addChallenge challengename flag point')
async def addChallenge(ctx, challenge, flag, point):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.addChallenge(challenge, flag, point)
        await ctx.send("Challenge eklendi!")
    else:
        await ctx.send("Ben aslında yoğum!")
@client.command(name="deleteUser",description=f'{client.command_prefix}deleteUser discord_id',brief=f'{client.command_prefix}deleteUser discord_id')
async def deleteUser(ctx, discord_id):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.deleteUser(discord_id)
        await updateScoreBoard()
        await ctx.send("<@{}> şutlandı!".format(discord_id))

    else:
        await ctx.send("Başarısızlıklar söz konusu :(")
@client.command(name="addUser",description=f'{client.command_prefix}addUser discord_id',brief=f'{client.command_prefix}addUser discord_id')
async def addUser(ctx, discord_id):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.addUser(discord_id)
        await updateScoreBoard()
        await ctx.send("Tamamdır. <@{}>, scoreboarda eklendi.".format(discord_id))

    else:
        await ctx.send("Başarısızlıklar söz konusu :(")
@client.command(name="showChallenges",description=f'{client.command_prefix}showChallenges',brief=f'{client.command_prefix}showChallenges')
async def showChallenges(ctx):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        challenges = database.getChallenges()
        m="```\n"
        for challenge in challenges:
            m+=f"""{challenge['name']} : {challenge['flag']} :{challenge['points']} \n"""
        m+="```"
        await ctx.send(m)
    else:
        await ctx.send("Ben aslında yoğum")
@client.command(name="deleteChallenge",description=f'{client.command_prefix}deleteChallenge challengeName',brief=f'{client.command_prefix}deleteChallenge challengeName')
async def deleteChallenge(ctx,challengeName):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.deleteChallenge(challengeName)
        await ctx.send(f"{challengeName} deleted!")
    else:
        await ctx.send("Ben aslında yoğum")
@client.command(name="updateScoreboard",description=f'{client.command_prefix}updateScoreboard',brief=f'{client.command_prefix}updateScoreboard')
async def updateScoreboard(ctx):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        await updateScoreBoard()
        await ctx.send("Scoreboard Updated")
    else:
        await ctx.send("Ben aslında yoğum")


@client.command(name="rank",description='Puanını ve çözdüğün challengeları gösterir',brief='Puanını ve çözdüğün challengeları gösterir')
async def rank(ctx):

    user=database.getUser(ctx.author.id)
    if user:
        total_points = user["total_points"]
        solved_challenges =', '.join(database.getChallengeNames(ctx.author.id,solved=True))
        unolved_challenges =', '.join(database.getChallengeNames(ctx.author.id,solved=False))
        msg =f"Hey {ctx.author.mention} toplamda `{total_points}` puanın var!"
        msg+=f"\n\nÇözdüğün challengelar:\n```\n{solved_challenges}\n```"
        msg+=f"Henüz çözmediğin challengelar:\n```\n{unolved_challenges}\n```"
        await ctx.send(msg)
    else:
        await ctx.send(f"Hey {ctx.author.mention} toplamda `0` puanın var")

@client.event
async def on_command_error(ctx, error):
    await logPrint(f"ERROR {error}")
@client.event
async def on_error(ctx, error):
    await logPrint(f"ERROR {error}")

@client.event
async def on_ready():
    await logPrint(f"{client.user.name} has connected to Discord")
    await updateScoreBoard()

client.run(TOKEN)
