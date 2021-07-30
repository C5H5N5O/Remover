from os import name
from discord.client import Client
from discord.ext import commands, tasks
from discord.utils import get
import discord
import time
from db import DB


class Player():

    def __init__(self, id, discord, X, Z, nick='Ananas_klemente'):
        
        self.id = id
        self.discord = discord
        self.X_cord = X
        self.Z_cord = Z
        self.nick = nick

    def set_cords(self, X, Z):
        self.X_cord = X
        self.Z_cord = Z

    def get_cords(self):
        return self.X_cord, self.Z_cord



class Place():
    def __init__(self, x_cord_from, x_cord_to, y_cord_from, y_cord_to, name_channel):

        self.x_cord_from = x_cord_from
        self.x_cord_to   = x_cord_to
        self.y_cord_form = y_cord_from
        self.y_cord_to   = y_cord_to
        self.name_channel = name_channel

        self.players_in_place = []

    def set_player(self, players):
        self.players_in_place.append(players)

    def remove_player(self, player):
        self.players_in_place.pop(player)


class Bot(Client):

    db = DB('db.db')

    server_id = 0
    category_id = 0
    

    def download_players(self):
        self.players = []
        for row in self.db.get_all_data_from('players'):
            self.players.append(Player(
                id      = row[0], 
                discord = get(row[1]),
                X       = row[2],
                Z       = row[3],
                nick    = row[4]
            ))


    def connect_to_db(self):
        self.db.connect()


    def __init__(self):
        super().__init__()

        self.connect_to_db()
        self.download_players()
        #self.download_places()
        

    async def on_ready(self):

        self.server = self.get_guild(id=self.server_id)
        self.category = get(self.server.categories, id=self.category_id)
        
        print('ready')


    def set_players_cords_from_db(self):
        data = self.db.get_all_data_from('players')

        for i in range(len(data)):
            self.players[i].set_cords(data[i][2], data[i][3])


    # возвращает всех людей, находящихся недалеко от переданного игрока
    def find_players_nearly(self, main_player, players_nearly_each_other = [], already_checked=[], distance=50):
        
        if main_player not in already_checked:
            players_nearly_each_other.append(main_player)
            already_checked.append(main_player) 

        for player in self.players:
            if main_player != player:
                if player not in already_checked:
                    if main_player.get_cords()[0] - player.get_cords()[0] <= distance \
                        and main_player.get_cords()[1] - player.get_cords()[1] <= distance \
                    or player.get_cords()[0] - main_player.get_cords()[0] <= distance \
                        and player.get_cords()[1] - main_player.get_cords()[1] <= distance:
                            already_checked.append(player)
                            players_nearly_each_other.append(player)
                            self.find_players_nearly(player, players_nearly_each_other, already_checked)

        return players_nearly_each_other

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



    @tasks.loop(seconds=0.5)
    async def set_players_cords(self):
        await self.wait_until_ready()
        self.set_players_cords_from_db()


    
    @tasks.loop(seconds=1)
    async def remove_in_all_places(self):
        await self.wait_until_ready()

        
        # чтобы не проверять одних и тех же игроков по несколько раз все 
        # уже проверенные игроки будут записываться сюда и пропускаться
        already_checked = []

        for player in self.players:
            
            if player in already_checked: continue

            players_nearly_each_other = self.find_players_nearly(player)
            
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
