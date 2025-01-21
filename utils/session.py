import requests
from workers.ui import *

retries = 5
class TLSSession:

    def __init__(self):
        
        self.session = requests.Session()

  
    def _exec_request(self, allow_redirects=False, timeout=None, verify=None,**kwargs):


        for _ in range(retries):

            try:

                response = self.session.request(**kwargs, allow_redirects=allow_redirects, timeout=timeout, verify=verify)

                return response
            
            except Exception as e:
                

                Logger.Log("REQUEST", f"Failed to execute request", Colors.red, exception = "failed to do request due to: " + str(e))

                continue

        return None
