'''
Created on Aug 20, 2017
This class handles downloading traffic using ytdl.  Inspired by MusicBot.
@author: Alec Helyar
'''
from concurrent.futures import ThreadPoolExecutor
import youtube_dl
import traceback
import functools

ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': 'videos/%(id)s.%(ext)s',
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

class Downloader:
    '''
    Class handles a custom implementation of youtube_dl using future threadpools
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.thread_pool = ThreadPoolExecutor(max_workers = 5)
        self.unsafe_ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        self.safe_ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        self.safe_ytdl.params['ignoreerrors'] = True
        
    @property
    def ytdl(self):
        return self.safe_ytdl
    
    async def future_extract_info(self, loop, url, download=True):
        '''
        Function returns a future which can safely be fired.
        '''
        try:
            return await loop.run_in_executor(self.thread_pool, functools.partial(self.unsafe_ytdl.extract_info, url=url, download=download))
        except:
            return await loop.run_in_executor(self.thread_pool, functools.partial(self.safe_ytdl.extract_info, url=url, download=download))
            traceback.print_exc()