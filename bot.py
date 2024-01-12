
import discord
from discord.ext import commands, tasks
from discord.ui import Button
import mysql.connector
import zoneinfo

TOKEN = "My TOKEN"
CHANNEL_ID = 1195225140351467591

# my local database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="nmklop90",
    database="fordiscordbot"
)

mycursor = mydb.cursor(buffered=True)
# for testing
#mycursor.execute("DROP TABLE userss") 
mycursor.execute("CREATE TABLE userss(username VARCHAR(40) PRIMARY KEY, joined_server DATE, coins INT DEFAULT(100))")
mycursor.execute("SHOW TABLES")



bot = commands.Bot(command_prefix='!',intents=discord.Intents.all())
discord.member = True

# NOT NEEDED, THIS IS FOR TESTING
def printDb():
    print(mycursor.rowcount)
    mycursor.execute("SELECT * FROM userss")
    results = mycursor.fetchall()
    for row in results:
        print(row)


def insertToDb(member):
    mycursor.execute("SELECT COUNT(username) FROM userss WHERE username = %s", (member.name,))
    inside = mycursor.fetchone()
    if inside[0] != 0:
        return
    est = zoneinfo.ZoneInfo('America/New_York')
    est_time = member.joined_at.astimezone(est)
    mycursor.execute("INSERT INTO userss (username, joined_server) VALUES (%s, %s)",(member.name,est_time))
    mydb.commit()
    printDb()
    
@bot.event
async def on_ready():
    # channel = bot.get_channel(CHANNEL_ID)
    # await channel.send("READY")
    for mem in bot.get_all_members():
        insertToDb(mem)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    if message.content.startswith("hello"):
        await message.channel.send(f"HAIIIIIIIIII, {message.author}")

@bot.event
async def on_member_join(member):
    
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(f"Welcome, {member}")
    insertToDb(member)
    
# NOT NEEDED ANYMORE ?
# @bot.command()
# async def addtoDb(ctx):
#     name = ctx.author
#     insertToDb(name)

@bot.command()
async def hello(ctx):
    await ctx.send("hello!")

@bot.command()
async def add(ctx, *args):
    sum = 0
    for nums in args:
        sum+=int(nums)
    await ctx.send(sum)
    
    
@bot.command()
async def when_joined(ctx):
    mycursor.execute("SELECT joined_server FROM userss WHERE username = %s", (ctx.author.name,))
    inside = mycursor.fetchone()
    await ctx.send(f"{ctx.author.name} joined at",inside[0])


@bot.command()
async def rps(ctx):
    username = ctx.author.name
    but = Button( style=discord.ButtonStyle.grey, label="idk", emoji="🤑")
    butt = discord.ui.View()
    butt.add_item(but)
    
    await ctx.send(view = butt)

bot.run(TOKEN)

