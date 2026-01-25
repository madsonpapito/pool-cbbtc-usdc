python tools/fetch_pool_data.py
python tools/update_history.py
python tools/dashboard_gen_v3.py


Sobre as taxas:

Taxas Pendentes (Unclaimed): Sim, estas estão 100% corretas e automáticas. O script lê diretamente do contrato inteligente quanto você tem disponível para sacar agora.
Taxas Já Coletadas (Collected): Atualmente, este valor é manual. Ele está fixo em $1.80 no arquivo config.json. Se você coletou mais taxas recentemente na Uniswap e não atualizou este arquivo, o total estará defasado.
Quer que eu automatize isso? Posso criar um script que varre o histórico da blockchain (Logs de Eventos) para somar tudo o que você já coletou automaticamente, eliminando a estática manual. Deseja que eu implemente isso?

config.json
Open
