import discord
import os
from discord.ext import commands
from replit import db

client = commands.Bot(command_prefix = '.')

def update_list(user, task):
  if user in db.keys():
    lista = db[user]
    lista.append(task)
    db[user]=lista
  else:
    db[user] = [task]

def complete_task(user, index):
  if user not in db.keys():
    return
  else:
    lista = db[user]
    index = index - 1
    if len(lista)>index:
      del lista[index]
      db[user]=lista

  
@client.event
async def on_ready():
  print('Bot is ready.')

@client.command()
async def newtask(ctx, *, task):
  author = str(ctx.author.id)
  update_list(author, task)
  await ctx.send('Task added to the list.')

@client.command()
async def list(ctx):
  author = str(ctx.author.id)
  if author in db.keys():
    i=1
    for task in db[author].value:
      await ctx.send(f'{i} {task}\n')
      i = i+1
  else:
    await ctx.send('No tasks.')

@client.command()
async def complete(ctx, index):
  author = str(ctx.author.id)
  complete_task(author, int(index))
  await ctx.send('Task completed!')


TOKEN = os.environ['TOKEN']
client.run(TOKEN)
