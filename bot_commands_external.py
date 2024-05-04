import os
from datetime import datetime
import asyncio
import fnmatch
import win32security
import yt_dlp as youtube_dl

# Video zmienne
scanned_files = set()
error_files = set()
current_video_folder = None
# belka zmienne
monitoring_path = None  # Ścieżka do monitorowania
monitoring_enabled = False  # Stan monitoringu

known_files = {}  # Słownik przechowujący znane pliki i odpowiadające im wiadomości

# --- WYKRYWANIE KLATEK ---

@bot.command(name='start_video', help='Ustawia folder do skanowania czarnych klatek. Nazwę sciezki podaj w ""')
async def set_folder(ctx, folder_path: str):
    global current_video_folder, error_files, scanned_files
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        await ctx.send("Podana ścieżka nie istnieje lub nie jest katalogiem.")
        return
    if scan_videos.is_running():
        scan_videos.cancel()
        await ctx.send("Poprzednie skanowanie zostało zatrzymane.")
    current_video_folder = folder_path
    error_files.clear()  # Czyścimy zbiór błędów przy ustawianiu nowego folderu
    scanned_files.clear()  # Czyścimy zbiór przeskanowanych plików
    await ctx.send(f"Ścieżka do skanowanego folderu została ustawiona na: {current_video_folder}")
    scan_videos.start()  # Uruchamiamy zadanie po ustawieniu folderu

@bot.command(name='stop_video', help='Zatrzymuje skanowanie folderu.')
async def stop_scan(ctx):
    if scan_videos.is_running():
        scan_videos.cancel()
        await ctx.send("Skanowanie zatrzymane.")
    else:
        await ctx.send("Aktualnie skanowanie nie jest aktywne.")

@tasks.loop(seconds=60)
async def scan_videos():
    global current_video_folder, error_files, scanned_files
    channel_id = 1205875409804197928  # ID kanału, na który bot ma wysyłać wiadomości
    channel = bot.get_channel(channel_id)
    if not channel:
        print("Nie można znaleźć kanału. Sprawdź, czy ID kanału jest poprawne.")
        return

    video_folder = current_video_folder
    if not video_folder or not os.path.exists(video_folder):
        await channel.send("Podany folder nie istnieje lub nie został ustawiony. Proszę sprawdzić ścieżkę.")
        return
    if not os.path.isdir(video_folder):
        await channel.send("Podana ścieżka nie jest katalogiem.")
        return

    for root, dirs, files in os.walk(video_folder):
        for filename in files:
            if filename.endswith(".mpg"):
                file_path = os.path.join(root, filename)
                if file_path in scanned_files:
                    continue  # Pomijamy pliki, które już zostały przeskanowane bez błędów

                print(f"Znaleziono: {file_path}")
                command = [
                    'ffmpeg.exe',
                    '-i', file_path,
                    '-vf', 'blackdetect=d=0.1:pix_th=0.10',
                    '-an',
                    '-f', 'null',
                    '-',
                    '-vstats_file', 'stats.txt'  # Dodatkowa opcja, aby uzyskać szczegółowe statystyki
                ]

                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    scanned_files.add(file_path)
                    result_lines = stderr.decode().split('\n')
                    for line in result_lines:
                        if '[blackdetect @' in line:
                            print(f"Czarne klatki wykryte w {file_path}:\n{line}")
                else:
                    error_files.add(file_path)
                    print(f"Błąd podczas analizy pliku {file_path}:\n{stderr.decode()}")

# /--- WYKRYWANIE KLATEK ---/

# --- WYKRYWANIE BELEK ---
@tasks.loop(seconds=45)
async def monitor_folder():
    global known_files
    if monitoring_path and monitoring_enabled:
        # print(f'Skanowanie folderu: {monitoring_path}')
        for root, dirs, files in os.walk(monitoring_path):
            for file in files:
                if fnmatch.fnmatch(file.lower(), 'belka.*'):
                    full_path = os.path.join(root, file)
                    if full_path not in known_files:
                        try:
                            security_info = win32security.GetFileSecurity(full_path, win32security.OWNER_SECURITY_INFORMATION)
                            owner_sid = security_info.GetSecurityDescriptorOwner()
                            owner_name, owner_domain, _ = win32security.LookupAccountSid(None, owner_sid)
                            creation_time = datetime.fromtimestamp(os.path.getctime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
                            message_text = f'```css\n{full_path}\n```**Zlecil:** {owner_name}, **Data utworzenia:** {creation_time}'
                            channel = bot.get_channel(1229169424821653554)  # Zastąp ID kanału
                            # channel = bot.get_channel(1228251367500546149)  # kanał test
                            if channel:
                                sent_message = await channel.send(message_text)
                                known_files[full_path] = sent_message
                        except Exception as e:
                            print(f"Nie można uzyskać informacji o pliku {full_path}: {str(e)}")

                if fnmatch.fnmatch(file.lower(), 'ok.txt'):
                    ok_path = os.path.join(root, file)
                    ok_security_info = win32security.GetFileSecurity(ok_path, win32security.OWNER_SECURITY_INFORMATION)
                    ok_owner_sid = ok_security_info.GetSecurityDescriptorOwner()
                    ok_owner_name, _, _ = win32security.LookupAccountSid(None, ok_owner_sid)
                    ok_creation_time = datetime.fromtimestamp(os.path.getctime(ok_path)).strftime('%Y-%m-%d %H:%M:%S')

                    belka_folder = os.path.dirname(ok_path)
                    for belka_path, msg in known_files.items():
                        if os.path.dirname(belka_path) == belka_folder:
                            updated_message = (f"~~{msg.content.split('```css\n{full_path}\n```')[0]}~~\n"
                                               f"**Robi:** {ok_owner_name}, **Data utworzenia (ok):** {ok_creation_time}")
                            await msg.edit(content=updated_message)


@bot.command(name='belka_start', help='Uruchamia skanowanie belek. Podaj ścieżkę skanowania po komendzie.')
async def start_monitoring(ctx, path: str):
    global monitoring_path, monitoring_enabled, known_files
    print(f"Checking path: {path}")  # Diagnostic print
    print(f"Path exists: {os.path.exists(path)}")  # Diagnostic print
    if os.path.exists(path):
        monitoring_path = path
        monitoring_enabled = True
        known_files = {}  # Resetujemy znane pliki przy każdym nowym uruchomieniu monitoringu
        monitor_folder.start()
        await ctx.send(f'Rozpoczęto monitorowanie folderu: {path}')
    else:
        await ctx.send('Podana ścieżka jest nieprawidłowa.')

@bot.command(name='belka_stop', help='Zatrzymaj skanowanie belek')
async def stop_monitoring(ctx):
    global monitoring_enabled
    if monitoring_enabled:
        monitoring_enabled = False
        monitor_folder.stop()
        await ctx.send('Zatrzymano monitorowanie.')
    else:
        await ctx.send('Monitorowanie nie jest aktywne.')

# /--- WYKRYWANIE BELEK ---/

@bot.command(name='download', help='Pobierz z YT ale chuj jeszcze nie działa')
async def download(ctx, url: str):
    await ctx.send('jeszcze nie działa!!!')
    """Pobiera film z YouTube i zapisuje na dysku."""
    """ ydl_opts = {
        'format': 'bestaudio/best',  # Możesz zmienić na "best" dla najlepszej jakości wideo i audio
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Zmiana klucza postprocesora dla yt-dlp
            'preferredcodec': 'mp4',  # Ustawienie na mp3, zmień na 'mp4' dla wideo
            'preferredquality': '192',  # Jakość audio, dostępne opcje to '192' itp.
        }],
        'ffmpeg_location': 'C:\\FFmpeg\\bin',  # Aktualizuj ścieżkę zgodnie z lokalizacją ffmpeg w twoim systemie
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # Folder i format nazwy pliku
        'noplaylist': True,  # Jeśli chcesz pobrać tylko pojedyncze wideo, a nie całą playlistę
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await ctx.send("Rozpoczynam pobieranie filmu...")
            ydl.download([url])
            await ctx.send("Film został pobrany pomyślnie!")
        except Exception as e:
            await ctx.send(f"Wystąpił błąd: {str(e)}")
    """