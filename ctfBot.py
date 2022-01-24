import discord
import gettext
from inspect import currentframe
import os
import requests
import time
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from config import TOKEN, SCOREBOARD_CHANNEL_ID, CHALLENGES_CHANNEL_ID, DISCUSSION_CHANNEL_ID
from config import LOG_CHANNEL_ID, ADMIN_CHANNEL_ID
from config import HOST, USERNAME, PASSWORD,PORT, DATABASE,COMMAND_PREFIX, LANGUAGE
from databaseHelper import DB

# please select your bot's language here
# lütfen botun dilini seçin
lang_translations = gettext.translation('base', localedir='locale', languages=[LANGUAGE])
lang_translations.install()

# define _ shortcut for translations
# çeviri için _ isimli fonksiyonu tanımla
_ = lang_translations.gettext

# define a function to use formatting with _
# _ ile formatlamayı kullanmak için fonksiyon tanımla
def f(s):
    frame = currentframe().f_back
    return eval(f"f'{s}'", frame.f_locals, frame.f_globals)

# use selected command prefix (like "!command")
# tanımlanmış komut önekini kullan ("!komut" gibi)
client = commands.Bot(command_prefix=COMMAND_PREFIX)

# connect to the database
#veritabanına bağlan
database=DB(HOST, USERNAME, PASSWORD,PORT, DATABASE)



# overrşde the default help message
# varsayılan help komutunu silip yerine kanala göre help mesajı at
client.remove_command("help")
@client.command(name="help", description=f(_("Help message")))
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

# for a better log time define a function
# loglarda zamanı düzgün alması için fonksiyon tanımla
def getTime():
    date = None
    try:
        date = datetime.fromisoformat(requests.get('http://worldtimeapi.org/api/timezone/Europe/Istanbul').json()['datetime'])
    except:
        date = datetime.now()
    return str(date.strftime('%Y-%m-%d %H:%M:%S'))

# print wrapper for logging
# logging için print wrapper
async def logPrint(message):
    log = f"{getTime()} -> {message}"
    print(log)
    await client.get_channel(LOG_CHANNEL_ID).send(log)


# generate a scoreboard
# veritabanındaki kullanıcılara göre skorboard stringi üret
async def makeScoreboard():
    players,length,size=database.getScoreboard()

    scoreboard_string="```\n╭──────┬──────────────────────┬────────╮\n│ " + _("RANK")+" │        "+_("PLAYER")+"        │ "+_("POINT")+"   │\n├──────┼──────────────────────┼────────┼\n"
    for i,player in enumerate(players):
        fetched_user=await client.fetch_user(int(player["discord_id"]))
        player_username=fetched_user.name
        scoreboard_string+=f"│ {str(i+1).ljust(5)}│ {player_username.ljust(21)}│ {str(player['total_points']).ljust(7)}│\n"
    for i in range(length,size):
        scoreboard_string+=f"│ {str(i+1).ljust(5)}│ {'-'.ljust(21)}│ {str(0).ljust(7)}│\n"

    scoreboard_string+="""╰──────┴──────────────────────┴────────╯\n```"""
    return scoreboard_string
# a function to update the scoreboard
# adminlerin skorboardı güncellemesi için komut
async def updateScoreBoard():
    scoreboard=await makeScoreboard()
    channel = client.get_channel(SCOREBOARD_CHANNEL_ID)
    scoreboard_message = await channel.history().find(lambda m: m.author.id == client.user.id)

    # if there is no already a scoreboard
    # daha önce skorboard atılmamışsa...
    if scoreboard_message is None:
        await channel.send(scoreboard)
        await logPrint(f(_("Scoreboard initialized.")))

    # ...otherwise
    # daha önce skorboard atılmışsa
    else:
        await scoreboard_message.edit(content=scoreboard)
        await logPrint(f(_("Scoreboard updated.")))

# hi command
# merhaba komutu
@client.command(description=_('Say hello to our bot!'),brief=_('Say hello to our bot!'))
async def hi(ctx):
    await ctx.send(f(_("Hi {ctx.author.name}")))

# enterflag comman
# flag girme komutu
@client.command(name="enterflag",description=f(_('You should send me flag from DM, {client.command_prefix}enterflag <flag>')),brief=f(_('You should send me flag from DM, {client.command_prefix}enterflag <flag>')))
async def check_flag(ctx, flag):
    # DM'den atmış kontrol etme
    if flag and isinstance(ctx.channel, discord.channel.DMChannel):
        username=ctx.author.name
        await logPrint(f(_("`{username}` has send `{flag}` in dm.")))
        challengeFlag_ret = database.isCorrectFlag(flag, ctx.author.id)
        if challengeFlag_ret[0]=="AlreadySolved":
            challenge_name=challengeFlag_ret[1]
            await ctx.send(f(_("Come on! You already solved `{challenge_name}` challenge.")))
        elif challengeFlag_ret[0]=="NotCorrect":
            await ctx.send(_("Sorry :( This is not a valid flag..."))
        else:
            challengeInfo = challengeFlag_ret[1]
            challenge_name=challengeInfo['name']
            challenge_id=challengeInfo['id']
            user_id=ctx.author.id
            await logPrint(f(_("`{username}` found flag for , `{challenge_name}` challenge.")))
            await ctx.send(f(_("Yey! You found flag for `{challenge_name}` challenge! Dont forget to check out the scoreboard!")))
            await client.get_channel(DISCUSSION_CHANNEL_ID).send(f(_("{ctx.author.mention} , found flag for `{challenge_name}` challenge.")))
            database.updateSolvedChallenge(user_id,challenge_id)
            await updateScoreBoard()
    else:
        await ctx.send(f(_("{ctx.author.mention} Please send flag from DM. Flag format: `{client.command_prefix}enterflag <flag>`")))
        async for message in ctx.channel.history(limit=10):
            if message.author.id == ctx.author.id:
                await message.delete()
                break
@client.command(name="addChallenge",description=f'{client.command_prefix}addChallenge challengename flag point',brief=f'{client.command_prefix}addChallenge challengename flag point')
async def addChallenge(ctx, challenge, flag, point):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.addChallenge(challenge, flag, point)
        await ctx.send(_("Challenge added!"))
    else:
        await ctx.send("There is no spoon")
@client.command(name="deleteUser",description=f'{client.command_prefix}deleteUser discord_id',brief=f'{client.command_prefix}deleteUser discord_id')
async def deleteUser(ctx, discord_id):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.deleteUser(discord_id)
        await updateScoreBoard()
        await ctx.send("<@{}> şutlandı!".format(discord_id))

    else:
        await ctx.send("There is no spoon")
@client.command(name="addUser",description=f'{client.command_prefix}addUser discord_id',brief=f'{client.command_prefix}addUser discord_id')
async def addUser(ctx, discord_id):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.addUser(discord_id)
        await updateScoreBoard()
        await ctx.send(_("Ok. <@{}>, added to scoreboard.").format(discord_id))

    else:
        await ctx.send(_("There is no spoon"))
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
        await ctx.send(_("There is no spoon"))
@client.command(name="deleteChallenge",description=f'{client.command_prefix}deleteChallenge challengeName',brief=f'{client.command_prefix}deleteChallenge challengeName')
async def deleteChallenge(ctx,challengeName):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        database.deleteChallenge(challengeName)
        await ctx.send(f(_("{challengeName} deleted!")))
    else:
        await ctx.send(_("There is no spoon"))
@client.command(name="updateScoreboard",description=f'{client.command_prefix}updateScoreboard',brief=f'{client.command_prefix}updateScoreboard')
async def updateScoreboard(ctx):
    if ctx.channel == client.get_channel(ADMIN_CHANNEL_ID):
        await updateScoreBoard()
        await ctx.send(_("Scoreboard Updated"))
    else:
        await ctx.send(_("There is no spoon"))


@client.command(name="rank",description=_('Shows your point and solved challenges'),brief=_('Shows your point and solved challenges'))
async def rank(ctx):

    user=database.getUser(ctx.author.id)
    if user:
        total_points = user["total_points"]
        solved_challenges =', '.join(database.getChallengeNames(ctx.author.id,solved=True))
        unolved_challenges =', '.join(database.getChallengeNames(ctx.author.id,solved=False))
        msg =f(_("Hi {ctx.author.mention}! You have `{total_points}` point!"))
        """
        msg+=f(_("\n\nThe challenges that you solved:\n```\n{solved_challenges}\n```"))
        msg+=f(_("And you didn't:\n```\n{unolved_challenges}\n```"))
        
        """
        msg += "\n\n" + _("The challenges that you solved:") + f"\n```\n{solved_challenges}\n```"
        msg += _("And you didnt:") + f"\n```\n{unolved_challenges}\n```"
        await ctx.send(msg)
    else:
        await ctx.send(f(_("Hi {ctx.author.mention}! You have `0` point")))

@client.event
async def on_command_error(ctx, error):
    await logPrint(f"ERROR {error}")
@client.event
async def on_error(ctx, error):
    await logPrint(f"ERROR {error}")

@client.event
async def on_ready():
    await logPrint(f(_("{client.user.name} has connected to Discord!")))
    await updateScoreBoard()

client.run(TOKEN)
