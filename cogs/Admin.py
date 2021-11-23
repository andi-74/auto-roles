import discord
from discord.ext import commands

import modules.helpers as hlpr

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ar_logger = hlpr.get_logger('ar_logger')
        
    async def cog_command_error(self, ctx, error):
        try: self.ar_db.close()
        except: pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addmgrrole(self, ctx, arg):
        try:
            self.ar_db = hlpr.db_connect()
            mgr_role = hlpr.get_manager(self.ar_db, ctx.guild, ctx.author, arg)
            msg = 'Allowing role {} AutoRoles permissions'.format(mgr_role[0].mention)
        except Exception as err:
            self.ar_logger.warning('Error: ', exc_info=1)
            msg = ('{0}: {1}'.format(err, arg))
        finally:
            await ctx.channel.send(msg)
            try: self.ar_db.close()
            except: pass
            return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dropmgrrole(self, ctx, arg):
        try:
            self.ar_db = hlpr.db_connect()
            mgr_role = hlpr.del_manager(self.ar_db, ctx.guild, arg)
            msg = 'Disallowing role {} AutoRoles permissions'.format(mgr_role.mention)
        except Exception as err:
            self.ar_logger.warning('Error: ', exc_info=1)
            msg = ('{0}: {1}'.format(err, arg))
        finally:
            await ctx.channel.send(msg)
            try: self.ar_db.close()
            except: pass
            return

def setup(bot):
    bot.add_cog(Admin(bot))