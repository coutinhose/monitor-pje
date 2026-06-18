import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import schedule
import time
import os
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://pje1g.trf5.jus.br/pjeconsulta/ConsultaPublica/DetalheProcessoConsultaPublica/listView.seam?ca=24dc5811edf16972b2ee6e561a36a0811178ebde1719a18b"

ultimo_estado = {}

def consultar_processo():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        movimentos = soup.find_all("tr", class_=lambda x: x and "rich-table-row" in x)

        dados = []
        for mov in movimentos[:5]:
            colunas = mov.find_all("td")
            if colunas:
                linha = " | ".join(col.get_text(strip=True) for col in colunas)
                if linha.strip():
                    dados.append(linha)

        return dados if dados else ["Nenhum movimento encontrado"]
    except Exception as e:
        return [f"Erro ao consultar: {str(e)}"]

async def enviar_mensagem(texto):
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=texto)

def verificar_e_notificar(obrigatorio=False):
    global ultimo_estado
    dados = consultar_processo()
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    if obrigatorio:
        msg = f"📋 Consulta agendada — {agora}\n\n"
        msg += "\n".join(dados)
        asyncio.run(enviar_mensagem(msg))
    else:
        chave = "\n".join(dados)
        if chave != ultimo_estado.get("dados"):
            ultimo_estado["dados"] = chave
            msg = f"🔔 Atualização detectada — {agora}\n\n"
            msg += "\n".join(dados)
            asyncio.run(enviar_mensagem(msg))

def consulta_obrigatoria():
    verificar_e_notificar(obrigatorio=True)

def consulta_mudanca():
    verificar_e_notificar(obrigatorio=False)

schedule.every().day.at("08:00").do(consulta_obrigatoria)
schedule.every().day.at("12:00").do(consulta_obrigatoria)
schedule.every().day.at("14:00").do(consulta_obrigatoria)
schedule.every().day.at("18:00").do(consulta_obrigatoria)
schedule.every().day.at("19:00").do(consulta_obrigatoria)

schedule.every(30).minutes.do(consulta_mudanca)

print("Monitor iniciado...")
asyncio.run(enviar_mensagem("✅ Monitor PJe iniciado com sucesso!"))

while True:
    schedule.run_pending()
    time.sleep(60)
