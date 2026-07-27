import os
import re
import discord

# Legge il Token direttamente dalle variabili d'ambiente di Render
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Inizializzazione del client Discord con i permessi per leggere i messaggi
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def trova_prima_fila_bingo(sequenza):
    """Calcola quale fila (1-20) fa prima bingo (completa tutti e 5 i suoi numeri)."""
    # Ogni fila i (da 1 a 20) contiene i numeri: i, i+20, i+40, i+60, i+80
    file = {i: set([i, i + 20, i + 40, i + 60, i + 80]) for i in range(1, 21)}

    numeri_usciti = set()

    for idx, num in enumerate(sequenza, start=1):
        numeri_usciti.add(num)

        # Controlliamo se una delle 20 file è stata completamente estratta
        for num_fila, fila_set in file.items():
            if fila_set.issubset(numeri_usciti):
                return num_fila, num, idx

    return None, None, None


@client.event
async def on_ready():
    print(f"Bot connesso con successo come: {client.user}")


@client.event
async def on_message(message):
    # Ignora i messaggi inviati da se stesso per evitare loop
    if message.author == client.user:
        return

    # Controlla se il messaggio contiene una sequenza racchiusa tra parentesi quadre [...]
    if "[" in message.content and "]" in message.content:
        try:
            # Estrae tutti i numeri presenti nel messaggio
            estrazione = re.findall(r"\[(.*?)\]", message.content)
            if not estrazione:
                return

            # Converte la stringa in una lista di interi
            sequenza = [
                int(n.strip())
                for n in estrazione[0].split(",")
                if n.strip().isdigit()
            ]

            if not sequenza:
                return

            # Calcola la prima fila vincente
            fila_vincente, ultimo_numero, posizione = trova_prima_fila_bingo(
                sequenza
            )

            if fila_vincente:
                # Costruisci i 5 numeri della fila vincente per chiarezza
                numeri_fila = [fila_vincente + 20 * k for k in range(5)]
                str_numeri = ", ".join(map(str, numeri_fila))

                risposta = (
                    f"🏆 **BINGO!** 🏆\n"
                    f"La prima fila a fare bingo è la **Fila {fila_vincente}** ({str_numeri}).\n"
                    f"È stata completata al **{posizione}° numero estratto** con l'uscita del numero **{ultimo_numero}**."
                )

                # Invia la risposta nel canale
                await message.channel.send(risposta)

        except Exception as e:
            print(f"Errore durante l'elaborazione del messaggio: {e}")


# Avvio del bot
if __name__ == "__main__":
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print(
            "ERRORE: La variabile DISCORD_TOKEN non è stata trovata su Render!"
        )
