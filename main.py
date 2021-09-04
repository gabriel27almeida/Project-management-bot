import discord
import os
import datetime
from discord.ext import commands
from replit import db
from tabulate import tabulate

client = commands.Bot(command_prefix = '.')

"""
Auxiliary functions:
- Add task to a user's personal to do list
- Delete task from a user's personal to do list
- Change state of a task
- Calculate time intervals
"""

def add_task(user, task, due_date):
  if user in db.keys():
    lista = db[user]
    lista.append((task, 'Undone', due_date))
    db[user]=lista
  else:
    db[user] = [(task, 'Undone', due_date)]

def delete_task(user, index_list):
  if user not in db.keys():
    return
  else:
    lista = db[user]
    for i in range(len(index_list)):
      index_list[i] = int(index_list[i])
    index_list.sort(reverse=True)
    for index in index_list:
      index = index - 1
      if len(lista)>index:
        del lista[index]
    db[user]=lista
  
def set_state(user, index, state):
  if user in db.keys():
    lista = db[user]
    lista[index-1][1]=state
    return True

def time_left(due_date):
  if due_date == 'None':
    return '\U0000221E'
  day = int(due_date.split("/", 2)[0])
  month = int(due_date.split("/", 2)[1])
  year = int(due_date.split("/", 2)[2])
  delta_t = datetime.datetime(year, month, day) - datetime.datetime.now()
  return delta_t.days


def my_sort(a):
  ans = 0
  if(a[1]=='Done'):
    ans = ans + 1024
  
  due_date = a[2]
  if due_date == 'None':
    ans = ans + 512
  else:
    ans = ans + time_left(due_date)
  
  return ans
  
def sort_tasks(user):
  if user not in db.keys():
    return

  lista = db[user].value
  lista.sort(key=my_sort)
  db[user]=lista


""""
Events:
- When bot is ready
- When a reaction is added
"""
  
@client.event
async def on_ready():
  print('Bot is ready.')

#Comands by reactions
@client.event
async def on_reaction_add(reaction, user):
  if reaction.emoji == '\N{WHITE HEAVY CHECK MARK}':
    #complete task
    index = int(reaction.message.content.split(' ', 1)[0])
    completed = set_state(str(user.id), index, 'Done')
    if completed:
      await reaction.message.channel.send('Task completed!')

  if reaction.emoji == '\U0001F527':
    #Change task state to "Doing"
    index = int(reaction.message.content.split(' ', 1)[0])
    changed = set_state(str(user.id), index, 'Doing')
    if changed:
      await reaction.message.channel.send('State changed to: Doing')

  if reaction.emoji == '\U0001F504':
    #Sort the tasks list by urgency 
    author=str(user.id)
    sort_tasks(author)
    if author in db.keys():
      await reaction.message.channel.send('List sorted by urgency!')
      #edit message
      i=1
      table=[['#', 'Task', 'State', 'Due date']]
      for (task, state, due_date) in db[author].value:
        table.append([i, task, state, due_date])
        i = i+1
      
      await reaction.message.edit(content= f'```\n{tabulate(table, headers="firstrow")}\n```')


  
"""
Commands:
- Add a new task
- List all tasks
- Delete task
- Details about task
"""

#Add task command
@client.command()
async def newtask(ctx, *, msg):
  author = str(ctx.author.id)
  if('&' in msg):
    (task, due_date) = msg.split('&', 1)
  else:
    task=msg
    due_date = 'None'
  
  add_task(author, task, due_date)
  await ctx.send('Task added to the list.')

#List all tasks command
@client.command()
async def list(ctx):
  author = str(ctx.author.id)
  if author in db.keys():
    i=1
    table=[['#', 'Task', 'State', 'Due date']]
    for (task, state, due_date) in db[author].value:
      table.append([i, task, state, due_date])
      i = i+1
    message = await ctx.send(f'```\n{tabulate(table, headers="firstrow")}\n```')
    await message.add_reaction('\U0001F504')

  else:
    await ctx.send('No tasks record.')


#Delete tasks command
@client.command()
async def delete(ctx, *,msg):
  author = str(ctx.author.id)
  index_list = msg.split(',')
  delete_task(author, index_list)
  
  await ctx.send('Task(s) deleted!')


#Details about task
@client.command()
async def details(ctx, index):
  author = str(ctx.author.id)
  if author in db.keys():
    lista = db[author].value
    task = lista[int(index)-1][0]
    state = lista[int(index)-1][1]
    due_date = lista[int(index)-1][2]
    days = time_left(due_date)

    message = await ctx.send(f'#{index} {task}\nState: {state}\nYou have {days} days left\n--\nReact with \N{WHITE HEAVY CHECK MARK} in order to complete the task.\nReact with \U0001F527 to change the state to Doing')

    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
    await message.add_reaction('\U0001F527')

    



TOKEN = os.environ['TOKEN']
client.run(TOKEN)
