from os import name
from discord.client import Client
from discord.ext import commands, tasks
from discord.utils import get
import discord
import time
from db import DB


class Player():

    def __init__(self, id, discord):
        self.id = id
        self.discord = discord



class Bot(Client):

    db = DB('db.db')

    server_id = 0
    category_id = 0
    
    players = []


    def connect_to_db(self):
        self.db.connect()


    def __init__(self):
        super().__init__()

        self.connect_to_db()

    async def on_ready(self):

        self.server = self.get_guild(id=self.server_id)
        self.category = get(self.server.categories, id=self.category_id)
        
        print('ready')


    @tasks.loop(seconds=100)
    async def set_new_players(self):

        data = self.db.get_data_from('players')

        for player_index in range(len(data)):
            
            founded = False

            for player in self.players:

                if player.id == data[player_index][0]:
                    founded = True
                    break

            if not founded:
                self.players.append(Player(
                    id      = data[player_index][0], 
                    discord = self.get_discord_by_nick(data[player_index][1]),
                ))


    def get_discord_by_nick(self, nick):
        return get(nick)


    def get_groups_of_players(self):
        groups = []

            # в groups_data находиться набор массивов, каждый из которых представляет
            # из себя набор находящихся рядом друг с другом игроков, (игроки записаны по id)
        groups_data = DB.get_data_from("group_of_players")

        for index in range(len(groups_data)):

            groups.append([])
            group = groups_data[index]

            for player_id in group:
                groups[index].append(self.get_player_by_id(int(player_id)))


    def get_player_by_id(self, id):
        
        for player in self.players:
            if player.id == id:
                return player

        raise f"ERROR, cant find player with id {id}"


    # возвращает канал в котором собраннa хотябы четверть от всех игроков, находящихся в одной 
    # зоне, если такого канала нет, ничего не возвращает, в дальнейшем он будет создан
    def get_channel_to_remove(self, players, channel_name=None):
        
        members_in_channels = 0
        members_need_to_remove = len(players) / 4

        members_in_group = {}

        for channel in self.server.channels:

            if str(channel.type) == 'voice':

                for member in channel.members:
                    for player in players:
                        if player.discord.name == member.name:
                            members_in_channels += 1
            
            members_in_channels[channel] = members_in_channels

        highest_count_of_members = 0

        for count_of_members in members_in_channels:
            if count_of_members > highest_count_of_members:
                highest_count_of_members = count_of_members

        if highest_count_of_members == 0:
            return self.server.create_voice_channel(name=f'{channel_name}', category=self.category)

        for i in range(len(members_in_channels)):
            if members_in_channels[members_in_channels.keys()[i]] == highest_count_of_members:
                return members_in_channels.keys()[i]

    
    @tasks.loop(seconds=2)
    async def remove_players_in_channels(self):
        await self.wait_until_ready()

        groups_of_players = self.get_groups_of_players()
        
        for grop_of_players in groups_of_players:
            
            channel = self.get_channel_to_remove(grop_of_players)

            # перемещение игркоков в канал 
            for pl in grop_of_players:
                await pl.discord.move_to(channel)


    def start_loop(self):
        self.loop.create_task(self.remove_players_in_channels())
        self.loop.create_task(self.set_new_players())

client = Bot()
client.start_loop()
client.run("TOKEN")
