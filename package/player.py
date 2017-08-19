'''
Created on Aug 19, 2017
This module handles download collection of videos
@author: Alec Helyar
'''
import asyncio
import discord
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

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
    

    def __init__(self, client: discord.Client):
        '''
        Constructor
        '''
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.deque = deque()
        self.client = client
        self.state = self.State.INACTIVE
        self.voice = None
        self.player = None
        self.volume = .5
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        
    def isEmpty(self):
        return not deque
    
    async def getState(self):
        return self.state
    
    async def set_volume(self, vol: float):
        self.volume = vol / 100
        if self.player:
            self.player.volume = self.volume
    
    async def join_call(self, channel: discord.Channel):
        self.voice = await self.client.join_voice_channel(channel)
        self.state = self.State.IDLE
        
    async def leave_call(self):
        if self.voice is not None:
            await self.voice.disconnect()
            self.state = self.State.INACTIVE
            self.player = None
            self.deque.clear()
            
    async def queue(self, url: str):
        self.deque.append(url)
        if self.state == self.State.IDLE:
            await self.play()
    
    async def play(self):
        if self.state == self.State.IDLE:
            try:
                self.player = await self.voice.create_ytdl_player(self.deque.popleft(), ytdl_options=self.ytdl_format_options, after=self.callNext)
                self.player.volume = self.volume
                self.state = self.State.PLAYING
                self.player.start()
            except discord.ClientException as e: 
                print("ClientException: {}".format(e))
        elif self.state == self.State.PAUSED:
            self.player.resume()
            self.state = self.State.PLAYING
            
    async def pause(self):
        if self.state == self.State.PLAYING and self.player is not None:
            self.player.pause()
            self.state = self.State.PAUSED
        elif self.player is None:
            print("Player is none")
            
    async def skip(self):
        if self.state == self.State.PLAYING and self.player is not None:
            self.player.stop()
            self.callNext()
            
    async def getInfo(self):
        #nothing done yet
        
            
    def callNext(self):
        if self.deque:
            try:
                createPlayer = self.voice.create_ytdl_player(self.deque.popleft(), ytdl_options=self.ytdl_format_options, after=self.callNext)
                future = asyncio.run_coroutine_threadsafe(createPlayer, self.client.loop)
                future.result()
                self.player.volume = self.volume
                self.player.start()
            except:
                pass
        else:
            self.state = self.State.IDLE