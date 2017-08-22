'''
Created on Aug 19, 2017
This module handles download collection of videos
@author: Alec Helyar
'''
import discord
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import package.downloader
import package.song
import package.playlist_loader
import os
import traceback
from json import loads
import urllib

class Player:
    '''
    This class downloads videos
    '''
    class State(Enum):
        INACTIVE = 0
        PLAYING = 1
        PAUSED = 2
        IDLE = 3
    
    # Youtube_dl option format
    

    def __init__(self, client: discord.Client, api_key: str):
        '''
        Constructor
        '''
        self.api_key = api_key
        self.playlist_loader = package.playlist_loader.Playlist_loader()
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.deque = deque()
        self.client = client
        self.state = self.State.INACTIVE
        self.voice = None
        self.volume = .25
        self.downloader = package.downloader.Downloader()
        self.loop = asyncio.get_event_loop()
        self.curr_player = None
        self.curr_song = None
        self.lock = asyncio.Lock()
        self.is_looping = False
        self.voice_client = None
        for lib in ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']:
            try:
                discord.opus.load_opus(lib)
                print("[Loaded opus lib]")
            except:
                if lib == 'libopus-0.x86.dll':
                    print('Opus failed to load!!!')
        
    def clear(self):
        self.deque.clear()
        
    def isEmpty(self):
        return not deque
    
    def getState(self):
        return self.state
    
    async def toggle_looping(self):
        self.is_looping = not self.is_looping
        return self.is_looping
    
    async def connect(self, channel):
        print("[Connecting] ", channel)
        if not self.voice_client:
            for _ in range(3):
                try:
                    self.voice_client = await self.client.join_voice_channel(channel)
                    self.state = self.State.IDLE
                    print("[Connected]", self.voice_client.channel, self.voice_client.user)
                    break
                except:
                    await self.disconnect()
                    asyncio.sleep(0.25)
                    print("[Connection failed]")
        print("Decided already connected")
                
            
    async def disconnect(self):
        print("[Disconnecting]")
        if self.voice_client:
            await self.voice_client.disconnect()
            print("[Disconnected]")
        else:
            for server in self.client.servers:
                for channel in server.channels:
                    print("Checked: ", server, channel, len(self.client.voice_clients))
                    if channel.type == discord.ChannelType.voice and \
                    self.client.user in channel.voice_members:
                        try:
                            await self.client.voice_client_in(server).disconnect()
                        except:
                            print("Disconnect error.")
    
    async def set_volume(self, vol: float):
        self.volume = vol / 100
        if self.curr_player:
            self.curr_player.volume = self.volume
            
    async def queue_song(self, url):
        s = await self.extract_song(url)
        self.deque.append(s)
        if self.state == self.State.IDLE:
            self.play()
        return s
        
    async def extract_song(self, url):
        song = package.song.Song(url, self.downloader, self.loop)
        await song.download()
        return song
        
    async def create_curr_player(self, filename):
        if self.voice_client:
            self.curr_player = self.voice_client.create_ffmpeg_player(
                filename, 
                before_options='-nostdin', 
                options='-vn -b:a 128k', 
                after=lambda: self.loop.call_soon_threadsafe(self.song_finished))
            self.curr_player.volume = self.volume
            self.curr_player.setDaemon(True)
            self.state = self.State.PLAYING
            self.curr_player.start()
            print("[Current player created]")
        else:
            print("Voice is disconnected")
        
    def song_finished(self):
        print("[Song finished]", self.curr_song.getTitle(), self.curr_player is None)
        if self.curr_player:
            self.curr_player.after = None
            self.stop_curr_player()
            repeat = False
            for song in self.deque:
                print(song, song.filename, song.title)
                if self.curr_song.get_filename() == song.get_filename():
                    repeat = True
            
            if self.is_looping:
                print('[Song re-added to loop]', self.curr_song.title, len(self.deque))
                self.deque.append(self.curr_song)
                    
            if not self.is_looping and not repeat and \
            not self.curr_song.in_playlist:
                for _ in range(40):
                    try:
                        os.unlink(self.curr_song.get_filename())
                        print('[File Deleted]', self.curr_song.get_filename())
                        break
                    except PermissionError:
                        traceback.print_exc()
                        asyncio.sleep(0.25)
            print('[Curr song wiped]')
            self.curr_song = None
        self.state = self.State.IDLE
        self.play()
        
    def play(self):
        print('[Play future created]')
        self.loop.create_task(self.future_play())
        
    def resume(self):
        if self.state == self.State.PAUSED and self.curr_player:
            print('[Player resumed]')
            self.curr_player.resume()
            self.state = self.State.PLAYING
        elif self.state == self.State.PAUSED:
            self.state = self.State.PLAYING
    
    async def future_play(self):
        print("[Future play called]")
        if self.state == self.State.PAUSED:
            return self.resume()
        elif self.state == self.State.INACTIVE:
            return
        
        with await self.lock:
            if self.state == self.State.IDLE:
                if self.deque.__len__() > 0:
                    song = self.deque.popleft()
                else:
                    return
                
                #just in case
                self.stop_curr_player()
                
                await self.create_curr_player(song.get_filename())
                self.curr_song = song
                print('[Current song]', song.getTitle())
        
    def stop_curr_player(self):
        print("[Current player stopping]")
        if self.curr_player:
            if self.state == self.State.PAUSED:
                self.resume()
                
            try:
                self.curr_player.stop()
            except:
                traceback.print_exc()
            
            self.curr_player = None
            self.state = self.State.INACTIVE
        else:
            print("[No current player found]")
            
    async def add_playlist_song(self, url, playlist_title):
        new_song = package.song.Song(url, self.downloader, self.loop)
        await new_song.download()
        try:
            old = new_song.get_filename()
            new_song.in_playlist = True
            new = new_song.get_filename()
            if old != new:
                os.rename(old, new)
                print('[File moved]', new)
            print("Duration: ", new_song.getDuration(), type(new_song.getDuration()))
            self.playlist_loader.add_song(
                playlist_title, url, new, new_song.getTitle(), 
                new_song.getDuration())
            return new_song.getTitle()
        except:
            traceback.print_exc()
            raise ValueError
        
    async def add_queue_to_playlist(self, playlist_title):
        async def quick_load(song):
            try:
                old = song.get_filename()
                song.in_playlist = True
                new = song.get_filename()
                if old != new:
                    os.rename(old, new)
                    print('[File moved]', new)
                self.playlist_loader.add_song(playlist_title, song.url, song.filename, song.title, song.duration)
            except:
                traceback.print_exc()
                asyncio.sleep(1)
                await quick_load(song)
        for song in self.deque:
            try:
                await quick_load(song)
            except:
                traceback.print_exc()
        await quick_load(self.curr_song)
            
            
    async def remove_playlist_song(self, url, playlist_title):
        return self.playlist_loader.remove_song(url, playlist_title)
    
    async def load_playlist(self, playlist_title):
        try:
            song_info = self.playlist_loader.get_playlist(playlist_title)
            print('[Playlist info received]')
            await self.validate_playlist(song_info)
            for file in song_info:
                song = package.song.Song(
                    file['url'], self.downloader, self.loop, 
                    playlist=True, is_downloaded=True, title=file['songtitle'], 
                    filename=file['filename'], duration=file['duration'])
                #await song.download()
                self.deque.append(song)
                
                if self.state == self.State.IDLE:
                    self.play()
                
            return len(song_info)
        except:
            traceback.print_exc()
            return None
    
    def get_playlist_info(self, playlist_title=None):
        return self.playlist_loader.get_playlist_info(playlist_title)
            
    def get_song(self):
        if self.curr_song:
            return self.curr_song.getTitle()
        else:
            return "nothing playing"
        
    def get_info(self):
        string = 'The current music player state is: **' + self.State(self.state).name + '**.'
        if self.curr_song:
            string += '\n The current song is: **{}**.'.format(self.curr_song.getTitle())
        string += '\nThere are **{}** songs queued for a total of **{}** seconds.'.format(
            len(self.deque), self.get_queue_duration())
        for song in self.deque:
            string += '\n    **{}** - **{}s**'.format(song.getTitle(), song.getDuration())
        return string
            
    async def search_youtube(self, keyword):
        url_additions = urllib.parse.urlencode(
            {'key':self.api_key, 'relevanceLanguage':'en', 'type':'video', 'part':'snippet', 
             'maxResults':'15', 'q':urllib.parse.quote_plus(keyword)})
        api_url = "https://www.googleapis.com/youtube/v3/search?" + url_additions
        print("[Searching]", api_url)
        return_array = []
        data = None
        
        async def load_data():
            try:
                response = loads(urllib.request.urlopen(api_url).read())
                return response
            except urllib.error.HTTPError:
                print("[Load request failed]")
                return None
        
        for i in range(25):
            data = await load_data()
            if data:
                break
            asyncio.sleep(0.25)
        
        if not data:
            print("[Loading failed]")
            raise ValueError
            
        sumX = 0
        for result in data['items']:
            if sumX == 5:
                break
            if result['snippet']['liveBroadcastContent'] == 'none':
                return_array.append({
                    "url":('https://www.youtube.com/watch?v=' + result['id']['videoId']), 
                    'title':result['snippet']['title']})
                sumX += 1
        return return_array
    
    async def validate_playlist(self, playlist_info):
        print("[Checking playlist]")
        for playlist_song in playlist_info:
            try:
                if not playlist_song['filename']:
                    new_song = package.song.Song(
                        playlist_song['url'], self.downloader, self.loop, 
                        playlist=True, song_id=playlist_song['songtitle'], 
                        duration=playlist_song['duration'])
                    await new_song.download()
                    print("[Playlist song fixed]", playlist_song['songtitle'])
            except:
                print("Error checking song", playlist_song['songtitle'])
                traceback.print_exc()
        print("[Playlist Checked]")
                
            
    def pause(self):
        if self.state == self.State.PLAYING and self.curr_player:
            self.state = self.State.PAUSED
            self.curr_player.pause()
            
    def get_queue_duration(self):
        sumX = 0
        for song in self.deque:
            sumX += song.getDuration()
        return sumX