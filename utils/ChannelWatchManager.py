import discord
from mcstatus import MinecraftServer
from aternosapi import AternosAPI
import dropbox
import os
import json

class DropBoxManager:
    def __init__(self):
        self.dbx = None
        self.connected = False
        access_token = os.environ.get('DROPBOX_TOKEN', None)
        if access_token is not None:
            try:
                self.dbx = dropbox.Dropbox(access_token)
                self.connected = True
            except Exception as e:
                print('Error accessing DropBox')
                print(e)

    def upload(self, filename, json_content):
        try:
            with open(filename, "w") as text_file:
                text_file.write(json_content)

            if self.connected:
                with open(filename, "rb") as file_contents:
                    self.dbx.files_upload(file_contents.read(), '/' + filename, mode=dropbox.files.WriteMode.overwrite)
        except Exception as e:
            print(e)

    def download(self, filename):
        try:
            if self.connected:
                self.dbx.files_download_to_file(filename, '/' + filename)
            data = ''
            with open(filename, 'r') as myfile:
                data = myfile.read()
            return data
        except Exception as e:
            print(e)
        return '{}'

class ChannelPayload:
    def __init__(self, watchlist, aternos):
        self.watchlist = watchlist
        self.aternos = aternos

class ChannelManager:
    def __init__(self):
        self.channels = {}
        self.dbx_manager = DropBoxManager()
        self.startup_aid = {}

    def add_server(self, channel, server):
        if channel not in self.channels:
            self.channels[channel] = Channel(channel)

        self.channels[channel].add_server(server)
        self.save()

    def set_aternos_server(self, channel, server):
        if channel not in self.channels:
            self.channels[channel] = Channel(channel)

        self.channels[channel].set_aternos_server(server)
        self.save()

    def get_aternos_server(self, channel):
        return self.channels[channel].get_aternos_server()

    def start_aternos_server(self, channel):
        self.channels[channel].start_aternos_server()

    def stop_aternos_server(self, channel):
        self.channels[channel].stop_aternos_server()

    def remove_server(self, channel, server):
        if channel in self.channels:
            self.channels[channel].remove_server(server)
            self.save()

    def get_watchlist(self, channel):
        watchlist = []
        if channel in self.channels:
            watchlist = self.channels[channel].get_watchlist()
        return watchlist

    def get_status_embeds(self, channel):
        if channel in self.channels:
            return self.channels[channel].get_status_embeds()
        return []

    def get_updated_status_embeds(self, channel):
        if channel in self.channels:
            return self.channels[channel].get_updated_status_embeds()
        return []

    def get_json(self):
        content = {}
        for channel in self.channels:
            watchlist = self.channels[channel].get_watchlist()
            aternos = self.channels[channel].get_aternos_server()
            if len(watchlist) > 0 or len(aternos) > 0:
                #content[channel.id] = self.channels[channel].get_watchlist()
                content[channel.id] = ChannelPayload(watchlist, aternos)
        return json.dumps(content)

    def save(self):
        self.dbx_manager.upload("ServerWatchlist3.txt", self.get_json())

    async def load(self, bot):
        print(bot)
        try:
            raw_json = self.dbx_manager.download("ServerWatchlist3.txt")
            parsed_json = json.loads(raw_json)
            for channel_id in parsed_json:
                print(channel_id)
                channel = bot.get_channel(int(channel_id))
                print(channel)
                watchlist = parsed_json[channel_id]['watchlist']
                print(watchlist)
                self.channels[channel] = Channel(channel)
                for server in watchlist:
                    self.channels[channel].add_server(server)
                aternos = parsed_json[channel_id]['aternos']
                print(aternos)
                self.channels[channel].set_aternos_server(aternos)
        except Exception as e:
            print(e)
        try:
            raw_json = self.dbx_manager.download("aternos.json")
            for channel in self.channels:
                self.channels[channel].set_aternos_api_info(json.loads(raw_json))
            self.startup_aid = json.loads(raw_json)
        except Exception as e:
            print(e)


class Channel:
    def __init__(self, channel):
        self.channel = channel
        self.mc_server_list = []
        self.aternos_server = ''
        self.aternos_api = None
        self.aternos_api_info = None

    def set_aternos_api_info(self, aternos_api_info):
        self.aternos_api_info = aternos_api_info

    def add_server(self, server):
        if server not in self.mc_server_list:
            self.mc_server_list.append(ServerStatus(server))
    
    def set_aternos_server(self, server):
        if aternos_api_info is not None:
            self.aternos_server = server
            api_info = aternos_api_info[aternos_server]
            self.aternos_api = AternosAPI(api_info['headers_cookie'], api_info['cookie'], api_info['asec'])

    def get_aternos_server(self):
        return self.aternos_server

    def start_aternos_server(self):
        if self.aternos_api is not None:
            self.aternos_api.StartServer()

    def stop_aternos_server(self):
        if self.aternos_api is not None:
            self.aternos_api.StopServer()

    def remove_server(self, server):
        server_to_remove = None
        for s_status in self.mc_server_list:
            if s_status.server == server:
                server_to_remove = s_status
                break

        if server_to_remove is not None:
            self.mc_server_list.remove(server_to_remove)

    def get_watchlist(self):
        watchlist = []
        for s in self.mc_server_list:
            watchlist.append(s.server)
        return watchlist

    def get_status_embeds(self):
        embeds = []
        for server in self.mc_server_list:
            server.update_status()
            em = server.get_embed()
            if em is not None:
                embeds.append(em)
        return embeds

    def get_updated_status_embeds(self):
        embeds = []
        for server in self.mc_server_list:
            server.update_status()
            if server.is_status_changed():
                em = server.get_embed()
                if em is not None:
                    embeds.append(em)
        return embeds


class ServerStatus:
    def __init__(self, server):
        self.server = server
        self.online = False
        self.prev_online_state = False
        self.status = None
        self.prev_status = None

    def is_status_changed(self):
        online_change = (self.online != self.prev_online_state)

        status_change = False
        if self.prev_status is None and self.status is not None:
            status_change = True
        elif self.prev_status is not None and self.status is not None:
            status_change = (self.prev_status.players.online != self.status.players.online)

        return (online_change or status_change)

    def update_status(self):
        self.prev_online_state = self.online
        self.prev_status = self.status
        aternos_on = False
        try:
            mc_server = MinecraftServer.lookup(self.server)
            if 'aternos' in self.server and mc_server.host != self.server:
                aternos_on = True
            self.status = mc_server.status()
            #self.query = mc_server.query()
            print('o: ' + self.status.players.online)
            print('m: ' + self.status.max)
            #if self.status.players.online > 0 and self.status.players.online < 50:
                #self.online = True
            #else:
                #self.online = False
        except:
            self.online = False
        if aternos_on:
            self.online = True
        
    def get_embed(self):
        if(self.online):
            color=0x00ff00
        else:
            color=0xff0000

        embed = discord.Embed(title=f'Minecraft Server: {self.server}', color=color)
        embed.set_thumbnail(url='https://i.imgur.com/lxtYZIR.gif')
        if(self.online):
            embed.add_field(name="Status", value="Online", inline=True)
            #embed.add_field(name="Version", value=f"{self.query.software.version}", inline=True)
            if self.status is not None and self.status.players is not None:
                embed.add_field(name="# Online", value=f"{self.status.players.online}", inline=False)
            #if(self.status.players.online > 0):
                #embed.add_field(name="Players Online", value="\n".join(self.query.players.names), inline=False)
        else:
            embed.add_field(name="Status", value="Offline", inline=False)
            embed.add_field(name="# Online", value=f"0", inline=True)

        return embed
