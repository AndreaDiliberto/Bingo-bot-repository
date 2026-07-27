import os
import re
from threading import Thread
import discord
from flask import Flask

# --- TRUCCO PER RENDER FREE ---
app = Flask("")


@app.route("/")
def home():
    return "Bingo Bot è ONLINE!"


def run_web_server():
    # Render assegna una porta dinamica tramite la variabile PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# Avvia il server HTTP in un thread separato
Thread(target=run_web_server).start()
# ------------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def trova_prima_fila_bingo(sequenza):
    file = {i: set([i, i + 20, i + 40, i + 60, i + 80]) for i in range(1, 21)}
    numeri_usciti = set()

    for idx, num in enumerate(sequenza, start=1):
        numeri_usciti.add(num)
        for num_fila, fila_set in file.items():
            if fila_set.issubset(numeri_usciti):
                return num_fila, num, idx

    return None, None, None


@client.event
async def on_ready():
    print(f"Bot connesso con successo come: {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if "[" in message.content and "]" in message.content:
        try:
            estrazione = re.findall(r"\[(.*?)\]", message.content)
            if not estrazione:
                return

            sequenza = [
                int(n.strip())
                for n in estrazione[0].split(",")
                if n.strip().isdigit()
            ]

            if not sequenza:
                return

            fila_vincente, ultimo_numero, posizione = trova_prima_fila_bingo(
                sequenza
            )

            if fila_vincente:
                numeri_fila = [fila_vincente + 20 * k for k in range(5)]
                str_numeri = ", ".join(map(str, numeri_fila))

                risposta = (
                    f"🏆 **BINGO!** 🏆\n"
                    f"La prima fila a fare bingo è la **Fila {fila_vincente}** ({str_numeri}).\n"
                    f"È stata completata al **{posizione}° numero estratto** con l'uscita del numero **{ultimo_numero}**."
                )

                await message.channel.send(risposta)

        except Exception as e:
            print(f"Errore durante l'elaborazione del messaggio: {e}")


if __name__ == "__main__":
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print(
            "ERRORE: La variabile DISCORD_TOKEN non è stata trovata su Render!"
        )
