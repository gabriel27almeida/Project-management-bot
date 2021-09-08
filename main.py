import discord
import os
import datetime
import time
import asyncio
from discord.ext import commands
from replit import db
from tabulate import tabulate



client = commands.Bot(command_prefix = '.')

"""
Auxiliary functions:
- Add task 
- Delete tasks
- Calculate time left to a due date
- Sorting criteria
- Sort tasks based on sorting criteria
- Get name from a member
- Reset database
- Set state of a task
"""

def add_task(user_id, message):
  task = message
  due_date='None'
  if '&' in message:
    task, due_date = message.split('&', 1)
  
  if user_id in db.keys():
    db[user_id].append((task, 'Undone', due_date, 'None'))
  else:
    db[user_id]=[(task, 'Undone', due_date, 'None')]

def delete_tasks(user_id, index_list):
  lista = db[user_id]
  for i in range(len(index_list)):
    index_list[i] = int(index_list[i])
  index_list.sort(reverse=True)
  
  for index in index_list:
    index -= 1
    if len(lista)>index:
      del lista[index]

  db[user_id]=lista

def time_left(due_date, mode):
  if mode == 1:
    if due_date == 'None':
      return '\U0000221E'
    day = int(due_date.split("/", 2)[0])
    month = int(due_date.split("/", 2)[1])
    year = int(due_date.split("/", 2)[2])
    delta_t = datetime.datetime(year, month, day) - datetime.datetime.now()
    return delta_t.days
  if mode == 2:
    #Calculate seconds left to 8am of a specified day
    day = int(due_date.split("/", 2)[0])
    month = int(due_date.split("/", 2)[1])
    year = int(due_date.split("/", 2)[2])
    delta_t = datetime.datetime(year, month, day, 8) - datetime.datetime.now()
    return delta_t.seconds

def my_sort(a):
  ans = 0
  if(a[1]=='Done'):
    ans = ans + 1024
  
  due_date = a[2]
  if due_date == 'None':
    ans = ans + 512
  else:
    ans = ans + time_left(due_date,1)
  
  return ans
  
def sort_tasks(user):
  if user not in db.keys():
    return

  lista = db[user].value
  lista.sort(key=my_sort)
  db[user]=lista

def get_name(member):
  name = member.nick
  if name is None:
    name = member.name
  return name

def reset_db():
  for key in db.keys():
    del db[key]

def set_state(user_id, index, state):
  if user_id in db.keys():
    lista = db[user_id]
    if len(lista)> index - 1:
      lista[index-1][1] = state
      db[user_id] = lista
      return f'State changed to \"{state}\"'
    else:
      return 'Invalid index'
  else:
    return 'User not found'


  



"""
Events:
- When bot is ready
- When a reaction is added
"""

@client.event 
async def on_ready():
  print('Bot is ready')
  #reset_db()

@client.event
async def on_reaction_add(reaction, user):
  if reaction.emoji == '\U0001F504':
    #check if it's a "command" reaction
    if user.id != 881239395372523600 and reaction.message.author.id == 881239395372523600:
      #sort list by urgency
      message = reaction.message.content
      first_line = message.split('\n',1)[0]
      user = first_line.split(' ', 1)[1]
      user_id = db[user]
      sort_tasks(str(user_id))
      i=1
      table=[['#', 'Task', 'State', 'Due date']]
      for (task, state, due_date, notes) in db[str(user_id)].value:
        table.append([i, task, state, due_date])
        i = i+1
      await reaction.message.edit(content = f'User: {user}\n```\n{tabulate(table, headers="firstrow")}\n```')
      await reaction.message.channel.send('Tasks sorted by urgency')

  if reaction.emoji == '\N{WHITE HEAVY CHECK MARK}' or reaction.emoji == '\U0001F527':
    if user.id != 881239395372523600 and reaction.message.author.id == 881239395372523600:
      #Change state to done or doing
      message = reaction.message.content
      first_line = message.split('\n',1)[0]
      index, user = first_line.split(' ', 1)

      index = int(index[1])
      user_id = db[user]

      message = ''
      if reaction.emoji== '\N{WHITE HEAVY CHECK MARK}':
        message = set_state(str(user_id), index, 'Done')
      else:
        message = set_state(str(user_id), index, 'Doing')
      
      await reaction.message.channel.send(message)



#Error handling
"""
@client.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.MemberNotFound):
    await ctx.send('Utilizador não encontrado')
"""





"""
Initial configurations commands:
- Add member to some team 
- List members of some team
- Remove members from some team
"""

@client.command()
async def newmember(ctx, aula, *,user: commands.MemberConverter):
  key = 'aula' + str(aula)
  name = get_name(user)

  if key in db.keys():
    db[key].append(user.id)
  else:
    db[key]=['None', 'None', user.id] #future meeting, notes, team members
  db[name] = user.id
  await ctx.send('Membro adicionado')

@client.command()
async def members(ctx, aula):
  key = 'aula' + str(aula)
  if key in db.keys():
    lista = f'Equipa da aula {aula}:\n'
    for user_id in db[key].value:
      if type(user_id) is str:
        continue

      member = await ctx.guild.fetch_member(user_id)
      name = get_name(member)
      lista += str(name) + '\n'
    await ctx.send(lista)
  else:
    await ctx.send('Aula inválida')

@client.command()
async def removemember(ctx, aula, user: commands.MemberConverter):
  key = 'aula' + str(aula)
  if key in db.keys():
    lista = db[key].value
    for i in range(len(lista)):
      if lista[i] == user.id:
        del lista[i]
    db[key]=lista
  await ctx.send(f'Membro retirado da aula {aula}')




"""
Commands:
- Add task
- List user's tasks
- Details about task
- Add/Edit notes of a task
- Add/Edit due date of a task
- Delete task(s)
"""


#Add task
@client.command()
async def newtask(ctx, user: commands.MemberConverter, *,message):
  add_task(str(user.id), message)
  await ctx.send('Tarefa adicionada')

#List user's tasks
@client.command()
async def list(ctx, *,member: commands.MemberConverter):
  user = str(member.id)
  if user in db.keys():
    name = get_name(member)
    i=1
    table=[['#', 'Task', 'State', 'Due date']]
    for (task, state, due_date, notes) in db[user].value:
      table.append([i, task, state, due_date])
      i = i+1
    message = await ctx.send(f'User: {name}\n```\n{tabulate(table, headers="firstrow")}\n```')
    await message.add_reaction('\U0001F504')
  else:
    await ctx.send('No tasks')

#Details about task
#To do: add emojis
@client.command()
async def details(ctx, user: commands.MemberConverter, index):
  author = str(user.id)
  if author in db.keys():
    lista = db[author].value

    task = lista[int(index)-1][0]
    state = lista[int(index)-1][1]
    due_date = lista[int(index)-1][2]
    notes = lista[int(index)-1][3]
    days = time_left(due_date,1)

    name = get_name(user)

    message = await ctx.send(f'#{index} {name}\n**Task:** {task}\n**State:** {state}\n**Days left:** {days}\n**Notes:** {notes}\n--\nReact with \N{WHITE HEAVY CHECK MARK} in order to complete the task.\nReact with \U0001F527 to change the state to Doing')

    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
    await message.add_reaction('\U0001F527')

@client.command()
async def addnotes(ctx, user: commands.MemberConverter, index, *, notes):
  author = str(user.id)
  if author in db.keys():
    index = int(index) - 1
    lista = db[author].value
    if index >= 0 and index < len(lista):
      lista[index][3] = notes
      db[author] = lista
      await ctx.send('Notes added')
    else:
      await ctx.send('Invalid index')
  
@client.command()
async def duedate(ctx, user: commands.MemberConverter, index, *, data):
  author = str(user.id)
  if author in db.keys():
    index = int(index) - 1
    lista = db[author].value
    if index >= 0 and index < len(lista):
      lista[index][2] = data
      db[author] = lista
      await ctx.send('Due date updated')
    else:
      await ctx.send('Invalid index')

@client.command()
async def delete(ctx, user: commands.MemberConverter,*, indexs):
  author = str(user.id)
  if author in db.keys():
    index_lista = indexs.split(',')
    delete_tasks(author, index_lista)
    await ctx.send('Task(s) deleted!')


"""
Team commands:
- Status report
"""

#TO DO: Set reminder to team members in the morning
@client.command()
async def meeting(ctx, aula, *, data):
  key = 'aula' + aula
  if key in db.keys():
    lista = db[key].value
    lista[0] = data
    db[key] = lista
    await ctx.send('New meeting added')

    meeting_time, meeting_day = data.split(' ', 1)
    seconds = time_left(meeting_day, 2)
    
    await asyncio.sleep(seconds)

    if db[key].value[0] == data:
      #meeting date hasn't been changed
      mentions = ''
      for user_id in db[key]:
        if type(user_id) is str:
          continue
        mentions += f'<@{user_id}> '
          
      await ctx.send(f'{mentions}\nLembrete para reunião hoje. Hora: {meeting_time}')

    
    


@client.command()
async def newnotes(ctx, aula, *, notes):
  key = 'aula' + aula
  if key in db.keys():
    lista = db[key].value
    lista[1] = notes
    db[key] = lista
    await ctx.send('Notes added')


@client.command()
async def statusreport(ctx, aula):
  key = 'aula'+aula
  if key in db.keys():
    table = {
      'Undone' : ['To do'],
      'Doing' : ['Doing'],
      'Done' : ['Done']
    }
    for user_id in db[key].value:
      if type(user_id) is str:
        continue
      for (task, state, due_date, notes) in db[str(user_id)].value:
        member = await ctx.guild.fetch_member(user_id)
        name = get_name(member)
        
        lista = table[state]
        lista.append(f'{task} ({name})')
        table[state] = lista
    
    meeting_date = db[key].value[0]
    notes = db[key].value[1]
    await ctx.send(f'**Aula {aula}**\n```{tabulate(table, headers="firstrow")}```\nNext meeting: {meeting_date}\nNotes: {notes}')
       





TOKEN = os.environ['TOKEN']
client.run(TOKEN)
