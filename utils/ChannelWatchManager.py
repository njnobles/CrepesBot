import discord
from mcstatus import MinecraftServer

class Channel:
    def __init__(self, channel):
        self.channel = channel
        self.mc_server_list = []

    def add_server(self, server):
        if server not in self.mc_server_list:
            self.mc_server_list.append(ServerStatus(server))

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

class ChannelManager:
    def __init__(self):
        self.channels = {}

    def add_server(self, channel, server):
        if channel not in self.channels:
            self.channels[channel] = Channel(channel)

        self.channels[channel].add_server(server)

    def get_status_embeds(self, channel):
        if channel in self.channels:
            return self.channels[channel].get_status_embeds()
        return []

    def get_updated_status_embeds(self, channel):
        if channel in self.channels:
            return self.channels[channel].get_updated_status_embeds()
        return []

class ServerStatus:
    def __init__(self, server):
        self.server = server
        self.online = False
        self.prev_online_state = False
        self.status = None
        self.prev_status = None

    def is_status_changed(self):
        print('status change:')
        print(self.online != self.prev_online_state)

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
            print(mc_server.host)
            print(mc_server.port)
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