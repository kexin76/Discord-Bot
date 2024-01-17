
from typing import Optional
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from discord import ui, app_commands
import mysql.connector
import zoneinfo
import random
import time
import asyncio

TOKEN = "My Token"
CHANNEL_ID = 1195225140351467591

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="nmklop90",
    database="fordiscordbot"
)

mycursor = mydb.cursor(buffered=True)
mycursor.execute("DROP TABLE userss") # for testing
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

# def updateExp(mem):
    

@bot.event
async def on_ready():
    for mem in bot.get_all_members():
        insertToDb(mem)
    # for channel in bot.get_all_channels():
    #     async for mess in channel.history(limit=None):
            

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

@bot.command()
async def when_joined(ctx):
    mycursor.execute("SELECT joined_server FROM userss WHERE username = %s", (ctx.author.name,))
    inside = mycursor.fetchone()
    await ctx.send(f"{ctx.author.name} joined at",inside[0])

@bot.command()
async def db(ctx):
    mycursor.execute("SELECT * FROM userss")
    results = mycursor.fetchall()
    for row in results:
        await ctx.send(row)

def getCoins(ctx):
    name = ctx.author.name
    mycursor.execute("SELECT coins FROM userss WHERE username = %s",(name,))
    return mycursor.fetchone()[0]
    
async def validBet(ctx, bet):
    coins = getCoins(ctx)
    if coins == 0 or coins < bet:
        await ctx.send("Invalid bet.")
        return False
    return True


def updateCoins(ctx, won, bet):
    coins = getCoins(ctx)
    if won:
        coins+=(bet*2)
    else:
        coins-=bet
        
    print(coins , ctx.author.name)
    mycursor.execute("UPDATE userss SET coins = %s WHERE username = %s",(coins,ctx.author.name))
    mydb.commit()    


class rpsHelper(View):
    def __init__(self,ctx, bet):
        super().__init__()
        self.ctx = ctx
        self.num = random.randrange(1,4)
        self.bet = bet
    
    @discord.ui.button( style=discord.ButtonStyle.blurple, emoji="🧱", custom_id="rock")
    async def rps_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.results(interaction,button, 1)
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="📄",custom_id="paper")
    async def pap(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.results(interaction,button, 2)
    @discord.ui.button(style=discord.ButtonStyle.green, emoji="✂️", custom_id="scissor")
    async def sci(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.results(interaction,button, 3)
        
    
    async def results(self, interaction: discord.Interaction, button: discord.ui.Button, choice):
        emoji = {1:"🧱", 2:"📄", 3:"✂️"}
        win = True
        for box in self.children:
            box.disabled = True
        await interaction.response.edit_message(view=self, content=f"{self.ctx.author.name} has chosen **{emoji[choice]}**!")
        time.sleep(3)
        mes = await self.ctx.reply(f"They chose **{emoji[self.num]}**!")
        time.sleep(2)
        if choice == self.num:
            await mes.edit(content="**TIE!**, You lose nothing 😅")
            return
        elif choice == 1 and self.num == 3:
            await mes.edit(content="🧱 beats ✂️, You winnnn!!!!")
        elif choice == 2 and self.num == 1:
            await mes.edit(content="📄 beats 🧱, You winnnn!!!!")
        elif choice == 3 and self.num == 2:
            await mes.edit(content="✂️ beats 📄, You winnnn!!!!")
        else:
            win = False 
            await mes.edit(content=f"{emoji[self.num]} beats {emoji[choice]}, You lost!")
        
        updateCoins(self.ctx, win, self.bet)

async def getMessage(ctx, line, limit):
    def check(m):
        if m.author == ctx.author and m.channel == ctx.channel:
            try:
                int(m.content)
                return True
            except ValueError:
                return False
        return False
    await ctx.send(line)
    
    try:
        return await bot.wait_for("message", check=check, timeout=limit)
    except asyncio.TimeoutError:
        await ctx.send("Too Slow!!!")
        return 

@bot.command()
async def rps(ctx):
    bet = await getMessage(ctx, "Enter your bet: ", 15)
    if bet == None:
        return 
    bet = int(bet.content)
    valid = await validBet(ctx, bet)
    if valid is False:
        return
    hlper = rpsHelper(ctx, bet)
    await ctx.reply("Pick a choice! Rock, Paper, or Scissors",view = hlper)

@bot.command()
async def guess(ctx):
    bet = await getMessage(ctx, "Enter your bet: ", 15)
    if bet == None:
        return
    bet = int(bet.content)
    valid = await validBet(ctx, bet)
    if valid is False:
        return 
    answer = random.randrange(1,101)
    print(answer)
    lower = 1
    upper = 100
    lives = 5
    async def getChoice():
        line = f"Pick number from {lower} to {upper}"
        choice = await getMessage(ctx, line, 20)
        if choice == None:
            return 
        choice = int(choice.content)
        if int(choice) < lower or upper < int(choice):
            await ctx.send("Invalid choice, pick again.")
            getChoice()
        return choice
    while True:
        choice = await getChoice()
        if choice is None:
            return
        if answer == choice:
            await ctx.send(f"You found the answer, it is {answer}!!")
            updateCoins(ctx, True, bet)
            return
        if answer < choice:
            upper = choice-1
        else:
            lower = choice+1
        lives-=1
        if lives == 0:
            break
        await ctx.send(f"Incorrect, the number is from {lower} to {upper}")
    await ctx.send(f"You lost, the correct answer was {answer}")
    updateCoins(ctx, False, bet)

bot.run(TOKEN)

