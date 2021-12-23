from discord.ext import commands
from tools import embed_builder
from discord.commands import slash_command, Option
import discord
import youtube_dl
from requests import get
import uitools


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.queue = {}

        self.ydl_opts = {
            'format': 'bestaudio'
        }

        self.ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


    async def join_channel(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice == None:
            await ctx.author.voice.channel.connect()
            await ctx.send(f'joinattu kanavalle {ctx.author.voice.channel}')
        else:
            await voice.move_to(ctx.author.voice.channel)

    async def queue_maker(self, ctx):
        if ctx.guild.id in self.queue:
            pass
        else:
            self.queue[ctx.guild.id] = []


    async def now_playing(self, ctx):
        queue = self.queue[ctx.guild.id][0]
        em = await embed_builder(ctx, 'Nyt soi', queue['title'], image=queue['thumbnail'])
        await ctx.send(embed=em)


    async def player(self, ctx, url):
        ctx.voice_client.stop()
        vc = ctx.voice_client
        source = await discord.FFmpegOpusAudio.from_probe(url, **self.ffmpeg_opts)
        vc.play(source, after=lambda error: self.bot.loop.create_task(self.play_from_queue(ctx)))


    async def play_from_queue(self, ctx):
        ctx.voice_client.stop()
        if len(self.queue[ctx.guild.id]) > 0:
            print(self.queue[ctx.guild.id])
            await self.player(ctx, self.queue[ctx.guild.id][0]['source'])
            await self.now_playing(ctx)
            self.queue[ctx.guild.id].pop(0)


    async def song_data(self, terms):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            data = ydl.extract_info('ytsearch:%s' % terms, download=False)#['entries'][0]
            print(data)


            if 'entries' in data and data['entries'] != []:
                info = data['entries'][0]
            else:
                # i need to figure out how to work with playlists
                print("type is playlist")
            
               
        return {'source': info['formats'][0]['url'], 'title': info['title'], 'thumbnail': info['thumbnail'], 'video_url': info['webpage_url']}

    async def clear_queue(self, ctx):
        self.queue[ctx.guild.id] = []

    async def channel_check(self, ctx):
        if ctx.voice_client is None:
            await ctx.send('En soita mitään tällä hetkellä')
            return False
        
        if ctx.author.voice is None:
            await ctx.send('Et ole äänikanavalla bruhh')
            return False

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            await ctx.send('Et ole samalla kanavalla kuin botti')
            return False

        return True


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None:
            if len(before.channel.members) == 1 and self.bot.user == before.channel.members[0]: # if the bot is the only user left in a vc
                voice = discord.utils.get(self.bot.voice_clients, guild=member.guild)
                await voice.disconnect()
                self.queue[member.guild.id] = []


    @slash_command(description = 'Joinaa samalle ääni kanavalle jolla olet')
    async def join(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice == None:
            await ctx.author.voice.channel.connect()
            await ctx.respond(f'joinattu kanavalle {ctx.author.voice.channel}')
        else:
            await voice.move_to(ctx.author.voice.channel)


    @slash_command(description = 'Soittaa kappaleen youtubesta')
    async def play(self, ctx, *, terms: Option(str, 'Hakutermit tai url')):
        if ctx.author.voice is None:
            await ctx.respond('Et ole äänikanavalla bruhh')
        else:
            await self.queue_maker(ctx)
            await ctx.respond('Kohta soi:D')
            data = await self.song_data(terms)
            if ctx.voice_client is not None:
                if len(self.queue[ctx.guild.id]) < 25:
                    self.queue[ctx.guild.id].append(data)
                    await ctx.respond(data['title'] + ' Lisätty jonoon')
            else:
                await self.join_channel(ctx)
                self.queue[ctx.guild.id].append(data)
                await self.player(ctx, terms)



    @slash_command(description = 'Skippaa tällä hetkellä soivan kappaleen')
    async def skip(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
            if len(self.queue[ctx.guild.id]) == 0:
                await ctx.respond('Queue on tyhjä')
            else:
                em = await embed_builder(ctx, 'Skipataanko??', ' ')
                view = uitools.Confirm(ctx)
                await ctx.respond(embed = em, view=view)
                await view.wait()
                if view.value == True:
                    await self.play_from_queue(ctx)
                else:
                    pass


    @slash_command(description = 'Pausettaa botin')
    async def pause(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
        
            ctx.voice_client.pause()
            await ctx.respond('Pausetettu')


    @slash_command(description = 'Jatkaa toistoa')
    async def resume(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
        
            ctx.voice_client.resume()
            await ctx.respond('Jatketaan toistoa')


    @slash_command(description = 'Lähtee pois kanavalta ja samalla tyhjentää jonon')
    async def leave(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
        
            await ctx.voice_client.disconnect()
            await ctx.respond('Lähetty pois')
            await self.clear_queue(ctx)


    @slash_command(description = 'Tyhjentää jonon')
    async def clear(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:

            await self.clear_queue(ctx)
            await ctx.respond('Jono tyhjennetty')


    @slash_command(description = 'Näyttää jonon')
    async def queue(self, ctx):
        n = 1
        fields = []
        for song in self.queue[ctx.guild.id]:
            fields.append([f'{n}) {song[1]}', song[3], False])
            n += 1 
        em = await embed_builder(ctx, 'Jono', ctx.guild, fields=fields)
        await ctx.respond(embed=em)


def setup(bot):
    bot.add_cog(Music(bot))
