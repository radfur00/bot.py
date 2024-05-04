@bot.command(name='hello', help='Powitanie')
async def hello(ctx):
    await ctx.send('Cześć! Jestem botem.')

@bot.command(name='kurwa', help='wiadomo...')
async def kurwa(ctx):
    await ctx.send('Tak, sam spier...')

@bot.command(name='czas', help='Wyświetla czas.')
async def czas(ctx):
    # Pobieranie bieżącego czasu i formatowanie go w czytelny sposób
    now = datetime.now()
    time_string = now.strftime("%H:%M:%S")  # Formatowanie czasu (godzina:minuta:sekunda)
    await ctx.send(f'Aktualny czas: {time_string}')

@bot.command(name='data', help='Wyświetla datę.')
async def data(ctx):
    today = datetime.now()
    date_string = today.strftime("%d-%m-%Y")  # Format dd-mm-yyyy
    await ctx.send(f'Dzisiejsza data: {date_string}')

@bot.command(name='wyczysc', help='Czyści 100 wiadomości na danym kanale')
async def wyczysc(ctx, limit: int = 100):
    """
    Komenda usuwająca wiadomości z kanału.

    :param limit: Opcjonalny parametr określający limit liczby wiadomości do usunięcia (domyślnie 10).
    """
    try:
        # Sprawdź, czy bot ma uprawnienia do usuwania wiadomości
        if ctx.author.guild_permissions.manage_messages:
            # Usuń wiadomości
            await ctx.channel.purge(limit=limit + 1)
            # Wyślij potwierdzenie
            await ctx.send(f"Usunięto {limit} wiadomości z kanału.", delete_after=5)
        else:
            await ctx.send("Nie masz uprawnień do zarządzania wiadomościami.")
    except Exception as e:
        await ctx.send(f"Wystąpił błąd podczas usuwania wiadomości: {e}")
