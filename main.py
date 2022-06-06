import discord
from discord.ext import commands
import json
import datetime
from datetime import datetime, timedelta
import asyncio

with open("config.json", "r") as f:
    config = json.load(f)

bot = commands.Bot(command_prefix=config["prefix"], intents=discord.Intents.all())
bot.remove_command("help")

if config["use-jishaku"]:
    bot.load_extension("jishaku")


async def modlog(action, user: discord.Member, sender: discord.Member, reason):
    if config["mod-log"]:
        embed = discord.Embed(title="Moderation Log", description=f"A user was punished by {sender.mention}.",
                              color=0xA52EF5)
        embed.add_field(name="Action", value=action, inline=False)
        embed.add_field(name="User Punished", value=f"{user}", inline=False)
        embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
        embed.set_footer(text=f"Sent at {datetime.now()}")
        await bot.get_channel(981696853080965142).send(embed=embed)


@bot.event
async def on_member_join(member):
    if member.created_at > (datetime.now() - timedelta(days=config["alt-threshold-days"])):
        await member.kick(reason="This account is younger than the threshold you have configured.")
        if config["alt-kick-logging"]:
            embed = discord.Embed(
                description=f"""{member} has been flagged as an alternative account. They have been kicked 
                automatically.""",
                color=0xA52EF5)
            embed.set_author(name="Alt Flagged", icon_url=member.avatar_url)
            await bot.get_channel(config["log-channel"]).send(embed=embed)
        else:
            pass
    else:
        role = discord.utils.get(member.guild.roles, id=config["verified-role-id"])
        await member.add_roles(role)
        embed = discord.Embed(description=f"Welcome to {member.guild.name}!", color=0xA52EF5)
        embed.set_author(name=member.name, icon_url=member.avatar_url)
        embed.set_footer(text=f"{member.guild.name} now has {len(member.guild.members)} members.")
        await bot.get_channel(config["welcome-channel"]).send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="None provided."):
    try:
        embed2 = discord.Embed(description=f"You have been banned from {member.guild.name}.", color=0xA52EF5)
        embed2.add_field(name="Reason", value=f"```{reason}```")
        await member.send(embed=embed2)
    except discord.Forbidden:
        pass
    await member.ban(reason=reason)
    embed = discord.Embed(description=f"{member} has been banned.", color=0xA52EF5)
    embed.add_field(name="Reason", value=f"```{reason}```")
    await ctx.send(embed=embed)
    await modlog("Ban", member, ctx.author, reason)


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(description="You do not have permission to ban members.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="You did not specify a member to ban.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(description="That is not a valid member.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandInvokeError):
        embed = discord.Embed(description="That member is already banned.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="None provided."):
    try:
        embed2 = discord.Embed(description=f"You have been kicked from {member.guild.name}.", color=0xA52EF5)
        embed2.add_field(name="Reason", value=f"```{reason}```")
        await member.send(embed=embed2)
    except discord.Forbidden:
        pass
    await member.kick(reason=reason)
    embed = discord.Embed(description=f"{member} has been kicked.", color=0xA52EF5)
    embed.add_field(name="Reason", value=f"```{reason}```")
    await ctx.send(embed=embed)
    await modlog("Kick", member, ctx.author, reason)


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(description="You do not have permission to kick members.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="You did not specify a member to kick.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(description="That is not a valid member.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, time, *, reason="None provided."):
    if time[-1] == "d":
        time = int(time[:-1]) * 86400
    elif time[-1] == "h":
        time = int(time[:-1]) * 3600
    elif time[-1] == "m":
        time = int(time[:-1]) * 60
    muterole = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muterole:
        muterole = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muterole, send_messages=False)
        await member.add_roles(muterole)
        embed = discord.Embed(description=f"Muted {member}.", color=0xA52EF5)
        await ctx.send(embed=embed)
        await modlog("Mute", member, ctx.author, reason)
        await asyncio.sleep(time)
        await member.remove_roles(muterole)


@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(description="You do not have permission to mute members.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="You did not specify a member to mute.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(description="That is not a valid member.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandInvokeError):
        embed = discord.Embed(description="That member is already muted.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    muterole = discord.utils.get(ctx.guild.roles, name="Muted")
    await member.remove_roles(muterole)
    embed = discord.Embed(description=f"Unmuted {member}.", color=0xA52EF5)
    await ctx.send(embed=embed)


@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(description="You do not have permission to unmute members.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="You did not specify a member to unmute.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(description="That is not a valid member.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandInvokeError):
        embed = discord.Embed(description="That member is not muted.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int, channel: discord.TextChannel = None):
    if not channel:
        await ctx.channel.purge(limit=amount)
    else:
        await channel.purge(limit=amount)
    embed = discord.Embed(
        description=f"Purged {amount} message(s) from {channel.mention if channel else ctx.channel.mention}.",
        color=0xA52EF5)
    await ctx.send(embed=embed)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(description="You do not have permission to purge messages.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="You did not specify an amount of messages to purge.", color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            description="The amount of messages you have requested to purge does not appear to be a valid number.",
            color=0xA52EF5)
        embed.set_author(name="Error")
        await ctx.send(embed=embed)


bot.run(config["bot-token"])
