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
            await ctx.send(f"joinattu kanavalle {ctx.author.voice.channel}")
        else:
            await voice.move_to(ctx.author.voice.channel)

    async def queue_maker(self, ctx):
        if ctx.guild.id in self.queue:
            pass
        else:
            self.queue[ctx.guild.id] = []


    async def now_playing(self, ctx):
        queue = self.queue[ctx.guild.id][0]
        em = await embed_builder(ctx, "Nyt soi", queue[1], image=queue[2])
        await ctx.send(embed=em)


    async def player(self, ctx, url):
        ctx.voice_client.stop()
        vc = ctx.voice_client
        source = await discord.FFmpegOpusAudio.from_probe(url, **self.ffmpeg_opts)
        vc.play(source, after=lambda error: self.bot.loop.create_task(self.play_from_queue(ctx)))


    async def play_from_queue(self, ctx):
        ctx.voice_client.stop()
        if len(self.queue[ctx.guild.id]) > 0:
            await self.player(ctx, self.queue[ctx.guild.id][0][0])
            await self.now_playing(ctx)
            self.queue[ctx.guild.id].pop(0)


    async def song_data(self, terms):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            try:
                get(terms)
            except:
                video_data = await self.bot.loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch:{terms}", download=False)["entries"][0])
            else:
                video_data = await self.bot.loop.run_in_executor(None, lambda: ydl.extract_info(terms, download=False))
        data = {
            'channel': video_data['uploader'],
            'channel_url': video_data['uploader_url'],
            'title': video_data['title'],
            'description': video_data['description'],
            'video_url': video_data['webpage_url'],
            'duration': video_data['duration'], #in seconds
            'thumbnail': video_data['thumbnail'],
            'audio_source': video_data['formats'][0]['url'],
            'view_count': video_data['view_count'],
            'like_count': video_data['like_count'],
            'id': video_data['id'],
        }
        return data

    async def clear_queue(self, ctx):
        self.queue[ctx.guild.id] = []

    async def channel_check(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("En soita mitään tällä hetkellä")
            return False
        
        if ctx.author.voice is None:
            await ctx.send("Et ole äänikanavalla bruhh")
            return False

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            await ctx.send("Et ole samalla kanavalla kuin botti")
            return False

        return True


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None:
            if len(before.channel.members) == 1 and self.bot.user == before.channel.members[0]: # if the bot is the only user left in a vc
                voice = discord.utils.get(self.bot.voice_clients, guild=member.guild)
                await voice.disconnect()
                self.queue[member.guild.id] = []


    @slash_command(description = "Joinaa samalle ääni kanavalle jolla olet")
    async def join(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice == None:
            await ctx.author.voice.channel.connect()
            await ctx.respond(f"joinattu kanavalle {ctx.author.voice.channel}")
        else:
            await voice.move_to(ctx.author.voice.channel)


    @slash_command(description = "Soittaa kappaleen youtubesta")
    async def play(self, ctx, *, terms: Option(str, "Hakutermit tai url")):
        if ctx.author.voice is None:
            await ctx.respond("Et ole äänikanavalla bruhh")
        else:
            await self.queue_maker(ctx)
            await ctx.respond("Kohta soi:D")
            data = await self.song_data(terms)
            if ctx.voice_client is not None:
                if len(self.queue[ctx.guild.id]) < 25:
                    self.queue[ctx.guild.id].append([data["audio_source"], data['title'], data['thumbnail'], data["video_url"]])
                    await ctx.respond(data["title"] + " Lisätty jonoon")
            else:
                await self.join_channel(ctx)
                self.queue[ctx.guild.id].append([data["audio_source"], data['title'], data['thumbnail'], data["video_url"]])
                await self.player(ctx, terms)



    @slash_command(description = "Skippaa tällä hetkellä soivan kappaleen")
    async def skip(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
            if len(self.queue[ctx.guild.id]) == 0:
                await ctx.respond("Queue on tyhjä")
            else:
                em = await embed_builder(ctx, "Skipataanko??", " ")
                view = uitools.Confirm(ctx)
                await ctx.respond(embed = em, view=view)
                await view.wait()
                if view.value == True:
                    await self.play_from_queue(ctx)
                else:
                    pass


    @slash_command(description = "Pausettaa botin")
    async def pause(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
        
            ctx.voice_client.pause()
            await ctx.respond("Pausetettu")


    @slash_command(description = "Jatkaa toistoa")
    async def resume(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
        
            ctx.voice_client.resume()
            await ctx.respond("Jatketaan toistoa")


    @slash_command(description = "Lähtee pois kanavalta ja samalla tyhjentää jonon")
    async def leave(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:
        
            await ctx.voice_client.disconnect()
            await ctx.respond("Lähetty pois")
            await self.clear_queue(ctx)


    @slash_command(description = "Tyhjentää jonon")
    async def clear(self, ctx):
        check = await self.channel_check(ctx)
        if check == True:

            await self.clear_queue(ctx)
            await ctx.respond("Jono tyhjennetty")


    @slash_command(description = "Näyttää jonon")
    async def queue(self, ctx):
        n = 1
        fields = []
        for song in self.queue[ctx.guild.id]:
            fields.append([f"{n}) {song[1]}", song[3], False])
            n += 1 
        em = await embed_builder(ctx, "Jono", ctx.guild, fields=fields)
        await ctx.respond(embed=em)


def setup(bot):
    bot.add_cog(Music(bot))
