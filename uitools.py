import discord
from discord.ext import commands
from tools import embed_builder


class Confirm(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author == interaction.user:
            embed = discord.Embed(title="Hyväksytty!", color=0x00FF00)
            await interaction.message.edit("", embed=embed, view=None)
            self.value = True
            self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author == interaction.user:
            embed = discord.Embed(title="Peruutettu.", color=0xFF0000)
            await interaction.message.edit("", embed=embed, view=None)
            self.value = False
            self.stop()


# creates select menu from a list and assigns selected value as self.value. Mostly used for jobs
class SelectFromList(discord.ui.View):
    def __init__(self, ctx, builder_list):
        super().__init__(timeout=25)
        self.ctx = ctx
        self.builder_list = builder_list
        self.selectbuilder()
        self.values = None


    def selectbuilder(self):
        options = []
        for builder in self.builder_list:
            name, desc, emoji = builder
            if emoji == None:
                options.append(discord.SelectOption(label=name, description=desc, value=name)) #if there is no emoji dont add it
            else:
                options.append(discord.SelectOption(label=name, description=desc, emoji=emoji, value=name))
        dropmenu = SelectDrop(placeholder="Valitse biisi listasta", min_values=1, max_values=1, options=options)
        self.add_item(dropmenu)



class SelectDrop(discord.ui.Select):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    async def callback(self, interaction):
        if self.view.ctx.author == interaction.user:
            self.view.values = self.values
            self.view.stop()