'''
Created on Aug 20, 2017
This class handles a song object for a youtube video.
@author: Alec Helyar
'''
import traceback
import asyncio
import os

class Song:
    '''
    A song object
    '''

    def __init__(self, url, downloader, loop, playlist=False, is_downloaded=False, song_id=None, ext=None, filename=None, title=None, duration=None):
        '''
        Constructor
        '''
        self.url = url
        self.is_downloading = False
        self.downloader = downloader
        self.futures = []
        self.loop = loop
        self.id = song_id
        self.ext = ext
        self.in_playlist = playlist
        self.is_downloaded = is_downloaded
        self.filename = filename
        self.title = title
        self.duration = duration
        if title:
            self.title = title.encode('utf-8', 'namereplace').decode('utf-8')
        
    def get_future(self):
        future = asyncio.Future()
        if self.is_downloading:
            future.set_result(self)
        else:
            asyncio.ensure_future(self.download())
            self.futures.append(future)
        return future
    
    def callFutures(self):
        futures = self.futures
        self.futures = []
        for future in futures:
            if future.cancelled():
                continue
            
            try:
                future.set_result(self)
            except:
                traceback.print_exc()
        
    async def download(self):
        if self.is_downloading:
            return
        
        self.is_downloading = True
        await self.downloadFile()
        self.callFutures()
        self.is_downloading = False
        
    async def downloadFile(self):
        #Check if file exists already
        try:
            result = await self.downloader.future_extract_info(self.loop, self.url, download=False)
            self.title = result['title']
            self.duration = result['duration']
            self.id = result['id']
            self.ext = result['ext']
            print('[Checking for file]', self.id, self.ext, self.get_norm_filename(), self.get_playlist_filename())
            if os.path.exists(self.get_playlist_filename()):
                self.filename = self.get_playlist_filename()
                print('[File found]', self.filename)
                self.is_downloaded = True
                self.in_playlist = True
            elif os.path.exists(self.get_norm_filename()):
                if self.in_playlist:
                    try:
                        old = self.get_norm_filename()
                        new = self.get_playlist_filename()
                        os.rename(old, new)
                        print('[File moved]', new)
                    except:
                        traceback.print_exc()
                        raise ValueError
                else:
                    self.filename = self.get_norm_filename()
                    print('[File found]', self.filename)
                self.is_downloaded = True
        except:
            traceback.print_exc()
        
        if not self.is_downloaded:
            print("[Downloading] ", self.url)
            try:
                result = await self.downloader.future_extract_info(self.loop, self.url)
                self.duration = result['duration']
                self.title = result['title']
                self.id = result['id']
                self.ext = result['ext']
                print("[Download complete]", self.id, self.ext)
                self.is_downloaded = True
                if self.in_playlist:
                    try:
                        old = self.get_norm_filename()
                        new = self.get_playlist_filename()
                        os.rename(old, new)
                        print('[File moved]', new)
                    except:
                        traceback.print_exc()
                        raise ValueError
            except:
                print("Ytld was not able to download file")
                traceback.print_exc()
        
    def getDuration(self):
        if self.duration is not None:
            return self.duration
        else:
            print("getDuration called incorrectly")
            return
        
    def get_filename(self):
        try:
            if self.filename:
                return self.filename
            elif self.in_playlist:
                return self.get_playlist_filename()
            return self.get_norm_filename()
        except:
            print("[Filename not found for song]", self.title)
            self.get_future()
            self.callFutures()
    
    def get_playlist_filename(self):
        return "playlists/videos/" + self.id + "." + self.ext
    
    def get_norm_filename(self):
        return "videos/" + self.id + "." + self.ext
        
    def getTitle(self):
        return self.title.encode('utf-8', 'namereplace').decode('utf-8')