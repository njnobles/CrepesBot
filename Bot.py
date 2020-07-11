import discord
import asyncio
import os
from discord.ext import commands
from mcstatus import MinecraftServer

from utils.ChannelWatchManager import ChannelManager

channelManager = ChannelManager()

token = None
if 'CREPESBOT_TOKEN' in os.environ:
    token = os.environ['CREPESBOT_TOKEN']

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))

async def my_background_task():
    await bot.wait_until_ready()
    while not bot.is_closed():  
        for channel in channelManager.channels: 
            status_embeds = channelManager.get_updated_status_embeds(channel)
            if(len(status_embeds) > 0):
                for em in status_embeds:
                    await channel.send(embed=em)
            #else:
                #await channel.send(embed=discord.Embed(title='No status updates', color=0x0000ff))

        await asyncio.sleep(12)

@bot.event
async def on_ready():
    print('Bot is ready')

@bot.command()
async def shutdown(ctx):
    await ctx.send(embed=discord.Embed(title='Shutting down CrepesBot...', color=0xff00ff))
    await ctx.bot.logout()

@bot.command()
async def clear(ctx, *, number):
    try:
        msgs = [] #Empty list to put all the messages in the log
        number = int(number) #Converting the amount of messages to delete to an integer
        msgs = await ctx.channel.history(limit=number).flatten()
        await ctx.channel.delete_messages(msgs)
    except Exception as e:
        print(e)
        pass

@bot.command()
async def add(ctx, *, server):
    channelManager.add_server(ctx.channel, server)
    await ctx.send(f'Now Watching: {server}')

@bot.command()
async def status(ctx):
    await ctx.send('Checking status...')
    status_embeds = channelManager.get_status_embeds(ctx.channel)
    if(len(status_embeds) > 0):
        for em in status_embeds:
            await ctx.send(embed=em)
    else:
        await ctx.send(embed=discord.Embed(title='No status updates'))


bot.loop.create_task(my_background_task())
bot.run(token)
