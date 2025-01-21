from minecraft.networking.connection import Connection
from minecraft.authentication import AuthenticationToken, Profile
from minecraft.networking.connection import Connection
from minecraft.networking.packets import clientbound
from minecraft.exceptions import LoginDisconnect
import time
import uuid
import json
import threading

def custom_excepthook(args):
    if issubclass(args.exc_type, Exception):
        pass

threading.excepthook = custom_excepthook


class CheckBan:
    
    def __init__(self, access_token, username, username_uuid):
        self.access_token = access_token
        self.auth_token = AuthenticationToken(username=username, access_token=self.access_token, client_token=uuid.uuid4().hex)
        self.auth_token.profile = Profile(id_=username_uuid, name=username)
        self.banned = None
        self.connection = Connection("alpha.hypixel.net", 25565, auth_token=self.auth_token, initial_version=47)
        self.connection.connect()

    def check_ban(self):
        @self.connection.listener(clientbound.login.DisconnectPacket, early=True)
        def login_disconnect(packet):
            data = json.loads(str(packet.json_data))

            if "Suspicious activity" in str(data):
                self.banned = f"[Permanently] Suspicious activity has been detected on your account. Ban ID: {data['extra'][6]['text'].strip()}"
            elif "temporarily banned" in str(data):
                self.banned = f"[{data['extra'][1]['text']}] {data['extra'][4]['text'].strip()} Ban ID: {data['extra'][8]['text'].strip()}"
            elif "You are permanently banned from this server!" in str(data):
                self.banned = f"[Permanently] {data['extra'][2]['text'].strip()} Ban ID: {data['extra'][6]['text'].strip()}"
            elif "The Hypixel Alpha server is currently closed!" in str(data):
                self.banned = "False"
            elif "Failed cloning your SkyBlock data" in str(data):
                self.banned = "False"
            else:
                self.banned = ''.join(item["text"] for item in data["extra"])

            return self.banned

        @self.connection.listener(clientbound.play.JoinGamePacket, early=True)
        def joined_server(packet):
            self.banned = "False"
            print("Joined server")

        c = 0

        while self.banned is None and c < 1000:
            time.sleep(0.01)
            c += 1

        self.connection.disconnect()

        return self.banned
