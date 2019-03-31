import discord
import asyncio
import json
from discord.ext import commands
import os
import logging
import sqlalchemy as sql
import requests



logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


default_prefix = "!"


sqlEngine = sql.create_engine("sqlite:///botdata.sqlite3")
sqlConn = sqlEngine.connect()
sqlMetadata = sql.MetaData(sqlEngine)

class sqlTablesHolder():
	# prefixes = sql.Table("prefixes", sqlMetadata, sql.Column('id', sql.Integer, primary_key=True, nullable=False), sql.Column('guild_id', sql.String),sql.Column('prefix', sql.String))
	# modulok = sql.Table("modulok", sqlMetadata, sql.Column('id', sql.Integer, primary_key=True, nullable=False), sql.Column('guild_id', sql.String),sql.Column('modul_neve', sql.String), sql.Column('allapot', sql.Integer))
	swears = sql.Table("swears", sqlMetadata, sql.Column('id', sql.Integer, primary_key=True, nullable=False), sql.Column('guild_id', sql.String),sql.Column('user_id', sql.String), sql.Column('username', sql.String), sql.Column('display_name', sql.String), sql.Column('points', sql.Integer))
	messages = sql.Table("messages", sqlMetadata, sql.Column('id', sql.Integer, primary_key=True, nullable=False), sql.Column('guild_id', sql.String),sql.Column('channel_id', sql.String),sql.Column('user_id', sql.String), sql.Column('channel_name', sql.String), sql.Column('message', sql.String), sql.Column('point', sql.Integer))
	pass

sqlTables = sqlTablesHolder()

sqlMetadata.create_all()

bot = commands.Bot(command_prefix=default_prefix)


TOKEN = ""
try:
	with open("key.txt") as f:
		try:
			TOKEN = f.read()
		except:
			print(27*"=")
			raise(" Can't access key.txt file")
			print(27*"=")
			exit()
except:
	print(23*"=")
	print(" NO key.txt FILE FOUND")
	print(23*"=")
	exit()


bug_tracker_webhook = None
try:
	with open("bug_tracker_webhook.txt") as f:
		try:
			bug_tracker_webhook = f.read()
		except:
			pass
except:
	print("Bug reports disabled, can't load webhook url")




try:
	with open("swears.txt", "r") as f:
		sweartxt = f.read()
		swears = sweartxt.split(", ")
except:
	with open("swears.txt", "w") as f:
		f.write("basz, bassz, bazd, picsa, picsá, pina, piná, fasz, geci, kurva, pénisz, kúrt, szop, buzi, szar, dug\n")
		swears = ["basz", "bassz", "bazd", "picsa", "picsá", "pina", "piná", "fasz", "geci", "kurva", "pénisz", "kúrt", "szop", "buzi", "szar", "dug"]

bot.remove_command('help')
attachedMessages = {}

@bot.event
async def on_raw_reaction_add(payload):
	if payload.user_id != bot.user.id:
		try:
			message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
		except:
			pass
		else:
			if payload.emoji.is_unicode_emoji() and payload.emoji.name == "\U0001F5D1" and message.author.id == payload.user_id: # :wastebin:
				if attachedMessages.get(str(payload.message_id)):
					for m in attachedMessages.get(str(payload.message_id)):
						try:
							await m.delete()
						except:
							pass
					del attachedMessages[str(payload.message_id)]


@bot.event
async def on_ready():
	#await bot.change_presence(activity=discord.Activity(name='Test',type=0))
	print("Everything's all ready to go~")

	
@bot.event
async def on_message(message):
	if message.guild:
		print("[("+message.guild.name+") "+message.channel.name+" : "+message.author.name+"] "+message.content)
	else:
		print("["+message.author.name+"] "+message.content)
	moderate = False
	for swear in swears:
		if swear in message.content:
			moderate = True
			break
	if moderate:# and message.content[:len(default_prefix)] != default_prefix:
		ctx = await bot.get_context(message)
		r = sqlConn.execute(sqlTables.swears.select().where(sqlTables.swears.c.guild_id == str(ctx.guild.id)).where(sqlTables.swears.c.user_id == str(message.author.id))).fetchone()
		if r:
			swearCounter = r.points + 1
			sqlConn.execute(sqlTables.swears.update().where(sqlTables.swears.c.guild_id == str(ctx.guild.id)).where(sqlTables.swears.c.user_id == str(message.author.id)).values(points = r.points + 1))
		else:
			swearCounter = 1
			sqlConn.execute(sqlTables.swears.insert().values(guild_id = str(ctx.guild.id), user_id = str(message.author.id), points = 1, username = message.author.name, display_name = message.author.display_name))
		sqlConn.execute(sqlTables.messages.insert().values(guild_id = str(ctx.guild.id), channel_id = str(message.channel.id) ,user_id = str(message.author.id), message = message.content, channel_name = message.channel.name, point = swearCounter))
		try:
			await message.delete()
		except:
			pass
		await ctx.send("<@"+str(message.author.id)+"> Ne káromkodj! :rage: (ez a(z) "+str(swearCounter)+". figyelmeztetés)", delete_after=2.0)
	else:
		await bot.process_commands(message)

	
@bot.command()
@commands.check(lambda ctx: True if ctx.guild else False)
@commands.has_permissions(administrator=True)
async def karomkodolista(ctx, page=1):
	# try:
		# await ctx.message.delete()
	# except:
		# pass
	top = sqlConn.execute(sqlTables.swears.select().where(sqlTables.swears.c.guild_id == str(ctx.guild.id)).order_by(sqlTables.swears.c.points.desc()).offset((page-1)*10).limit(10)).fetchmany(-1)
	embed = discord.Embed(
		color=0xf3b221, 
		#description="Káromkodók listája",
		title="Káromkodók listája - "+str(page)+". oldal")
	loops = 0
	topstr = ""
	for item in top:
		if loops < 10:
			loops += 1
			#embed.add_field(name=str(loops)+". "+item.title, value=item.desc, inline=False)
			#embed.description += str(loops)+". "+item.title+"\n"
			topstr += str((page-1)*10 + loops)+". "+item.display_name+" - "+str(item.points)+" figyelmeztetés\n"
	embed.add_field(name="Káromkodás szerinti sorban:", value=topstr if len(topstr) > 0 else "Üres oldal", inline=False)
	# embed.add_field(name="field4", value="field4 értéke", inline=True)
	answer = await ctx.send(embed=embed)
	await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
	attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	
@bot.command()
@commands.check(lambda ctx: True if ctx.guild else False)
@commands.has_permissions(administrator=True)
async def torol(ctx, member=""):
	if member == "" or len(ctx.message.mentions) != 1:
		answer = await ctx.send("Meg kell jelölnöd a parancs után egy felhasználót, akinek a történetét resetelni szeretnéd!")
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	else:
		member = ctx.message.mentions[0]
		sqlConn.execute(sqlTables.swears.delete().where(sqlTables.swears.c.guild_id == str(ctx.guild.id)).where(sqlTables.swears.c.user_id == str(member.id)))
		sqlConn.execute(sqlTables.messages.delete().where(sqlTables.messages.c.guild_id == str(ctx.guild.id)).where(sqlTables.messages.c.user_id == str(member.id)))
		answer = await ctx.send(member.display_name+" története és figyelmeztetései törölve!")
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]

@bot.command()
@commands.check(lambda ctx: True if ctx.guild else False)
@commands.has_permissions(administrator=True)
async def tortenet(ctx, member=""):
	if member == "" or len(ctx.message.mentions) != 1:
		answer = await ctx.send("Meg kell jelölnöd a parancs után egy felhasználót, akinek a történetét meg szeretnéd nézni!")
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	else:
		member = ctx.message.mentions[0]
		# try:
			# await ctx.message.delete()
		# except:
			# pass
		top = sqlConn.execute(sqlTables.messages.select().where(sqlTables.messages.c.guild_id == str(ctx.guild.id)).where(sqlTables.messages.c.user_id == str(member.id)).order_by(sqlTables.messages.c.point)).fetchmany(-1)
		embed = discord.Embed(
			color=0xf3b221, 
			#description="Káromkodók listája",
			title=member.display_name +" káromkodásai")
		loops = 0
		topstr = ""
		for item in top:
			if item:
				loops += 1
				#embed.add_field(name=str(loops)+". "+item.title, value=item.desc, inline=False)
				#embed.description += str(loops)+". "+item.title+"\n"
				#topstr += str(item.point)+". #"+item.channel.name+": "+str(item.message)+" figyelmeztetés\n"
				embed.add_field(name=str(item.point)+". figyelmeztetés:", value="#"+item.channel_name+": "+str(item.message) if len(str(item.message)) < 700 else "#"+item.channel_name+": "+str(item.message)[:700]+"...", inline=False)
		#embed.add_field(name="Figyelmeztetés szerinti sorban:", value=topstr if len(topstr) > 0 else "Nem káromkodott", inline=False)
		# embed.add_field(name="field4", value="field4 értéke", inline=True)
		answer = await ctx.send(embed=embed)
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
		
@bot.command()
@commands.check(lambda ctx: True if ctx.guild else False)
async def bug(ctx, *, report=""):
	if report == "":
		answer = await ctx.send("Nem adtál meg semmilyen szöveget!")
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	elif not bug_tracker_webhook:
		answer = await ctx.send("Nincs engedélyezve a bug bejelentés!")
		await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
		attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	else:
		
		payload = {
			"username" : bot.user.name,
			"avatar_url": bot.user.avatar_url,
			"embeds": [
				{
					"title": "Bug report",
					"description": "Hibát észleltek egy bottal kapcsolatban",
					"color": 13632027,
					"footer": {
						"icon_url": ctx.message.author.avatar_url,
						"text": ctx.message.author.name+"#"+ctx.message.author.discriminator
					},
					"author": {
						"name": bot.user.name,
						"icon_url": bot.user.avatar_url
					},
					"fields": [
						{
							"name": "Bejelentő guild:",
							"value": str(ctx.guild.name) + " ("+str(ctx.guild.id)+")",
							"inline": True
						},
						{
							"name": "Bejelentő channel:",
							"value": str(ctx.message.channel.name) + " ("+str(ctx.message.channel.id)+")",
							"inline": True
						},
						{
							"name": "Bejelentő member:",
							"value": str(ctx.message.author.name)+"#"+ctx.message.author.discriminator + " ("+str(ctx.message.author.id)+")",
							"inline": True
						},
						{
							"name": "Jelentés:",
							"value": report if len(report) < 1024 else report[:1000]+"..."
						}
					]
				}
			]
		}
		headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
		try:
			#print(bug_tracker_webhook)
			r = requests.post(bug_tracker_webhook, json=payload, headers=headers)
			#print(r.text)
		except:
			answer = await ctx.send("Bug report elküldése sikertelen")
			await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
			attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
		else:
			answer = await ctx.send("Köszönjük a visszajelzést, ha a hibát valósnak látjuk, értesülni fogsz a javítás állapotáról")
			await ctx.message.add_reaction("\U0001F5D1") # :wastebasket:
			attachedMessages[str(ctx.message.id)] = [ctx.message, answer]
	


#print(swears)
bot.run(TOKEN)