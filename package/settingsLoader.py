'''
Created on Aug 20, 2017
This class imports a settings file from a txt file containing a json
dict with a token variable
@author: Alec Helyar
'''
import traceback

class Settings:
    '''
    classdocs
    '''
    
    def __init__(self, params):
        '''
        Constructor
        '''
        self.token = None
        self.api_key = None
        self.loadFile(params)
        
    def loadFile(self, filename):
        try:
            file = open(filename, 'r')
            self.token = file.readline()[:-1]
            print('[Token Loaded]', self.token)
            self.api_key = file.readline()
            print('[API Key Loaded]', self.api_key)
            file.close()
        except IOError:
            print("IOError found")
            traceback.print_exc()
        except:
            traceback.print_exc()
            
    def get_token(self):
        return self.token
    
    def get_api_key(self):
        return self.api_key