from typing import List
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from discord import ui, app_commands
from discord.app_commands import Choice
import mysql.connector
import zoneinfo
import random
import time
import asyncio

TOKEN = "My token"
CHANNEL_ID = None # must be integer
OWNERS_ID = {000000,0000000} # integers as well
GUILD_ID = 000000000000 #integers

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="nmklop90",
    database="fordiscordbot"
)

mycursor = mydb.cursor(buffered=True)
# mycursor.execute("DROP TABLE userss") # for testing
# mycursor.execute(
#     "CREATE TABLE userss(username VARCHAR(40) PRIMARY KEY, joined_server DATE, coins INT DEFAULT(100), level INT DEFAULT(0), exp INT DEFAULT(0))"
# )
# mycursor.execute("SHOW TABLES")
search = False


bot = commands.Bot(command_prefix='!',intents=discord.Intents.all())
discord.member = True


def getGuild():
    return bot.guilds[0]

def insertToDb(member):
    mycursor.execute("SELECT COUNT(username) FROM userss WHERE username = %s", (member.name,))
    inside = mycursor.fetchone()
    if inside[0] != 0:
        return
    est = zoneinfo.ZoneInfo('America/New_York')
    est_time = member.joined_at.astimezone(est)
    mycursor.execute("INSERT INTO userss (username, joined_server) VALUES (%s, %s)",(member.name,est_time))
    mydb.commit()

def updateExp(name):
    mycursor.execute("SELECT COUNT(username) FROM userss WHERE username = %s", (name,))
    if mycursor.fetchone()[0] == 0:
        print(mycursor.fetchone()[0])
        return
    mycursor.execute("SELECT level, exp FROM userss WHERE username = %s", (name,))
    row = mycursor.fetchone()
    level = row[0]
    exp = row[1]
    exp+=1
    if exp == 100:
        level+=1
        exp=0
    mycursor.execute("UPDATE userss SET level = %s, exp = %s WHERE username = %s",(level,exp,name))
    mydb.commit()

def getCoins(interaction):
    name = interaction.user.name
    mycursor.execute("SELECT coins FROM userss WHERE username = %s",(name,))
    return mycursor.fetchone()[0]

async def validBet(interaction, bet):
    coins = getCoins(interaction)
    if coins == 0 or coins < bet:
        await interaction.response.send_message("Invalid bet.")
        return False
    return True
    
def updateCoins(interaction, won, bet):
    coins = getCoins(interaction)
    if won:
        coins+=(bet*2)
    else:
        coins-=bet
        
    print(coins , interaction.user.name)
    mycursor.execute("UPDATE userss SET coins = %s WHERE username = %s",(coins,interaction.user.name))
    mydb.commit()   
       
async def getMessage(interaction, line, limit):
    def check(m):
        if m.author.name == interaction.user.name and m.channel == interaction.channel:
            try:
                int(m.content)
                return True
            except ValueError:
                return False
        return False
    await interaction.channel.send(line)
    
    try:
        return await bot.wait_for("message", check=check, timeout=limit)
    except asyncio.TimeoutError:
        await interaction.channel.send("Too Slow!!!")
        return 

@bot.event
async def on_ready():
    for mem in bot.get_all_members():
        insertToDb(mem)
    bot.tree.clear_commands(guild=getGuild())
    print(GUILD_ID)
    print(bot.guilds)
    print(bot.guilds[0])
    # GUILD_ID = bot.guilds[0]
    # bot.tree.copy_global_to(guild=GUILD_ID)
    # await bot.tree.sync(guild=GUILD_ID)
    if search:
        for channel in bot.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                async for mess in channel.history(limit=None):
                        updateExp(mess.author.name)
    print("DONE")
    
@bot.command()
async def sync(ctx):
    if ctx.author.id in OWNERS:
        synced = await bot.tree.sync()
        print('Command tree synced.')
        await ctx.send(f"Synced {len(synced)} commands")
    else:
        await ctx.send('You dont have permission for this.')

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    updateExp(message.author.name)

@bot.event
async def on_member_join(member):
    
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(f"Welcome, {member}")
    insertToDb(member)

@bot.tree.command(name="get_user", description="User's level, exp, and coins")
async def get_user(interaction: discord.Interaction, username: discord.Member):
    
    mycursor.execute("SELECT level,exp, coins FROM userss WHERE username = %s",(username.name,))
    row = mycursor.fetchone()
    await interaction.response.send_message(f"{username.name} is level {row[0]}, with {row[1]}/100 exp and {row[2]} coins")

@bot.tree.command(name="coins_leaderboard", description="Most coins")
async def coinsleaderboard(interaction: discord.Interaction):
    mycursor.execute("SELECT username, coins FROM userss ORDER BY coins DESC")
    all = mycursor.fetchall()
    line = ""
    for row in all:
        line+= f"{row[0]}: {row[1]} coins\n"
    await interaction.response.send_message(line)

@bot.tree.command(name="exp_leaderboard", description="Users with the highest levels")
async def expleaderboard(interaction: discord.Interaction):
    mycursor.execute("SELECT username, level, exp FROM userss ORDER BY level DESC, exp DESC")
    all = mycursor.fetchall()
    line = ""
    for row in all:
        line+=f"{row[0]}, level: {row[1]}, exp: {row[2]}\n"
    await interaction.response.send_message(line)

@bot.tree.command(name="joined_server", description="When did the user join this server")
async def when_joined(interaction: discord.Interaction, username: discord.Member):
    mycursor.execute("SELECT joined_server FROM userss WHERE username = %s", (username.name,))
    inside = mycursor.fetchone()
    await interaction.response.send_message(f"{username.name} joined at "+str(inside[0]))

class rpsHelper(View):
    def __init__(self, bet):
        super().__init__()
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
        await interaction.response.edit_message(view=self, content=f"{interaction.user.name} has chosen **{emoji[choice]}**!")
        time.sleep(3)
        mes = await interaction.message.edit(view=None, content=f"They chose **{emoji[self.num]}**!")
        time.sleep(2)
        if choice == self.num:
            await interaction.message.edit(content="**TIE!**, You lose nothing 😅")
            return
        elif choice == 1 and self.num == 3:
            await interaction.message.edit(content="🧱 beats ✂️, You winnnn!!!!")
        elif choice == 2 and self.num == 1:
            await interaction.message.edit(content="📄 beats 🧱, You winnnn!!!!")
        elif choice == 3 and self.num == 2:
            await interaction.message.edit(content="✂️ beats 📄, You winnnn!!!!")
        else:
            win = False 
            await interaction.message.edit(content=f"{emoji[self.num]} beats {emoji[choice]}, You lost!")
        
        updateCoins(interaction, win, self.bet)

@bot.tree.command(name='rps', description="Rock, Paper, or Scissors")
async def rps(interaction: discord.Interaction, bet: int):
    if (await validBet(interaction, bet)) is False:
        return
    hlper = rpsHelper(bet)
    await interaction.response.send_message("Pick a choice! Rock, Paper, or Scissors",view = hlper)


@bot.tree.command(name="guess", description="Guess the number")
async def guess(interaction: discord.Interaction, bet: int):
    # valid = await validBet(bet)
    if (await validBet(interaction, bet)) is False:
        return 
    answer = random.randrange(1,101)
    print(answer)
    lower = 1
    upper = 100
    lives = 5
    async def getChoice():
        choice = 0
        while int(choice) < lower or upper < int(choice):
            line = f"**{interaction.user.name}**, Pick a number **between {lower} and {upper}**. "
            choice = await getMessage(interaction, line, 20)
            if choice == None:
                return 
            choice = int(choice.content)
            if int(choice) < lower or upper < int(choice):
                await interaction.channel.send("Invalid choice, pick again.")
        return choice
        
    while True:
        choice = await getChoice()
        if choice is None:
            return
        if answer == choice:
            await interaction.channel.send(f"You found the answer, it is {answer}!!")
            updateCoins(interaction, True, bet)
            return
        if answer < choice:
            upper = choice-1
        else:
            lower = choice+1
        lives-=1
        if lives == 0:
            break
        await interaction.channel.send(f"Incorrect")
    await interaction.channel.send(f"You lost, the correct answer was {answer}")
    updateCoins(interaction, False, bet)

bot.run(TOKEN)

