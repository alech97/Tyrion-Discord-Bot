'''
Created on Aug 20, 2017
Playlist_loader will load a playlist if needed.
@author: Alec Helyar
'''
import json
import os
from random import sample

class Playlist_loader:
    
    def __init__(self):
        self.playlists = self.load_playlists()
        
    def load_playlists(self):
        file = open('playlists/playlists.txt')
        res =  json.load(file)
        file.close()
        return res
        
    def add_song(self, title, url, filename, song_title, duration: int):
        if title not in self.playlists:
            self.playlists[title] = [{'url':url, 'filename':filename, 'songtitle':song_title, 'duration':duration}]
        else:
            for song in self.playlists[title]:
                if song['songtitle'] == song_title:
                    print('[Song skipped from playlist]', song_title)
                    return
            self.playlists[title].append({'url':url,'filename':filename, 'songtitle':song_title, 'duration':duration})
            
        self.update()
        
    def remove_song(self, url, title):
        for i in self.playlists[title]:
            if i['url'] == url:
                filename = i['filename']
                song_title = i['songtitle']
                self.playlists[title].remove(i)
                try:
                    os.unlink(filename)
                except:
                    print("Error: file in use")
                print('[Playlist Video Deleted]', filename)
                if len(self.playlists[title]) == 0:
                    self.playlists.pop(title)
                    print('[Playlist Removed]', title)
                self.update()
                return song_title
        
    def update(self):
        file = open('playlists/playlists.txt', 'w')
        json.dump(self.playlists, file)
        file.close()
        print('[Playlist File Updated]')
        
    def get_playlist(self, playlist_title):
        if playlist_title in self.playlists:
            print('[Playlist found]', playlist_title, len(self.playlists[playlist_title]))
            return sample(self.playlists[playlist_title], len(self.playlists[playlist_title]))
        else:
            print('[Playlist not found]', playlist_title)
            return None
                
    
    def get_playlist_info(self, playlist_title=None):
        string = ""
        duration = 0
        
        if playlist_title:
            try:
                string += "**{}** has **{}** songs:".format(playlist_title, len(self.playlists[playlist_title]))
                for song in self.playlists[playlist_title]:
                    string += "\n     **{}**".format(song['songtitle'])
                    duration += song['duration']
                string += "\nPlaylist total duration: **{}** seconds".format(duration)
            except:
                print("[Playlist view error]", playlist_title)
                return "Playlist not found: '{}'".format(playlist_title)
        else:
            string += "The following playlists exist:"
            for key in self.playlists:
                string += "\n     **{}** has **{}** songs.".format(key, len(self.playlists[key]))
        return string