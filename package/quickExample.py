'''
Created on Aug 18, 2017
@author: Alec Helyar
@version: 2017.8.18
'''
import discord
from parse import parse
from random import randint
from package.player import Player

client = discord.Client()
player = Player(client)
dankString = "A vidya has been posted by {}! Give this message a \N{THUMBS UP SIGN} if dank or a \N{THUMBS DOWN SIGN} stank.\n**This vidya has a rating of {} dankness.**"

@client.event
async def on_member_update(before, after):
    if before.status == 'offline' and after.status != 'offline' and after.top_role.name == 'knight':
        msg = await client.send_message(after, "Hey {0.mention}! I noticed you just came online.  Alec's Rules is open for you.".format(after))
        print("Message sent: " + msg)

@client.event
async def on_member_join(member):
    server = member.server
    msg = 'Sup {0.mention}.  The rules are simple: No DND and no Maplestory talk.'
    await client.send_message(server, msg.format(member))
    await client.replace_roles(member, member.server.roles[2])
    
@client.event
async def on_reaction_remove(reaction, user):
    print("Reaction removed by " + user.name)
    if reaction.message.content.startswith('A vidya') and reaction.message.author == client.__getattr__('user'):
        if reaction.emoji.startswith('\N{THUMBS UP SIGN}'):
            res = parse(dankString, reaction.message.content)
            num = int(res[1]) - 1
            await client.edit_message(reaction.message, dankString.format(res[0], num))
        elif reaction.emoji.startswith('\N{THUMBS DOWN SIGN}'):
            res = parse(dankString, reaction.message.content)
            num = int(res[1]) + 1
            await client.edit_message(reaction.message, dankString.format(res[0], num))

@client.event
async def on_reaction_add(reaction, user):
    print("Reaction made by " + user.name)
    if reaction.message.content.startswith('A vidya') and reaction.message.author == client.__getattr__('user') and \
        (reaction.emoji.startswith('\N{THUMBS UP SIGN}') or reaction.emoji.startswith('\N{THUMBS DOWN SIGN}')):
        print("Reaction made on A vidya post")
        if "\n" not in reaction.message.content and reaction.emoji.startswith('\N{THUMBS UP SIGN}'):
            print(parse("A vidya has been posted by {0}! Give this message a \N{THUMBS UP SIGN} if dank or a \N{THUMBS DOWN SIGN} stank.", reaction.message.content)[0])
            await client.edit_message(reaction.message, dankString.format(parse("A vidya has been posted by {0}! Give this message a \N{THUMBS UP SIGN} if dank or a \N{THUMBS DOWN SIGN} stank.", reaction.message.content)[0], '1'))
        elif "\n" not in reaction.message.content and reaction.emoji.startswith('\N{THUMBS DOWN SIGN}'):
            await client.edit_message(reaction.message, dankString.format(parse("A vidya has been posted by {0}! Give this message a \N{THUMBS UP SIGN} if dank or a \N{THUMBS DOWN SIGN} stank.", reaction.message.content)[0], '-1'))
        else:
            res = parse(dankString, reaction.message.content)
            num = int(res[1])
            if reaction.emoji.startswith('\N{THUMBS UP SIGN}'):
                num += 1 
            else:
                num -= 1
            await client.edit_message(reaction.message, dankString.format(res[0], num))

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if ('maplestory' in message.content.lower() or 'dnd' in message.content.lower() or 'd&d' in message.content.lower()) and message.author.top_role != message.server.role_hierarchy[0]:
        await client.send_message(message.channel, "**RULES HAVE BEEN BROKEN BY " + message.author.name.upper() + "**", tts=True)
        prisonPermissions = message.server.default_role.permissions
        prisonPermissions.update(speak=False, send_messages=False, hoist=True)
        
        memRoles = message.author.top_role
        
        newRole = await client.create_role(message.author.server, name='Prison', permissions=prisonPermissions)
        await client.replace_roles(message.author, newRole)
        
        def check(msg):
            print(msg.author.top_role, msg.author.server.role_hierarchy)
            return msg.author.top_role >= msg.author.server.role_hierarchy[1]
        
        await client.send_message(message.channel, "{} has been sent to prison for ten minutes for violating a rule. A king or knight may release him with **!release.**".format(message.author.mention))
        release = await client.wait_for_message(timeout=600, content='!release', check=check)
        
        if release is not None:
            await client.send_message(message.channel, '***{} has been released by {}.***'.format(message.author.name, release.author.name))
        
        await client.replace_roles(message.author, memRoles)
        await client.delete_role(message.author.server, newRole)
        
    elif message.content.startswith('https://www.youtube'):
        await client.send_message(message.channel, "A vidya has been posted by {0}! Give this message a \N{THUMBS UP SIGN} if dank or a \N{THUMBS DOWN SIGN} stank.".format(message.author))
    elif message.content.startswith('!'):
        if message.content == '!help':
            await client.send_message(message.channel, "This is Alec Rules' custom bot.  Currently it is a WIP with few commands.  But there *is* a !roll MEMBER command for a chance to kick an online member")
            await client.delete_message(message);
        elif message.content.startswith('!roll'):
            name = parse('!roll {}', message.content)
            member = message.author.server.get_member_named(name[0])
            if member is not None and message.server.get_member(member.id) is not None and member.status != discord.Status.offline and member.top_role < message.server.role_hierarchy[0]:
                needed = randint(0, 500)
                roll = randint(0, 500)
                if needed == roll:
                    await client.kick(member)
                    await client.send_message(message.channel, "{} rolled the correct number: {}!  {} has been kicked".format(message.author.mention, roll, member.mention))
                else:
                    await client.send_message(message.channel, "{} rolled for a 1/500 chance to kick {}.  He needed a {} but rolled a {}.".format(message.author.mention, member.mention, needed, roll))
            elif member is not None and member.top_role.name == 'King':
                await client.send_message(message.channel, "Kings can't be rolled, silly.")
        elif message.content == '!pawn' and message.author.top_role == message.server.role_hierarchy[0]:
            for member in message.server.members:
                if member.top_role == message.server.default_role:
                    await client.replace_roles(member, message.server.role_hierarchy[2])
            await client.send_message(message.channel, 'All default users have been made pawns')
        elif message.content.startswith('!knight'):
            member = message.server.get_member_named(parse('!knight {a}', message.content)['a'])
            await client.replace_roles(member, message.server.role_hierarchy[1])
            await client.send_message(message.channel, '**{} has been knighted!**'.format(member.mention))
        elif message.content.startswith('!rules'):
            await client.send_message(message.channel, 'The rules are simple: no maplestory and no dnd talk.')
        elif message.content.startswith('!play'):
            if await player.getState() == Player.State.INACTIVE:
                await player.join_call(message.author.voice.voice_channel)
            url = parse('!play {a}', message.content)['a']
            await player.queue(url)
        elif message.content.startswith('!resume'):
            if await player.getState() == Player.State.PAUSED:
                await player.play()
        elif message.content.startswith('!pause'):
            await player.pause()
        elif message.content.startswith('!stop'):
            await player.leave_call()
        elif message.content.startswith('!ready'):
            await player.join_call(message.author.voice.voice_channel)
        elif message.content == '!skip':
            await player.skip()
        elif message.content.startswith("!volume"):
            string = parse('!volume {a}', message.content)['a']
            if string is not None:
                try:
                    volNum = int(string)
                    if volNum >= 0 and volNum <= 100:
                        await player.set_volume(float(volNum))
                except:
                    client.send_message(message.channel, 'Please follow !volume with an integer 0-100')
            else:
                await client.send_message(message.channel, 'The current volume setting is: {}'.format(player.volume))

client.run('MzQ4MjIyODQ2MzY0ODExMjY0.DHjzcg.gtOqSKMcgeAbdJJ9ZKgXCDhP9dA')