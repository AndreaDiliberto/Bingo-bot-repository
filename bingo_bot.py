import io
import json
import os
import re
from threading import Thread
import discord
from flask import Flask
import matplotlib

matplotlib.use("Agg")  # Per generare immagini senza interfaccia grafica
import matplotlib.pyplot as plt

# --- TRUCCO PER RENDER FREE ---
app = Flask("")


@app.route("/")
def home():
    return "Bingo Bot è ONLINE!"


def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


Thread(target=run_web_server).start()
# ------------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STATS_FILE = "stats.json"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def carica_statistiche():
    """Carica le statistiche dal file JSON se esiste."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento stats: {e}")
    return {"totale_partite": 0, "vittorie_file": {}, "posizioni": []}


def salva_statistiche(stats):
    """Salva le statistiche aggiornate nel file JSON."""
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=4)
    except Exception as e:
        print(f"Errore salvataggio stats: {e}")


def registra_vittoria(fila, posizione):
    """Aggiorna i dati statistici con la nuova vittoria."""
    stats = carica_statistiche()
    stats["totale_partite"] += 1

    str_fila = str(fila)
    stats["vittorie_file"][str_fila] = (
        stats["vittorie_file"].get(str_fila, 0) + 1
    )
    stats["posizioni"].append(posizione)

    salva_statistiche(stats)


def genera_grafico_vittorie(stats):
    """Genera un grafico a barre in memoria con le frequenze delle vittorie."""
    file_ids = list(range(1, 21))
    vittorie = [stats["vittorie_file"].get(str(i), 0) for i in file_ids]

    fig, ax = plt.subplots(figsize=(10, 5))

    # Stile grafico
    bars = ax.bar(
        [f"Fila {i}" for i in file_ids],
        vittorie,
        color="#5865F2",
        edgecolor="#4752C4",
    )
    ax.set_title(
        "Frequenza Vittorie per Fila nel Bingo",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_ylabel("Numero di Vittorie", fontsize=11)
    ax.set_xlabel("File (1-20)", fontsize=11)
    plt.xticks(rotation=45, ha="right")

    # Aggiungi i numeri sopra le barre
    for bar in bars:
        yval = bar.get_height()
        if yval > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                yval + 0.1,
                int(yval),
                ha="center",
                va="bottom",
                fontsize=9,
            )

    plt.tight_layout()

    # Salva il grafico in memoria senza scriverlo sul disco
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf


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

    # COMANDO STATISTICHE: !stats
    if message.content.strip().lower() == "!stats":
        stats = carica_statistiche()
        totale = stats["totale_partite"]

        if totale == 0:
            await message.channel.send(
                "📊 Non ci sono ancora dati registrati! Invia prima qualche sequenza di Bingo."
            )
            return

        # Trova la fila con più vittorie
        vittorie_map = stats["vittorie_file"]
        top_fila = max(
            vittorie_map, key=lambda k: vittorie_map[k], default=None
        )
        top_vittorie = vittorie_map.get(top_fila, 0) if top_fila else 0

        # Calcola media dei numeri uscite
        media_pos = sum(stats["posizioni"]) / len(stats["posizioni"])

        testo_stats = (
            f"📊 **STATISTICHE GENERALI BINGO** 📊\n"
            f"• **Partite registrate:** `{totale}`\n"
            f"• **Fila più vincente:** **Fila {top_fila}** ({top_vittorie} vittorie)\n"
            f"• **Media estrazioni per fare Bingo:** `{media_pos:.1f}° numero`\n"
        )

        # Genera il grafico ed invialo su Discord
        buf = genera_grafico_vittorie(stats)
        file_grafico = discord.File(buf, filename="statistiche_bingo.png")

        await message.channel.send(content=testo_stats, file=file_grafico)
        return

    # ELABORAZIONE SEQUENZE BINGO [...]
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
                # Salva i dati per le statistiche
                registra_vittoria(fila_vincente, posizione)

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
