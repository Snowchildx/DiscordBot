import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp as youtube_dl
import re
import asyncio

# Credenciales
SPOTIPY_CLIENT_ID = 'd6ea3f18bc27470ca907088b14a4a9cc'
SPOTIPY_CLIENT_SECRET = '6458cc9a8ef84e7db69328c8d8b6a98b'
TOKEN = 'MTI3MDg4MDQ5ODA3OTQ5ODM3Mw.GiIT0L.PVyKyNGLUDjxKpQzHr20KpAb9g_m-S8FtasGp8'

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuración de Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                           client_secret=SPOTIPY_CLIENT_SECRET))

# Configuración de yt-dlp
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
}
ffmpeg_opts = {
    'options': '-vn',
}

# Cola de reproducción
music_queue = []

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def chavis(ctx):
    await ctx.send('Chavis es un pedazo de mierda')

@bot.command()
async def chango(ctx):
    await ctx.send('Chavis es un pinche chango')

@bot.command()
async def señoras(ctx):
    await ctx.send('ARRIBA LAS SEÑORAS CASADAS, ABAJO LAS GORDDAAAASSSSSSSSSS')

@bot.command()
async def almaenamorada(ctx):
    await ctx.send('TENGO EL ALMA ENAMORADA NOMAS DE PENSAR CORAZOOON, DE SOÑARME NOCHE A NOCHE DUEÑO DE TU AMOOOOOR')

# Comando para buscar canciones en Spotify
@bot.command()
async def song(ctx, *, song_name):
    results = sp.search(q=song_name, limit=1, type='track')
    tracks = results['tracks']['items']
    if tracks:
        track = tracks[0]
        title = track['name']
        artist = track['artists'][0]['name']
        url = track['external_urls']['spotify']
        await ctx.send(f'Canción: {title}\nArtista: {artist}\nEnlace: {url}')
    else:
        await ctx.send('No se encontró la canción.')

# Comando para unirse a un canal de voz
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send('Necesitas estar en un canal de voz para usar este comando.')

# Comando para desconectarse del canal de voz
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send('No estoy conectado a un canal de voz.')

# Comando para reproducir música
@bot.command()
async def play(ctx, *, song_name):
    if not ctx.voice_client:
        await ctx.send('Primero únete a un canal de voz con el comando !join.')
        return

    # Buscar la canción en YouTube
    ydl = youtube_dl.YoutubeDL(ytdl_opts)
    try:
        info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
        if not info['entries']:
            await ctx.send('No se encontró la canción.')
            return

        url = info['entries'][0]['url']
        ctx.voice_client.stop()

        ctx.voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_opts), after=lambda e: check_queue(ctx))
        await ctx.send(f'Reproduciendo: {info["entries"][0]["title"]}')
    except Exception as e:
        await ctx.send(f'Ocurrió un error: {str(e)}')

def check_queue(ctx):
    if music_queue:
        next_song = music_queue.pop(0)
        ctx.voice_client.play(discord.FFmpegPCMAudio(next_song['url'], **ffmpeg_opts), after=lambda e: check_queue(ctx))
        asyncio.run_coroutine_threadsafe(ctx.send(f'Reproduciendo: {next_song["title"]}'), bot.loop)

# Comando para reproducir playlists de Spotify
@bot.command()
async def play_playlist(ctx, *, playlist_url):
    if not ctx.voice_client:
        await ctx.send('Primero únete a un canal de voz con el comando !join.')
        return

    # Extraer el playlist ID de la URL
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        await ctx.send('URL de playlist inválida.')
        return

    # Obtener las pistas de la playlist de Spotify
    try:
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        if not tracks:
            await ctx.send('No se encontraron pistas en la playlist.')
            return

        for track in tracks:
            song_name = track['track']['name'] + " " + track['track']['artists'][0]['name']
            ydl = youtube_dl.YoutubeDL(ytdl_opts)
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
            if not info['entries']:
                await ctx.send(f'No se encontró la canción: {song_name}')
                continue

            url = info['entries'][0]['url']
            music_queue.append({'url': url, 'title': info['entries'][0]['title']})

        if not ctx.voice_client.is_playing() and music_queue:
            next_song = music_queue.pop(0)
            ctx.voice_client.play(discord.FFmpegPCMAudio(next_song['url'], **ffmpeg_opts), after=lambda e: check_queue(ctx))
            await ctx.send(f'Reproduciendo: {next_song["title"]}')

    except spotipy.exceptions.SpotifyException as e:
        await ctx.send(f'Ocurrió un error con la API de Spotify: {str(e)}')
    except Exception as e:
        await ctx.send(f'Ocurrió un error: {str(e)}')

def extract_playlist_id(url):
    """
    Extrae el ID de la playlist de una URL de Spotify.
    """
    match = re.match(r'https://open.spotify.com/playlist/([^/?&#]+)', url)
    if match:
        return match.group(1)
    return None

bot.run(TOKEN)
