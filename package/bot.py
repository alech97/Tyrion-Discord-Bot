'''
Created on Aug 18, 2017
@author: Alec Helyar
@version: 2017.8.18
'''
import sys
import os
sys.path.append(os.path.abspath('../'))

import discord
from parse import parse
from random import randint
import traceback
from package.player import Player
import package.settingsLoader

client = discord.Client()
settings = package.settingsLoader.Settings('config.txt')
player = Player(client, settings.get_api_key())
vote_factors = {'skip':(0.5, 1), 'volume':(0.51, 1), 'roll':(0.8, 3), 'pause':(0.3, 1), 'stop':(0.8, 1)}
chance = 600
summon_knights = True

@client.event
async def on_member_update(before, after):
    if before.status == discord.Status.offline and \
    after.status != discord.Status.offline and after.top_role.name.lower() == 'knight':
        if summon_knights and after.name != 'Tirion' and \
        after.nick != 'Tyrion' and after.name != 'AR-bot':
            await client.send_message(
                after, 
                "Hey {0.mention}! I noticed you've just came online.  Alec's Castle is open for you.".format(
                    after))
            print("[Autosummon] A message to a knight was sent: " + before.name)
    else:
        print("[Check] {} {} was checked from {} to {}".format(
            before.top_role.name, before.name, before.status, after.status, after.top_role.name))

@client.event
async def on_member_join(member):
    server = member.server
    msg = 'Sup {0.mention}.  The rules are simple: No DND and no Maplestory talk.'
    await client.send_message(server, msg.format(member))
    await client.replace_roles(member, member.server.roles[2])

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if ('maplestory' in message.content.lower() or \
        'dnd' in message.content.lower() or 'd&d' in message.content.lower()) and \
        message.author.top_role != message.server.role_hierarchy[0]:
        await rules_broken(message)
    elif message.content.startswith('!'):
        command = "command_" + message.content[1:].split()[0]
        if command in globals():
            print("[Command received]", command)
            await client.delete_message(message)
            await globals()[command](message)
        

async def command_help(message):
    """**!help** - get list of commands that are available"""
    string = "The following commands are available:"
    functions = []
    #Split up functions into multiple messages because discord doesn't 
    #like huge messages
    for value in globals():
        if callable(globals()[value]) and \
        globals()[value].__name__.startswith('command_'):
            functions.append(globals()[value])
    
    size = 1
    for func in functions:
        string += "\n" + func.__doc__
        size += 1
        if size == 10:
            await client.send_message(message.channel, string)
            size = 0
            string = ""
    
async def command_rules(message):
    """**!rules** - get the rules for this channel"""
    await client.send_message(
        message.channel, 'The rules are simple: no maplestory and no dnd talk.')
    
async def command_autosummon(message):
    """**!autosummon** - toggles autosummon messages for knights"""
    if message.author.top_role == message.server.role_hierarchy[0]:
        global summon_knights 
        summon_knights = not summon_knights
        await client.send_message(
            message.channel, 'Knights are ' + ('' if summon_knights else 'not ') + 'being summoned.')
    
async def command_roll(message):
    """**!roll person_name** - roll for a 1/(chance) chance to kick person_name"""
    name = parse('!roll {}', message.content)
    member = message.author.server.get_member_named(name[0])
    if member is not None and message.server.get_member(member.id) is not None and \
    member.status != discord.Status.offline and member.top_role < message.server.role_hierarchy[0]:
        global chance
        denom = randint(2, chance)
        needed = randint(1, denom)
        roll = randint(1, denom)
        if needed == roll:
            await client.kick(member)
            await client.send_message(
                message.channel, 
                "{} rolled the correct number: {}/{} [2 - {}]!  {} has been kicked".format(
                    message.author.mention, roll, denom, chance, member.mention))
        else:
            await client.send_message(
                message.channel,
                "{} rolled for a 1/{} [2 - {}] chance to kick {}.  He needed a {} but rolled a {}.".format(
                    message.author.mention, denom, chance, member.mention, needed, roll))
    elif member is not None and member.top_role.name == 'King':
        await client.send_message(message.channel, "Kings can't be rolled, silly.")
    
async def command_skip(message):
    """**!skip** - call a vote to skip current song"""
    pollStr = '{.mention} wants to skip the song **{}**.'.format(message.author, player.get_song())
    if player.getState() == Player.State.PLAYING or player.getState() == Player.State.PAUSED:
        if await create_poll(
            pollStr, 
            generate_num_required('skip', message.server), message.channel, message.author):
            player.song_finished()
            await client.send_message(
                message.channel, '{0.mention} has skipped the song.'.format(message.author))
            await client.send_message(message.channel, player.get_info())
    
async def command_clear(message):
    """**!clear** - clear this bot's most recent messages"""
    #TODO Change to purge
    print('[Clearing]')
    numCleared = 0
    async for msg in client.logs_from(message.channel, limit = 1000):
        if msg.author == client.user:
            await client.delete_message(msg)
            numCleared += 1
    print("[Finished Clearing]", numCleared)
            
async def command_chance(message):
    """**!chance int_between_2_100000000** - change !roll's chance value to int_between_2_100000000"""
    try:
        string = int(parse('!chance {a}', message.content)['a'])
    except:
        traceback.print_exc()
        await client.send_message(
            message.channel, 'This command should be formatted like: **!chance 2-10000000**.')
        
    if string in range(2, 100000000):
        pollStr = '{.mention} wants to chance the chance value to **{}**.'.format(
            message.author, string)
        if await create_poll(
            pollStr, generate_num_required(
                'roll', message.server), message.channel, message.author):
            chance = string
            await client.send_message(
                message.channel, 
                '{.mention} has changed the chance value to **{}**.'.format(
                    message.author, string))
            
async def command_summon(message):
    """**!summon knight_name** - send summon message to sir knight_name"""
    if message.author.top_role >= message.server.role_hierarchy[1]:
        knight = parse('!summon {a}', message.content)
        if knight:
            knight = message.server.get_member_named(knight['a'])
            if knight and knight.voice and \
            (knight.voice.voice_channel is None or \
             knight.voice.voice_channel.server not in client.servers):
                await client.send_message(
                    knight, "**{} has summoned you to the castle, Sir {}!**".format(
                        message.author.name, knight.name))
                print('[Summon sent]', knight.name)
            else:
                print('[Summon attempted]', knight, knight.voice)
    
async def command_roundtable(message):
    """**!roundtable** - send a round table request to disconnected knights"""
    if message.author.top_role.name.lower() == 'knight' or message.author.top_role.name.lower() == 'king':
        for member in message.server.members:
            if (member.top_role.name.lower() == 'knight' or member.top_role.name.lower() =='king') and \
            member.name != message.author.name and member.status != discord.Status.offline:
                if member.voice.voice_channel is not None:
                    if message.server == member.voice.voice_channel.server:
                        continue
                if member.name == client.user.name:
                    continue
                
                await client.send_message(
                    member, 
                    '**The King has summoned you to his table, Sir {}!**'.format(member.name))
                print('[Roundtable summoned] ', member.name)
    
async def command_music(message):
    """**!music** - retrieve the current music player's info"""
    await client.send_message(message.channel, player.get_info())
    
async def command_pawn(message):
    """**!pawn** - turn default players to pawns"""
    for member in message.server.members:
        if member.top_role == message.server.default_role:
            await client.replace_roles(member, message.server.role_hierarchy[2])
    await client.send_message(message.channel, 'All default users have been made pawns')
    
async def command_playlist(message):
    """**!playlist** - view saved playlists and their size
    **!playlist playlist_title** - add playlist playlist_title to queue
    **!playlist view playlist_title** - view the songs in playlist playlist_title
    **!playlist add/remove playlist_title youtube_url** - add or remove song youtube_url to playlist playlist_title
    **!playlist save playlist_title** - save all songs in the current queue to playlist playlist_title"""
    split = message.content.split(" ")
    if len(split) == 4:
        if split[1].lower() == 'add' or split[1].lower() == 'remove':
            try:
                if split[1].lower() == 'add':
                    s_title = await player.add_playlist_song(split[3], split[2])
                    await client.send_message(
                        message.channel, 
                        '{.mention} has added the song **{}** to **{}**.'.format(
                            message.author, s_title, split[2]))
                    return
                else:
                    s_title = await player.remove_playlist_song(split[3], split[2])
                    await client.send_message(
                        message.channel, 
                        '{.mention} has removed the song **{}** from **{}**.'.format(
                            message.author, s_title, split[2]))
                    return
            except:
                traceback.print_exc()
                print("[Playlist entry failed]", split)
    elif len(split) == 2:
        if player.getState() == player.State.INACTIVE and message.author.voice.voice_channel:
            await player.connect(message.author.voice.voice_channel)
        new_msg = await client.send_message(
            message.channel, 
            "{.mention} has added **{}** to the queue. Loading...".format(
                message.author, split[1]))
        result = await player.load_playlist(split[1])
        if result:
            await client.edit_message(
                new_msg, 
                "{.mention} has added **{}** songs found in **{}** to the queue. Loading...".format(
                    message.author, result, split[1]))
            return
    elif len(split) == 1:
        #!playlist called
        await client.send_message(message.channel, player.get_playlist_info())
        return
    elif len(split) == 3 and split[1] == 'view':
        #!playlist playlist_title called?
        await client.send_message(message.channel, player.get_playlist_info(split[2]))
        return
    elif len(split) == 3 and split[1] == 'save':
        await player.add_queue_to_playlist(split[2])
        await client.send_message(
            message.channel, 
            '{.mention} added the current queue to the playlist.\n'.format(message.author) + \
             player.get_playlist_info(split[2]))
        return
    print("[Invalid playlist command]", split)
    await client.send_message(
        message.channel, "**Invalid !playlist format. **\n" + command_playlist.__docs__)
        
async def command_pause(message):
    """**!pause** - vote to pause current song"""
    pollStr = '{.mention} wants to pause the song **{}**.'.format(
        message.author, player.get_song())
    if player.getState() == Player.State.PLAYING:
        if await create_poll(
            pollStr, generate_num_required(
                'pause', message.server), message.channel, message.author):
            player.pause()
            await client.send_message(
                message.channel, 
                '{0.mention} has paused the song.'.format(message.author))
        
async def command_stop(message):
    """**!stop** - vote to stop current song"""
    pollStr = '{.mention} wants to stop the music player.'.format(message.author)
    if player.getState() == Player.State.PLAYING or player.getState() == Player.State.IDLE:
        if await create_poll(
            pollStr, generate_num_required(
                'stop', message.server), message.channel, message.author):
            player.stop_curr_player()
            player.deque.clear()
            await player.disconnect()
            await client.send_message(
                message.channel, '{0.mention} has ended the music.'.format(message.author))
            
async def command_volume(message):
    """**!volume** - vote to change volume of music player"""
    string = parse('!volume {a}', message.content)
    if string is not None:
        try:
            volNum = int(string['a'])
            if volNum > 0 and volNum <= 50:
                pollStr = '{.mention} wants to set the volume to **{}%**.'.format(
                    message.author, volNum)
                if await create_poll(
                    pollStr, generate_num_required('volume', message.server), 
                    message.channel, message.author):
                    await client.send_message(
                        message.channel, 
                        '{.mention} has set the volume to **{}%**.'.format(message.author, volNum))
                    await player.set_volume(float(volNum))
        except:
            traceback.print_exc()
            await client.send_message(
                message.channel, 
                '{}, please follow !volume with an integer 1-50'.format(message.author.mention))
    else:
        await client.send_message(
            message.channel, 'The current volume setting is: {}'.format(player.volume))
    
async def rules_broken(message):
    """The rules have been broken"""
    await client.send_message(
        message.channel, 
        "**RULES HAVE BEEN BROKEN BY " + message.author.name.upper() + "**", 
        tts=True)
    prisonPermissions = message.server.default_role.permissions
    prisonPermissions.update(speak=False, send_messages=False, hoist=True)
    
    memRoles = message.author.top_role
    
    newRole = await client.create_role(
        message.author.server, name='Prison', permissions=prisonPermissions)
    await client.replace_roles(message.author, newRole)
    
    def check(msg):
        print(msg.author.top_role, msg.author.server.role_hierarchy)
        return msg.author.top_role >= msg.author.server.role_hierarchy[1]
    
    await client.send_message(
        message.channel, 
        "{} has been sent to prison for ten minutes for violating a rule. A king or knight may release him with **!release.**".format(
            message.author.mention))
    release = await client.wait_for_message(timeout=600, content='!release', check=check)
    
    if release is not None:
        await client.send_message(message.channel, 
                                  '***{} has been released by {}.***'.format(
                                      message.author.name, release.author.name))
    
    await client.replace_roles(message.author, memRoles)
    await client.delete_role(message.author.server, newRole)
    
async def command_knight(message):
    """**!knight pawn_name** - knights pawn_name, must be king"""
    if message.author.top_role == message.server.role_hierarchy[0]:
        member = message.server.get_member_named(parse('!knight {a}', message.content)['a'])
        await client.replace_roles(member, message.server.role_hierarchy[1])
        await client.send_message(message.channel, '**{} has been knighted!**'.format(member.mention))
    
async def command_play(message):
    """**!play youtube_url** - add youtube_url to music player queue"""
    try:
        url = parse('!play {a}', message.content)['a']
        print("[Play request seen]")
        if not url.startswith('https://www.youtube.com/watch?v='):
            return
        
        await player.connect(message.author.voice.voice_channel)
        song = await player.queue_song(url)
        await client.send_message(message.channel, 
                                  '{.mention} has added the song: **{}**.\n'.format(
                                      message.author, song.getTitle()) + player.get_info())
        return
    except:
        print("[Play Error Occurred in Bot]")
    await client.send_message(
        message.channel, 
        '{.mention} - An error occurred with your URL request'.format(
            message.author))
        
async def command_connect(message):
    """**!connect** - tell bot to connect to chat"""
    if not player.voice:
        await player.connect(message.author.voice.voice_channel)
        await client.send_message(
            message.channel, '{0.mention} has opened the music player.'.format(message.author))
        
async def command_resume(message):
    """**!resume** - resume music"""
    if player.getState() == Player.State.PAUSED:
        player.resume()
        await client.send_message(
            message.channel, '{0.mention} has resumed the song.'.format(message.author))
        
async def command_loop(message):
    """**!loop** - toggles loop, which re-adds song to queue when done"""
    resp = await player.toggle_looping()
    await client.send_message(
        message.channel, 
        "{.mention} has set looping to **{}**".format(message.author, resp))
        
async def command_search(message):
    """**!search keywords** - search youtube for keywords, respond with only number to play"""
    try:
        keyword = parse('!search {}', message.content)
        if keyword:
            keyword = keyword[0]
        search_results = await player.search_youtube(keyword)
        if not search_results:
            raise ValueError
        print('[Search results received]')
        message_string = 'Your search for **{}** returned these results: **'.format(keyword)
        for result_index in range(5):
            message_string += '\n    {} - {}'.format(
                result_index + 1, search_results[result_index]['title'])
        message_string += '\n**To play a result, respond with the number you want to play.'
        res_message = await client.send_message(message.channel, message_string)
        
        def check(msg):
            return msg.content.isdigit() and int(msg.content) >= 1 and int(msg.content) <= 5
        
        response = await client.wait_for_message(
            20, channel=message.channel, author=message.author, check=check)
        
        if response:
            await player.connect(message.author.voice.voice_channel)
            await client.delete_message(response)
            await client.delete_message(res_message)
            song = await player.queue_song(search_results[int(response.content) - 1]['url'])
            await client.send_message(
                message.channel, 
                '{.mention} has added the song: **{}**.\n'.format(
                    message.author, song.getTitle()) + player.get_info())
            return
        else:
            await client.delete_message(res_message)
        return
    except:
        traceback.print_exc()
    await client.send_message(
        message.channel, 
        "Invalid search. Search should be used like so: \n**!search** (anything here no parentheses)")
    
async def create_poll(pollStr: str, numRequired: int, channel, author):
    voted = [author]
    
    votes = 1 if author.top_role.name != 'King' else 100
    if numRequired:
        msg = await client.send_message(
            channel, pollStr + '\n**{}** yea votes are needed.  Vote with !yea or !nay'.format(
                numRequired - votes))
    else:
        msg = await client.send_message(
            channel, pollStr + '\n**0** votes were needed.  The vote is passed.')
        return True
    
    def vote_check(msg):
        return msg.content.startswith('!yea') or msg.content.startswith('!nay')
    
    while votes < numRequired:
        vote = await client.wait_for_message(timeout=60, channel=channel, check=vote_check)
        if vote and vote.author not in voted:
            voted.append(vote.author)
            if vote.content.startswith('!yea'):
                votes += 100 if vote.author.top_role.name == 'King' else 1
            else:
                votes -= 100 if vote.author.top_role.name == 'King' else 1
            await client.edit_message(
                msg, pollStr + '\n**{}** yea votes are needed.  Vote with !yea or !nay'.format(
                    numRequired - votes))
            await client.delete_message(vote)
        else:
            await client.edit_message(
                msg, pollStr + '\nThe vote expired after 1 minute with **{}** votes.'.format(
                    numRequired))
            print("[Vote concluded]", votes, numRequired)
            return False
    if votes >= numRequired:
        await client.edit_message(
            msg, pollStr + '\n**{}** votes were reached.  The vote is passed.'.format(
                numRequired))
        print("[Vote concluded]", votes, numRequired)
        return True
    return False

def generate_num_required(call, server):
    num = 0.0
    for channel in server.channels:
        num += len(channel.voice_members)
        for person in channel.voice_members:
            if person.name == 'AR-bot':
                num -= 1
    num *= vote_factors[call][0]
    rounded = round(num)
    if rounded < vote_factors[call][1]:
        rounded = vote_factors[call][1]
    print('[Vote generated]', num, rounded)
    return int(rounded)

client.run(settings.get_token())