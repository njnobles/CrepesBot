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

async def clear_bot_messages(channel):
    msgs = await channel.history(limit=10).flatten()
            
    crepesbot_msgs = []
    for msg in msgs:
        if msg.author == bot.user:
            crepesbot_msgs.append(msg)
        else:
            break
    if len(crepesbot_msgs) > 0:
        await channel.delete_messages(crepesbot_msgs)

async def my_background_task():
    await bot.wait_until_ready()
    while not bot.is_closed(): 
        try:
            for channel in channelManager.channels: 
                status_embeds = channelManager.get_updated_status_embeds(channel)
                if(len(status_embeds) > 0):
                    await clear_bot_messages(channel)
                    for em in status_embeds:
                        await channel.send(embed=em)
                #else:
                    #await channel.send(embed=discord.Embed(title='No status updates', color=0x0000ff))
        except Exception as e:
            print(e)
            pass

        await asyncio.sleep(60)

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
    try:
        channelManager.add_server(ctx.channel, server)
        await ctx.send(embed=discord.Embed(title=f'Now Watching: {server}'))
    except Exception as e:
        print(e)
        await ctx.send(embed=discord.Embed(title=f'Error trying to watch: {server}'))
        pass

@bot.command()
async def remove(ctx, *, server):
    try:
        channelManager.remove_server(ctx.channel, server)
        await ctx.send(embed=discord.Embed(title=f'Stopped Watching: {server}'))
    except Exception as e:
        print(e)
        await ctx.send(embed=discord.Embed(title=f'Error trying to stop watching: {server}'))
        pass

@bot.command()
async def watchlist(ctx):
    try:
        watchlist = channelManager.get_watchlist(ctx.channel)
        em = discord.Embed(title='Watchlist')

        servers = ""
        if len(watchlist) == 0:
            servers="None"
        else:
            servers = "\n".join(watchlist)
        em.add_field(name="Servers", value=servers, inline=True)

        await ctx.send(embed=em)
    except Exception as e:
        print(e)
        await ctx.send(embed=discord.Embed(title='Error getting watchlist...'))
        pass

@bot.command()
async def status(ctx):
    try:
        await ctx.send(embed=discord.Embed(title='Checking status...'))
        status_embeds = channelManager.get_status_embeds(ctx.channel)
        if(len(status_embeds) > 0):
            await clear_bot_messages(ctx.channel)
            for em in status_embeds:
                await ctx.send(embed=em)
        else:
            await ctx.send(embed=discord.Embed(title='No status updates'))
    except Exception as e:
        print(e)
        await ctx.send(embed=discord.Embed(title='Error checking status...'))
        pass


bot.loop.create_task(my_background_task())
bot.run(token)
