import psycopg2 as pgdb
import discord
from discord.ext import commands

import modules.helpers as hlpr

async def predicate(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    else:
        try:
            ar_db = hlpr.db_connect()
            mgr_roles = hlpr.get_managers(ar_db, ctx.guild)
        except:
            return False
        finally:
            try: ar_db.close()
            except: pass

            roles = []
            for row in mgr_roles:
                try:
                    role = hlpr.valid_role(ctx.guild, row[1])
                except:
                    break
                if role in ctx.author.roles:
                    return True
                else:
                    roles.append(role)
            raise commands.MissingAnyRole(roles)
is_mgr = commands.check(predicate)

class Manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ar_logger = hlpr.get_logger('ar_logger')

    async def cog_command_error(self, ctx, error):
        try: self.ar_db.close()
        except: pass

    @commands.command()
    @is_mgr
    async def watchchannel(self, ctx, arg):
        try:
            self.ar_db = hlpr.db_connect()
            channel = hlpr.get_channel(self.ar_db, ctx.guild, ctx.author, arg)
            msg = 'Watching channel {} for reactions'.format(channel[0].mention)
        except Exception as err:
            self.ar_logger.warning('Error: ', exc_info=1)
            msg = ('{0} on: {1}'.format(err, arg))
        finally:
            await ctx.channel.send(msg)
            try: self.ar_db.close()
            except: pass
            return

    @commands.command()
    @is_mgr
    async def forgetchannel(self, ctx, arg):
        try:
            self.ar_db = hlpr.db_connect()
            channel = hlpr.del_channel(self.ar_db, ctx.guild, arg)
            msg = 'Ignoring channel {} for reactions'.format(channel.mention)
        except Exception as err:
            self.ar_logger.warning('Error: ', exc_info=1)
            msg = ('{0} on: {1}'.format(err, arg))
        finally:
            await ctx.channel.send(msg)
            try: self.ar_db.close()
            except: pass
            return

    @commands.command()
    @is_mgr
    async def addlink(self, ctx, arg1, arg2):
        try:
            self.ar_db = hlpr.db_connect()
            react_role = hlpr.get_react_role(self.ar_db, ctx.guild, ctx.author, arg1, arg2)
            msg = 'Adding @{0} role with {1} reaction'.format(react_role[1].name, react_role[0]['print'])
        except Exception as err:
            self.ar_logger.warning('Error: ', exc_info=1)
            msg = ('{0} on: {1} {2}'.format(err, arg1, arg2))
        finally:
            await ctx.channel.send(msg)
            try: self.ar_db.close()
            except: pass
            return

    @commands.command()
    @is_mgr
    async def droplink(self, ctx, arg1, arg2):
        try:
            self.ar_db = hlpr.db_connect()
            react_role = hlpr.del_react_role(self.ar_db, ctx.guild, arg1, arg2)
            msg = 'Ignoring @{0} role with {1} reaction'.format(react_role[1].name, react_role[0]['print'])
        except Exception as err:
            self.ar_logger.warning('Error: ', exc_info=1)
            msg = ('{0} on: {1} {2}'.format(err, arg1, arg2))
        finally:
            await ctx.channel.send(msg)
            try: self.ar_db.close()
            except: pass
            return
    
    @commands.command()
    @is_mgr
    async def config(self, ctx):
        try:
            self.ar_db = hlpr.db_connect()
            manager_rows = hlpr.get_managers(self.ar_db, ctx.guild)
            channel_rows = hlpr.get_channels(self.ar_db, ctx.guild)
            reactive_rows = hlpr.get_react_roles(self.ar_db, ctx.guild)
        except Exception as err:
            self.ar_logger.warning('Error: ', exc_info=1)
            await ctx.channel.send(err)
            try: self.ar_db.close()
            except: pass
            return

        msg = discord.Embed(title='Current Configuration', colour=discord.Colour.dark_purple())

        try:
            # set embed field name & try to get mgr role/user ids from db
            name = 'Manager Roles:'
            if len(manager_rows) == 0:
                value = 'No manager roles\n*Administrators always have permissions.*'
            else:
                value = '*Administrators always have permissions.*'
                for row in manager_rows:
                    try:
                        # try to validate found role_id & mention mgr role by name
                        manager = hlpr.valid_role(ctx.guild, row[1])
                        value += '\n**@{0}**'.format(manager.name)
                    except:
                        # remove manager row if invalid
                        hlpr.del_manager(self.ar_db, ctx.guild, row[1], obsolete=True)
                        continue
                    try:
                        # try to validate found user_id & mention by name
                        author = hlpr.valid_user(ctx.guild, row[0])
                        value += ' - added by {0}'.format(author.name)
                    except:
                        # fallback on 'unknown user' if author not found (deleted or removed)
                        value += ' - added by unknown user'
        except pgdb.Error:
            value = 'DB Error: Could not find saved manager roles'
        finally:
            # add the embed field with available results
            msg.add_field(name=name, value=value, inline=False)

        try:
            # set embed field name & try to get channel/user ids from db
            name = 'Watched Channels:'
            if len(channel_rows) == 0:
                value = 'No watched channels\n(AutoRoles will not assign any roles.)'
            else:
                value = '*Make sure AutoRoles is a member of any watched channels.*'
                for row in channel_rows:
                    try:
                        # try to validate found channel_id & mention channel by name
                        channel = hlpr.valid_channel(ctx.guild, row[1])
                        value += '\n{0}'.format(channel.mention)
                    except:
                        # remove channel row if invalid
                        hlpr.del_channel(self.ar_db, ctx.guild, row[1], obsolete=True)
                        continue
                    try:
                        # try to validate found user_id & mention by name
                        author = hlpr.valid_user(ctx.guild, row[0])
                        value += ' - added by {0}'.format(author.name)
                    except:
                        # fallback on 'unknown user' if author not found (deleted or removed)
                        value += ' - added by unknown user'
        except pgdb.Error:
            value = 'DB Error: Could not find saved channels'
        finally:
            # add the embed field with available results
            msg.add_field(name=name, value=value, inline=False)

        try:
            # set embed field name & try to get channel/user ids from db
            name = 'Reaction Roles:'
            if len(reactive_rows) == 0:
                value = 'No reactions linked to any roles\n(AutoRoles will not assign any roles.)'
            else:
                value = '*Make sure AutoRoles\' role is higher than the roles it needs to manage.*'
                for row in reactive_rows:
                    try:
                        # try to validate found emoji & role
                        emoji = row[1] or row[2]
                        emoji = hlpr.valid_emoji(ctx.guild, emoji)
                        role = hlpr.valid_role(ctx.guild, row[3])
                        value += '\n{0} linked to **@{1}** role'.format(emoji['print'], role.name)
                    except:
                        # remove reaction role row if invalid
                        hlpr.del_react_role(self.ar_db, ctx.guild, emoji, row[3], obsolete=True)
                        continue
                    try:
                        # try to validate found user_id & mention by name
                        author = hlpr.valid_user(ctx.guild, row[0])
                        value += ' - added by {0}'.format(author.name)
                    except:
                        # fallback on 'unknown user' if author not found (deleted or removed)
                        value += ' - added by unknown user'
        except pgdb.Error:
            value = 'DB Error: Could not find saved reaction roles'
        finally:
            # add the embed field with available results
            msg.add_field(name=name, value=value, inline=False)

        await ctx.channel.send(embed=msg)
        try: self.ar_db.close()
        except: pass
        return

def setup(bot):
    bot.add_cog(Manager(bot))