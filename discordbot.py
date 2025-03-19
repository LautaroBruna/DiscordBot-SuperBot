import discord
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import asyncio

# Configurar las opciones de Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Configurar el servicio de ChromeDriver utilizando webdriver_manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)


# Configurar los intents de Discord
intents = discord.Intents.default()
intents.message_content = True

# Inicializar el cliente de Discord
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Conectado como {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!player'):
        try:
            # Extraer el nombre de usuario del mensaje
            _, username = message.content.split(' ', 1)
            username_encoded = username.replace('#', '%23')

            # Construir la URL
            url = f'https://supervive.op.gg/players/{username_encoded}'

            # Inicializar WebDriver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(url)

            # Espera hasta que el elemento esté presente
            wait = WebDriverWait(driver, 5)
            selector_css = "#app > div.min-h-screen.flex.flex-col.bg-stone-50.dark\\:bg-stone-900 > main > div > div:nth-child(3) > div > div.md\\:col-span-2.flex.flex-col.gap-4 > div.flex.flex-col.gap-2.p-4.md\\:p-0"
            elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_css)))

            # Extrae y procesa el texto del elemento
            texto = elemento.text.split('\n')

            # Extraer el número de juegos, KDA y Placement
            num_games = texto[0].split('(')[1].split(')')[0]  # 100
            kda_trend = float(texto[1])  # 4.5
            placement_trend = float(texto[3])  # 4.8

            # Mapeo de tiers basado en placement
            placement_tiers = {
                (9, 10): "🥉 Bronce",
                (8, 9): "🥈 Plata",
                (7, 8): "🥇 Oro",
                (6, 7): "⬜ Platino",
                (5, 6): "🔷 Diamante",
                (3.51, 5): "👑 Master",
                (2.5, 3.51): "🔥 Granmaster",
                (1, 2.5): "🌟 Leyenda"
            }

            # Determinar el rango de Elo basado en el placement
            elo = "Sin clasificación"
            for (low, high), name in placement_tiers.items():
                if low <= placement_trend < high:
                    elo = name
                    break

            # Ajustar el Elo basado en el KDA
            kda_adjustments = {
                (0, 1.5): " ⏬ overated ⏬ ",
                (4, float('inf')): " ⏫ underated ⏫ ",
                (3, 4): " 1/2",
                (1.5, 3): " 3/4"
            }

            for (low, high), adjustment in kda_adjustments.items():
                if low <= kda_trend < high:
                    elo += adjustment
                    break

            # Formatea el mensaje personalizado con emojis
            mensaje = (
                f"🎮 **{username}** / En {num_games} games\n"
                "===================================\n"
                f"⚔️ Avg KDA: {kda_trend} / / 📊 Avg Placement: {placement_trend}\n"
                f"🏆 Elo estimado: {elo}"
            )

            # Envía el mensaje al canal de Discord
            await message.channel.send(mensaje)

        except Exception as e:
            print(f"Error: {e}")
            await message.channel.send(f"Hubo un error al intentar obtener los datos{e}, verifica las mayúsculas y minúsculas del nombre.")

        finally:
            # Asegúrate de cerrar el navegador
            driver.quit()
            
# Inicia el bot usando el bucle de eventos existente
async def main():
    token = 'tokenplaceholder' 
    await client.start(token)

# Ejecuta el bucle de eventos
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
