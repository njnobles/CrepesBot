import discord
from mcstatus import MinecraftServer
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

        

class ChannelManager:
    def __init__(self):
        self.channels = {}
        self.dbx_manager = DropBoxManager()

    def add_server(self, channel, server):
        if channel not in self.channels:
            self.channels[channel] = Channel(channel)

        self.channels[channel].add_server(server)
        self.save()

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
        em = []
        if channel in self.channels:
            em = self.channels[channel].get_updated_status_embeds()
            if self.channels[channel].has_a_server_status_changed():
                self.save()
        return em

    def get_json(self):
        content = {}
        for channel in self.channels:
            watchlist = self.channels[channel].get_watchlist()
            if len(watchlist) > 0:
                content[channel.id] = self.channels[channel].get_watchlist()
        return json.dumps(content)

    def save(self):
        self.dbx_manager.upload("ServerWatchlist2.txt", self.get_json())

    async def load(self, bot):
        print(bot)
        try:
            raw_json = self.dbx_manager.download("ServerWatchlist2.txt")
            parsed_json = json.loads(raw_json)
            for channel_id in parsed_json:
                print(channel_id)
                channel = bot.get_channel(int(channel_id))
                print(channel)
                watchlist = parsed_json[channel_id]
                print(watchlist)
                self.channels[channel] = Channel(channel)
                for server in watchlist:
                    self.channels[channel].add_server(server["server"], server["online"])
        except Exception as e:
            print(e)

class Channel:
    def __init__(self, channel):
        self.channel = channel
        self.mc_server_list = []

    def add_server(self, server, online=False):
        if server not in self.mc_server_list:
            self.mc_server_list.append(ServerStatus(server, online))

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
            server_info = {"server": s.server, "online": s.online}
            watchlist.append(server_info)
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

    def has_a_server_status_changed(self):
        for server in self.mc_server_list:
            if server.is_online_status_changed():
                return True

class ServerStatus:
    def __init__(self, server, online=False):
        self.server = server
        self.online = online
        self.prev_online_state = False
        self.status = None
        self.prev_status = None

    def is_status_changed(self):
        online_change = self.is_online_status_changed()

        status_change = False
        if self.prev_status is None and self.status is not None:
            status_change = True
        elif self.prev_status is not None and self.status is not None:
            status_change = (self.prev_status.players.online != self.status.players.online)

        return (online_change or status_change)

    def is_online_status_changed(self):
        return (self.online != self.prev_online_state)

    def update_status(self):
        self.prev_online_state = self.online
        self.prev_status = self.status
        try:
            mc_server = MinecraftServer.lookup(self.server)
            self.status = mc_server.status()
            self.query = mc_server.query()
            self.online = True
        except:
            self.online = False
        
    def get_embed(self):
        if(self.online):
            color=0x00ff00
        else:
            color=0xff0000

        embed = discord.Embed(title=f'Minecraft Server: {self.server}', color=color)
        embed.set_thumbnail(url='https://i.imgur.com/lxtYZIR.gif')
        if(self.online):
            embed.add_field(name="Status", value="Online", inline=True)
            embed.add_field(name="Version", value=f"{self.query.software.version}", inline=True)
            embed.add_field(name="# Online", value=f"{self.status.players.online}", inline=False)
            if(self.status.players.online > 0):
                embed.add_field(name="Players Online", value="\n".join(self.query.players.names), inline=False)
        else:
            embed.add_field(name="Status", value="Offline", inline=False)
            embed.add_field(name="# Online", value=f"0", inline=True)

        return embed