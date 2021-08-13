from os import name
from discord.client import Client
from discord.ext import commands, tasks
from discord.utils import get
import discord
import time
from db import DB


class Player():

    def __init__(self, id, discord, X, Z, nick):
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
        self.download_players()
        

    async def on_ready(self):

        self.server = self.get_guild(id=self.server_id)
        self.category = get(self.server.categories, id=self.category_id)
        
        print('ready')


    @tasks.loop(second=100)
    async def set_new_players(self):
        data = self.db.get_all_data_from('players')

        # берётся информция из базы данных и обнавляются координаты всех игроков, 
        # в случае исли в базе данных появился новый игрок (зарегистрировался) он добавляется в массив игроков
        for player_index in range(len(data)):
            try:
                self.players[player_index]

            except IndexError:
                
                self.players.append(Player(
                    id      = data[player_index][0], 
                    discord = get(data[player_index][1]),
                ))


    def get_players_need_to_remove(self):
        players_to_remove = []
        for id in range(len(self.players)):
            players_to_remove.append[[self.players[id].discord]]
            others_id = self.db.get_all_data_from(f'{self.players[id]}')
            for other_id in others_id:
                players_to_remove[id].append(self.players[other_id].discord)
            
            

    # возвращает канал в котором собраннa хотябы четверть от всех игроков, находящихся в одной 
    # зоне, если такого канала нет, ничего не возвращает, в дальнейшем он будет создан
    def find_channel_to_remove(self, players):
        
        members_in_channels = 0
        members_need_to_remove = len(players) / 4


        for channel in self.server.channels:

            if str(channel.type) == 'voice':
                for member in channel.members:
                    for player in players:
                        if player.discord.name == member.name:
                            members_in_channels += 1

                if members_in_channels > members_need_to_remove:
                    return channel

    
    @tasks.loop(seconds=2)
    async def remove_in_all_places(self):
        await self.wait_until_ready()

        
        # чтобы не проверять одних и тех же игроков по несколько раз всe
        # уже проверенные игроки будут записываться сюда и пропускаться
        already_checked = []

        

        players_nearly_each_other = self.get_players_need_to_remove()
        
        for player in players_nearly_each_other:

            for pl in players_nearly_each_other:
                already_checked.append(pl)

            
            channel = self.find_channel_to_remove(players_nearly_each_other)
            
            # в случае если нет каналов с большим сосредоточением нужных игроков, то создаётся новый канал
            if channel == None:
                channel_name = players_nearly_each_other[0].get_cords

                channel = await self.server.create_voice_channel(name=f'{channel_name}', category=self.category)

            # перемещение игркоков в канал 
            for pl in players_nearly_each_other:
                await pl.discord.move_to(channel)




    def start_loop(self):
        self.loop.create_task(self.set_players_cords())
        self.loop.create_task(self.remove_in_all_places())


client = Bot()
client.start_loop()
client.run("Token")
