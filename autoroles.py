from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2 as pgdb
import modules.helpers as hlpr

import discord
from discord.utils import get
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents(guilds=True, members=True, emojis=True, guild_messages=True, guild_reactions=True)
bot = commands.Bot(command_prefix='!ar ', intents=intents)
bot.remove_command('help')

@bot.event
async def on_raw_reaction_add(reaction):
    try:
        try:
            # try to initialize db connection, set guild obj, & get watched channels
            ar_db = hlpr.db_connect()
            guild = bot.get_guild(reaction.guild_id)
            channels = hlpr.get_channels(ar_db, guild)
        except pgdb.Error:
            return
        except AttributeError:
            return
        # loop thru watched channels & find match with reaction channel
        for row in channels:
            if reaction.channel_id == row[1]:
                try:
                    # try to get reaction roles & validate reaction emoji
                    react_roles = hlpr.get_react_roles(ar_db, guild)
                    emoji = hlpr.valid_emoji(guild, reaction.emoji)
                except pgdb.Error:
                    continue
                except AttributeError:
                    continue
                # loop thru reaction roles & find match with reaction emoji
                for row in react_roles:
                    if emoji['id'] == row[1] or emoji['id'] == row[2]:
                        try:
                            # try to set role obj from reaction role
                            role = hlpr.valid_role(guild, row[3])
                        except AttributeError:
                            continue
                        if role not in reaction.member.roles:
                            try:
                                # try to update member role
                                try:
                                    # try to set channel obj to reference in role update reason
                                    channel = hlpr.valid_channel(guild, reaction.channel_id)
                                    reason = 'AutoRole added with {0} ({1}) reaction in #{2} ({3}) channel'.format(
                                        emoji['alias'], emoji['id'], channel.name, channel.id)
                                except AttributeError:
                                    # EXCEPTION: channel obj was not correctly set
                                    reason = 'AutoRole added with {0} ({1}) reaction in unknown channel'.format(
                                        emoji['alias'], emoji['id'])
                                await reaction.member.add_roles(role, reason=reason, atomic=True)
                            except discord.errors.Forbidden:
                                try:
                                    # try to post error message if bot was denied permission
                                    await hlpr.find_help(guild, channel, reaction.member, emoji['print'], role, add_role=True)
                                    # return
                                except:
                                    raise
    except:
        # could not update role or alert admins in discord
        pass    # needs logger here
    finally:
        try: ar_db.close()
        except pgdb.InterfaceError: pass
        return

@bot.event
async def on_raw_reaction_remove(reaction):
    try:
        try:
            # try to initialize db connection, set guild obj, & get watched channels
            ar_db = hlpr.db_connect()
            guild = bot.get_guild(reaction.guild_id)
            channels = hlpr.get_channels(ar_db, guild)
        except pgdb.Error:
            return
        except AttributeError:
            return
        # loop thru watched channels & find match with reaction channel
        for row in channels:
            if reaction.channel_id == row[1]:
                try:
                    # try to get reaction roles & validate reaction emoji
                    react_roles = hlpr.get_react_roles(ar_db, guild)
                    emoji = hlpr.valid_emoji(guild, reaction.emoji)
                except pgdb.Error:
                    continue
                except AttributeError:
                    continue
                # loop thru all reaction roles & find match with reaction emoji
                for row in react_roles:
                    if emoji['id'] == row[1] or emoji['id'] == row[2]:
                        try:
                            # try to set role obj from reaction role
                            role = hlpr.valid_role(guild, row[3])
                        except AttributeError:
                            continue
                        try:
                            # try to set member obj bc on_raw_reaction_remove does not provide it
                            member = guild.get_member(reaction.user_id)
                            if member is None: raise AttributeError
                        except AttributeError:
                            # EXCEPTION: member could not be found
                            raise
                        if role in member.roles:
                            try:
                                # try to update member role
                                try:
                                    # try to set channel obj to reference in role update reason
                                    channel = hlpr.valid_channel(guild, reaction.channel_id)
                                    reason = 'AutoRole removed with {0} ({1}) reaction in #{2} ({3}) channel'.format(
                                        emoji['alias'], emoji['id'], channel.name, channel.id)
                                except AttributeError:
                                    # EXCEPTION: channel obj was not correctly set
                                    reason = 'AutoRole removed with {0} ({1}) reaction in unknown channel'.format(
                                        emoji['alias'], emoji['id'])
                                await member.remove_roles(role, reason=reason, atomic=True)
                            except discord.errors.Forbidden:
                                try:
                                    # try to post error message if bot was denied permission
                                    await hlpr.find_help(guild, channel, member, emoji['print'], role, add_role=False)
                                    # return
                                except:
                                    raise

    except:
        # could not update role or alert admins in discord
        pass    # needs logger here
    finally:
        try: ar_db.close()
        except pgdb.InterfaceError: pass
        return

            
@bot.command()
@commands.bot_has_permissions(embed_links=True, send_messages=True)
async def help(ctx):
    msg = discord.Embed(title='AutoRoles Commands', colour=discord.Colour.dark_purple())
    msg.add_field(name='\u200b', value='__**Manager Cmds**__', inline=False)
    msg.add_field(name='!ar config', value='See the current configuration of AutoRoles.', inline=False)
    msg.add_field(name='!ar watchchannel *ChannelName*', value='Designate a channel for AutoRoles to watch for reactions. Required.\n*- Make sure AutoRoles is a member of any watched channels.*', inline=False)
    msg.add_field(name='!ar forgetchannel *ChannelName*', value='Remove specific channel from AutoRoles watch list.', inline=False)
    msg.add_field(name='!ar addlink *emoji* *RoleName*', value='Link a specific reaction emoji to a certain role.\n*- Make sure AutoRoles\' role is higher than the roles it needs to manage.*', inline=False)
    msg.add_field(name='!ar droplink *emoji* *RoleName*', value='Remove link between a specific reaction emoji and role.', inline=False)
    msg.add_field(name='\u200b', value='__**Admin Cmds**__', inline=False)
    msg.add_field(name='!ar addmgrrole *RoleName*', value='Give AutoRoles permissions to an additional role.\n*- Administrators always have permissions.*', inline=False)
    msg.add_field(name='!ar dropmgrrole *RoleName*', value='Remove AutoRoles permissions from manager role.', inline=False)
    await ctx.channel.send(embed=msg)

@bot.event
async def on_command_error(ctx, error):
    error = getattr(error, 'original', error)

    if isinstance(error, commands.MissingPermissions):
        await ctx.channel.send(error)
    elif isinstance(error, commands.BotMissingPermissions):
        try:
            await ctx.channel.send(error)
        except discord.errors.Forbidden:
            await ctx.user.send(error)
    elif isinstance(error, commands.MissingAnyRole):
        if len(error.missing_roles) > 0:
            await ctx.channel.send(error)
        else:
            await ctx.channel.send('You are missing Administrator permission(s) to run this command.')
    print(ctx, error)

@bot.event
async def on_ready():
    hlpr.get_logger('ar_logger')
    bot.load_extension('cogs.Admin')
    bot.load_extension('cogs.Manager')

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.run(TOKEN)