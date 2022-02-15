import os
from dotenv import load_dotenv
#for local tests
try:
    load_dotenv('.env')
except:
    pass

#DISCORD RELATED
TOKEN                 = os.getenv("DISCORD_TOKEN")                       #string
COMMAND_PREFIX        = os.getenv("DISCORD_COMMAND_PREFIX")              #string
SCOREBOARD_CHANNEL_ID = int(os.getenv("DISCORD_SCOREBOARD_CHANNEL_ID"))  #integer
CHALLENGES_CHANNEL_ID = int(os.getenv("DISCORD_CHALLENGES_CHANNEL_ID"))  #integer
DISCUSSION_CHANNEL_ID = int(os.getenv("DISCORD_DISCUSSION_CHANNEL_ID"))  #integer
LOG_CHANNEL_ID        = int(os.getenv("DISCORD_LOG_CHANNEL_ID"))         #integer
ADMIN_CHANNEL_ID      = int(os.getenv("DISCORD_ADMIN_CHANNEL_ID"))       #integer

#DATABASE RELATED
HOST                  = os.getenv("DATABASE_HOST")                       #string
USERNAME              = os.getenv("DATABASE_USERNAME")                   #string
PASSWORD              = os.getenv("DATABASE_PASSWORD")                   #string
PORT                  = int(os.getenv("DATABASE_PORT"))                  #integer
DATABASE              = os.getenv("DATABASE_DATABASE")                   #string

#BOT LANGUAGE
LANGUAGE              = os.getenv("BOT_LANGUAGE")                        #string, ex "tr","en"
