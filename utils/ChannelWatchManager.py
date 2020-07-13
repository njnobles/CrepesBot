import discord
from mcstatus import MinecraftServer
import dropbox
import os


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
                pass

    
    async def files(self):
        print('Checking files')
        if self.dbx is None:
            print('Dbx not defined...')
            return
        resp = self.dbx.files_list_folder('')
        print(resp)
        print('-------------------------------------')
        for entry in resp.entries:
            print(entry)

        print('-------------------------------------')
        try:
            self.dbx.files_download_to_file('ServerWatchlist.txt', '/ServerWatchlist.txt')
            print('downloaded')
        except Exception as e:
            print(e)

        # print('-------------------------------------')
        # try:
        #     self.dbx.files_download('ServerWatchlist.txt')
        # except Exception as e:
        #     print(e)

        # print('-------------------------------------')
        # try:
        #     self.dbx.files_download('./ServerWatchlist.txt')
        # except Exception as e:
        #     print(e)

        try:
            data = ''
            with open('ServerWatchlist.txt', 'r') as myfile:
                data = myfile.read()
            
            print(data)
        except:
            print('No file downloaded...')

        

class ChannelManager:
    def __init__(self):
        self.channels = {}
        print('creating DropBoxManager')
        self.dbx_manager = DropBoxManager()

    async def files(self):
        await self.dbx_manager.files()

    def add_server(self, channel, server):
        if channel not in self.channels:
            self.channels[channel] = Channel(channel)

        self.channels[channel].add_server(server)

    def remove_server(self, channel, server):
        if channel in self.channels:
            self.channels[channel].remove_server(server)

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


class Channel:
    def __init__(self, channel):
        self.channel = channel
        self.mc_server_list = []

    def add_server(self, server):
        if server not in self.mc_server_list:
            self.mc_server_list.append(ServerStatus(server))

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
            embed.add_field(name="Status", value="Online", inline=False)
            embed.add_field(name="# Online", value=f"{self.status.players.online}", inline=True)
            embed.add_field(name="Version", value=f"{self.query.software.version}", inline=True)
        else:
            embed.add_field(name="Status", value="Offline", inline=False)
            embed.add_field(name="# Online", value=f"0", inline=True)
            embed.add_field(name="Version", value=f"1.16.1", inline=True)

        return embed