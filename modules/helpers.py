import os
import sys
import logging
import logging.handlers
import psycopg2 as pgdb
from urllib.parse import urlparse
import emoji as emojis

import discord
from discord.utils import get
from discord.ext import commands

DB_URL = os.getenv('HEROKU_POSTGRESQL_COPPER_URL')
FORMATTER = '%(asctime)s %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# intents = discord.Intents(guilds=True, members=True, emojis=True, guild_messages=True, guild_reactions=True)
# bot = commands.Bot(command_prefix='!ar ', intents=intents)

## GET GUILD ROWS FROM TABLE ##
def get_managers(db, guild):
    # try to validate Discord guild first
    try:
        guild = valid_guild(guild)
    except:
        raise

    try:
        cursor = db.cursor()
        sql_select = 'SELECT * FROM get_managers(%s)'
        cursor.execute(sql_select, (str(guild.id), ))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

def get_channels(db, guild):
    # try to validate Discord guild first
    try:
        guild = valid_guild(guild)
    except:
        raise

    try:
        cursor = db.cursor()
        sql_select = 'SELECT * FROM get_channels(%s)'
        cursor.execute(sql_select, (str(guild.id), ))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

def get_react_roles(db, guild):
    # try to validate Discord guild first
    try:
        guild = valid_guild(guild)
    except:
        raise

    try:
        cursor = db.cursor()
        sql_select = 'SELECT * FROM get_react_roles(%s)'
        cursor.execute(sql_select, (str(guild.id), ))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

## ADD NEW ROW & RETRIEVE KEY ##
def get_manager(db, guild, author, role):
    # try to validate Discord guild/user/role first
    try:
        guild = valid_guild(guild)
        author = valid_user(guild, author)
        role = valid_role(guild, role)
    except:
        raise

    try:
        sql_select = 'SELECT get_manager(%s, %s, %s)'
        tup_vals = (guild.id, author.id, role.id)
        sql_values = tuple(map(lambda x: str(x) if x is not None else x, tup_vals))
    except TypeError:
        raise TypeError('Type Error: Could not form query. Requires iterable')

    try:
        cursor = db.cursor()
        cursor.execute(sql_select, sql_values)
        row = cursor.fetchone()
        cursor.close()
        db.commit()
        return (role, row)
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

def get_channel(db, guild, author, channel):
    # try to validate Discord guild/user/channel first
    try:
        guild = valid_guild(guild)
        author = valid_user(guild, author)
        channel = valid_channel(guild, channel)
    except:
        raise

    try:
        sql_select = 'SELECT get_channel(%s, %s, %s)'
        tup_vals = (guild.id, author.id, channel.id)
        sql_values = tuple(map(lambda x: str(x) if x is not None else x, tup_vals))
    except TypeError:
        raise TypeError('Type Error: Could not form query. Requires iterable')

    try:
        cursor = db.cursor()
        cursor.execute(sql_select, sql_values)
        row = cursor.fetchone()
        cursor.close()
        db.commit()
        return (channel, row)
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

def get_react_role(db, guild, author, emoji, role):
    # try to validate Discord guild/user/emoji/role first
    try:
        guild = valid_guild(guild)
        author = valid_user(guild, author)
        emoji = valid_emoji(guild, emoji)
        role = valid_role(guild, role)
    except:
        raise

    try:
        emoji_custom = int(emoji['id'])
        emoji_unicode = None
    except ValueError:
        emoji_custom = None
        emoji_unicode = emoji['id']

    try:
        sql_select = 'SELECT get_react_role(%s, %s, %s, %s, %s)'
        tup_vals = (guild.id, author.id, emoji_custom, emoji_unicode, role.id)
        sql_values = tuple(map(lambda x: str(x) if x is not None else x, tup_vals))
    except TypeError:
        raise TypeError('Type Error: Could not form query. Requires iterable')

    try:
        cursor = db.cursor()
        cursor.execute(sql_select, sql_values)
        row = cursor.fetchone()
        cursor.close()
        db.commit()
        return (emoji, role, row)
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

## DELETE ROW FROM TABLE ##
def del_manager(db, guild, role, obsolete=False):
    # try to validate Discord guild/role first
    try:
        guild = valid_guild(guild)
        if not obsolete:
            role = valid_role(guild, role)
            role_id = role.id
        else:
            try:
                role_id = int(role)
            except ValueError:
                return
    except:
        raise

    try:
        sql_call = 'CALL del_manager(%s, %s)'
        tup_vals = (guild.id, role_id)
        sql_values = tuple(map(lambda x: str(x) if x is not None else x, tup_vals))
    except TypeError:
        raise TypeError('Type Error: Could not form query. Requires iterable')

    try:
        cursor = db.cursor()
        cursor.execute(sql_call, sql_values)
        cursor.close()
        db.commit()
        return role or None
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

def del_channel(db, guild, channel, obsolete=False):
    # try to validate Discord guild/channel first
    try:
        guild = valid_guild(guild)
        if not obsolete:
            channel = valid_channel(guild, channel)
            channel_id = channel.id
        else:
            try:
                channel_id = int(channel)
            except ValueError:
                return
    except:
        raise

    try:
        sql_call = 'CALL del_channel(%s, %s)'
        tup_vals = (guild.id, channel_id)
        sql_values = tuple(map(lambda x: str(x) if x is not None else x, tup_vals))
    except TypeError:
        raise TypeError('Type Error: Could not form query. Requires iterable')

    try:
        cursor = db.cursor()
        cursor.execute(sql_call, sql_values)
        cursor.close()
        db.commit()
        return channel or None
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

def del_react_role(db, guild, emoji, role, obsolete=False):
    # try to validate Discord guild/user/emoji/role first
    try:
        guild = valid_guild(guild)
        if not obsolete:
            emoji = valid_emoji(guild, emoji)
            role = valid_role(guild, role)
            role_id = role.id
        else:
            try:
                emoji_custom = int(emoji)
                emoji_unicode = None
            except ValueError:
                emoji_custom = None
                emoji_unicode = emoji
            try:
                role_id = int(role)
            except ValueError:
                return
    except:
        raise

    if not obsolete:
        try:
            emoji_custom = int(emoji['id'])
            emoji_unicode = None
        except ValueError:
            emoji_custom = None
            emoji_unicode = emoji['id']

    try:
        sql_call = 'CALL del_react_role(%s, %s, %s, %s)'
        tup_vals = (guild.id, emoji_custom, emoji_unicode, role_id)
        sql_values = tuple(map(lambda x: str(x) if x is not None else x, tup_vals))
    except TypeError:
        raise TypeError('Type Error: Could not form query. Requires iterable')

    try:
        cursor = db.cursor()
        cursor.execute(sql_call, sql_values)
        cursor.close()
        db.commit()
        return (emoji, role) or None
    except pgdb.Error:
        try: cursor.close()
        except: pass
        raise Exception('DB Error: Could not execute query')

## DISCORD OBJECT VALIDATORS ##
def valid_guild(guild):
    try:
        guild.id
    except AttributeError:
        raise Exception('Could not find Discord guild')
    return guild

def valid_user(guild, user):
    try:
        guild = valid_guild(guild)
    except:
        raise
    try:
        user.id
    except AttributeError:
        # EXCEPTION: unknown user has no .id attribute
        try:
            user = guild.get_member(int(user))
        except ValueError:
            raise Exception('Could not find Discord user')
    return user

def valid_channel(guild, channel):
    try:
        guild = valid_guild(guild)
    except:
        raise
    try:
        channel.id
    except AttributeError:
        # EXCEPTION: unknown channel has no .id attribute
        try:
            channel = get(guild.channels, id=int(channel))
        except ValueError:
            # EXCEPTION: received a string instead of number
            channel = get(guild.channels, name=channel)
            try:
                channel.id
            except AttributeError:
                raise Exception('Could not find Discord channel')
    return channel

def valid_role(guild, role):
    try:
        guild = valid_guild(guild)
    except:
        raise    
    try:
        role.id
    except AttributeError:
        # EXCEPTION: unknown role has no .id attribute
        try:
            role = get(guild.roles, id=int(role))
        except ValueError:
            # EXCEPTION: received a string instead of number for int()
            role = get(guild.roles, name=role)
            try:
                role.id
            except AttributeError:
                raise Exception('Could not find Discord role')
    return role

def valid_emoji(guild, emoji):
    try:
        guild = valid_guild(guild)
    except:
        raise
    try:
        # try to validate emoji obj was passed
        emoji.id
        if emoji.id is not None:
            emoji_id = emoji.id
            alias = ':{}:'.format(emoji.name)
        # if partial emoji obj passed & not cust guild emoji, select only the name & further validate
        else:
            emoji = emoji.name
            raise AttributeError
    except AttributeError:
        # EXCEPTION: unknown emoji has no .id attribute
        try:
            # try to find custom guild emoji by id
            emoji = get(guild.emojis, id=int(emoji))
            emoji_id = emoji.id
            alias = ':{}:'.format(emoji.name)
        except ValueError:
            # EXCEPTION: received a unicode emoji or text for int()
            try:
                # try to split cust emoji string into int
                emoji = get(guild.emojis, id=int(emoji.split(':')[-1].split('>')[0]))
                emoji_id = emoji.id
                alias = ':{}:'.format(emoji.name)
            except ValueError:
                # EXCEPTION: received a unicode emoji or text for int()
                try:
                    # try to find unicode emoji by character (unicode symbol)
                    emoji_id = hex(ord(u'{}'.format(emoji)))
                    emoji = chr(int(emoji_id,16))
                    alias = emojis.demojize(emoji, use_aliases=True)
                except TypeError:
                # EXCEPTION: received a string instead of single char for ord()
                    try:
                        # try to find custom guild emoji by name
                        emoji = get(guild.emojis, name=emoji) or emoji
                        emoji_id = emoji.id
                        alias = ':{}:'.format(emoji.name)
                    except AttributeError:
                        # EXCEPTION: NoneType emoji has no .id attribute
                        try:
                            # try to convert hex id to unicode char
                            emoji = chr(int(emoji,16))
                            emoji_id = hex(ord(u'{}'.format(emoji)))
                            alias = emojis.demojize(emoji, use_aliases=True)
                        except ValueError:
                            # EXCEPTION: received some other text for int()
                            try:
                                # skip unicode emoji check if first char is alphanumeric, or more than 2 chars
                                if emoji[0].isalnum() or len(emoji) > 2:
                                    raise TypeError
                                # try again to find unicode emoji by first character only (unicode symbol)
                                emoji_id = hex(ord(u'{}'.format(emoji[0])))
                                emoji = chr(int(emoji_id,16))
                                alias = emojis.demojize(emoji, use_aliases=True)
                            except TypeError:
                                # skipped unicode symbol check
                                try:
                                    # try to find unicode emoji by alias
                                    emoji = emojis.emojize(':{}:'.format(emoji), use_aliases=True)
                                    emoji_id = hex(ord(u'{}'.format(emoji)))
                                    alias = emojis.demojize(emoji, use_aliases=True)
                                except TypeError:
                                    # EXCEPTION: received a string instead of single char for ord()
                                    raise Exception('Could not identify this emoji')
        except AttributeError:
            # EXCEPTION: NoneType emoji has no .id attribute
            # int was received, but emoji has been deleted
            raise Exception('This custom emoji has been removed')

    return {'id': emoji_id, 'print': emoji, 'alias': alias}

# walk through guild channels and send help message wherever available
async def find_help(guild, channel, member, emoji, role, add_role=True):
    try:
        guild = valid_guild(guild)
    except:
        raise
    # instantiate error msg & collect guild roles w/ admin privs
    msg = 'Error: AutoRoles is missing permissions, or reaction role is higher than AutoRoles. Please help '
    admin_roles = filter(lambda r: r.permissions.administrator == True, guild.roles)
    # append admin role mentions to msg
    for admin_role in admin_roles:
        msg += '{0} '.format(admin_role.mention)
    # provide context for specific role update failure
    if add_role:
        msg += '\n- {0} added {1} reaction and needs @{2} role'.format(member.mention, emoji, role)
    else:
        msg += '\n- {0} removed {1} reaction and doesn\'t need @{2} role'.format(member.mention, emoji, role)
    try:
        # try to post error to channel where role update failed
        await channel.send(msg)
        return
    except discord.errors.Forbidden:
        # EXCEPTION: bot does not have permission to post in this channel. include failure location in error msg
        msg += '\nReaction posted to {0} channel'.format(channel.mention)
        # loop through every channel, starting from the top (more likely to be admin channel), looking for text channels
        for x in range(0, len(guild.channels)):
            channel = get(guild.channels, position=x, type=discord.ChannelType.text)
            try:
                # try to post error message to a (hopefully admin) text channel
                await channel.send(msg)
                return
            except discord.errors.Forbidden:
                continue
        raise Exception('Could not post help message to admins')

# LOGGER #
def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(FORMATTER, DATE_FORMAT)
    console_handler.setFormatter(formatter)
    return console_handler
def get_file_handler(log_file):
    # file_handler = TimedRotatingFileHandler(log_file, when='midnight')
    # file_handler = logging.FileHandler(log_file)
    file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=6000000, backupCount=5)
    formatter = logging.Formatter(FORMATTER, DATE_FORMAT)
    file_handler.setFormatter(formatter)
    return file_handler
def get_logger(logger_name, log_file = None):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    if log_file is not None and len(logger.handlers) == 1:
        logger.addHandler(get_file_handler(log_file))
    if not len(logger.handlers):
        logger.addHandler(get_console_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger

# MYSQL CONNECTION #
def db_connect():
    url = urlparse(DB_URL)
    connection = pgdb.connect(
        host = url.netloc.split('@')[1].split(':')[0],
        user = url.username,
        password = url.password,
        database = url.path.split('/')[1]
    )
    return connection

async def on_error():
    print('probolo')