
import discord
from discord.ext import commands, tasks
import mysql.connector

TOKEN = "My Token"
CHANNEL_ID = 1194481436032516096

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="nmklop90",
    database="fordiscordbot"
)

mycursor = mydb.cursor()
mycursor.execute("DROP TABLE userss")
mycursor.execute("CREATE TABLE userss(username VARCHAR(40) PRIMARY KEY, id INT)")
mycursor.execute("SHOW TABLES")



bot = commands.Bot(command_prefix='!',intents=discord.Intents.all())
discord.member = True

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("READY")
    for x in mycursor:
        print(x)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    if message.content.startswith("hello"):
        await message.channel.send(f"Hello, {message.author}")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(f"Welcome, {member}")
    
@bot.command()
async def addtoDb(ctx):
    name = ctx.author.name
    print(name)
    mycursor.execute("INSERT INTO userss VALUES (%s, %s)",(name,1))
    mydb.commit()
    print(mycursor.rowcount)
    mycursor.execute("SELECT * FROM userss")
    results = mycursor.fetchall()
    for row in results:
        print(row)

@bot.command()
async def hello(ctx):
    await ctx.send("hello!")

@bot.command()
async def add(ctx, *args):
    sum = 0
    for nums in args:
        sum+=int(nums)
    await ctx.send(sum)
    
bot.run(TOKEN)

