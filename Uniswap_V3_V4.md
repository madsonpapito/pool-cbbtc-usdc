Diferenças entre Uniswap V3 e V4: Guia para o Agente
Olá, agente! Este documento explica as principais diferenças entre as versões V3 e V4 da Uniswap, com foco em pools de liquidez, arquitetura e impactos práticos. Além disso, incluo orientações sobre como adaptar nosso dashboard para rastrear (track) o desempenho de pools em ambas as versões. Baseado no estado atual em fevereiro de 2026, onde a V4 já está amplamente adotada, mas a V3 ainda domina em volume de liquidez acumulada.
O objetivo é ajudar você a monitorar métricas como TVL (Total Value Locked), volume de swaps, fees geradas, Impermanent Loss (IL) e APR para LPs (Liquidity Providers). Vamos usar ferramentas como subgraphs no The Graph, Dune Analytics e indexadores customizados.
1. Visão Geral das Diferenças
A Uniswap V3 (lançada em 2021) introduziu liquidez concentrada, permitindo que LPs coloquem liquidez em faixas de preço específicas. A V4 (lançada em 2025) mantém isso, mas adiciona customização extrema via "hooks" e uma arquitetura mais eficiente (singleton). Isso torna a V4 mais flexível, mas também mais complexa para rastreamento.
Tabela de Comparação Principal

| Característica | Uniswap V3 | Uniswap V4 | Impacto no Rastreamento |
| :--- | :--- | :--- | :--- |
| Arquitetura | Pools em contratos separados (um por par + fee tier) | Singleton: todos pools em um contrato (PoolManager) | V3: Fácil enumerar pools via factory. V4: Precisa indexar eventos de Initialize para descobrir pools. |
| Criação de Pools | Caro (deploy de novo contrato) | Barato (atualização de estado) | V4 facilita pools nichados, aumentando fragmentação de dados. |
| Customização | Limitada (fee tiers fixos: 0.01%, 0.05%, 0.3%, 1%) | Hooks: lógica customizada (fees dinâmicas, limit orders, etc.) | V4: Hooks complicam métricas (ex: fees variáveis exigem simulação). |
| Fees | Fixas por pool | Dinâmicas (ajustáveis via hooks) | V3: Simples cálculo. V4: Precisa parsear hooks para fees reais. |
| Eficiência de Gas | Mais alto para multi-hop | Flash accounting: mais eficiente | V4: Eventos agregados, difícil decompor por pool. |
| Identificação de Pools | Endereço único do contrato | PoolId (hash de params: tokens, fee, tickSpacing, hooks) | V4: Sem lista on-chain; use eventos para discovery. |
| Suporte a ETH Nativo | Não (usa WETH) | Sim | Menos impacto no tracking, mas swaps mais rápidos na V4. |
| Fragmentação de Liquidez | Poucos pools por par (por fee tier) | Ilimitados (múltiplos com hooks diferentes) | V4: TVL e volume espalhados; dashboard precisa agregar. |

Resumo Rápido:

V3: Simples, padronizada, boa para dashboards genéricos. Foco em liquidez concentrada e fees fixas.
V4: Extensível e eficiente, mas fragmentada. Ideal para inovações (ex: pools com KYC, auto-rebalance), mas exige mais engenharia para analytics.

Em 2026, ~70% do volume total da Uniswap está na V3 (por inércia), mas novos projetos migram para V4. Pools populares na V4 incluem aqueles com hooks como Bunni (para limit orders) ou Panoptic (opções).
2. Por Que Rastrear V4 é Mais Difícil que V3?

V3: Pools têm endereços fixos. Eventos (Swap, Mint, Burn) são emitidos por pool. Subgraphs prontos (ex: uniswap-v3 subgraph no The Graph) capturam tudo facilmente.
V4: Tudo centralizado no PoolManager. Pools não têm endereços; são estados internos. Hooks adicionam lógica arbitrária (ex: fees que mudam por volatilidade). Eventos são genéricos, e flash accounting agrega transações, complicando o tracing.

Resultados: Dashboards para V3 syncam rápido; para V4, subgraphs demoram mais e quebram com hooks customizados.
3. Como Adaptar o Dashboard para Rastrear Ambas as Versões
Para rastrear V3 e V4 no mesmo dashboard, use uma abordagem híbrida: subgraphs dedicados + indexadores customizados + queries on-chain. Foque em métricas chave: TVL, volume diário, fees acumuladas, posições ativas e IL estimado.
Passos Gerais para Implementação

Escolha Ferramentas de Indexação:
The Graph: Subgraphs oficiais para V3 (ex: uniswap/uniswap-v3). Para V4, use uniswap/uniswap-v4 (disponível desde 2025), mas customize para hooks.
Dune Analytics: Queries SQL prontas para V3 (ex: dune.com/uniswap). Para V4, crie spells customizadas usando ethereum.logs para eventos do PoolManager.
Subsquid ou Goldsky: Mais flexíveis para V4; suportam parsing de hooks via SDKs.
RPC Providers (Alchemy/Infura): Para queries on-chain reais (ex: ler estado via extsload na V4).

Rastreamento Específico para V3:
Descoberta de Pools: Query a factory V3 (endereço: 0x1F98431c8aD98523631AE4a59f267346ea31F984) para eventos PoolCreated.
Métricas:
TVL: Some liquidez em posições ativas (via NFTs ERC-721).
Volume/Fees: Soma eventos Swap por pool.
Exemplo de Query (The Graph):
```text
{
  pools(where: {id: "pool_address"}) {
    totalValueLockedUSD
    volumeUSD
    feesUSD
  }
}
```

Dashboard Integration: Use Grafana ou Superset para plotar gráficos. Sync diário é suficiente.

Rastreamento Específico para V4:
Descoberta de Pools: Indexe eventos `Initialize` do contrato Singleton (PoolManager). Diferente da V3, o identificador é o `PoolId` (hash do `PoolKey`), não um endereço de contrato.
Leitura de Estado: Utilize `StateView` contracts da periferia para ler `slot0` (preço) e liquidez. Evite ler storage slots diretamente a menos que necessário, pois o layout é otimizado e complexo.
Tratando Hooks:
Hooks "Vanilla": Pools sem hooks (address(0)) ou hooks simples comportam-se de forma previsível.
Hooks Dinâmicos: Para pools com taxas dinâmicas ou Oracles, o valor das fees não é fixo. Acompanhe os campos de retorno nos eventos de `Swap` para capturar as taxas efetivamente cobradas.

Métricas:
TVL: Saldo de tokens no PoolManager atribuídos ao PoolId. Rastrear eventos `ModifyLiquidity`.
Volume: Parse de eventos `Swap` no PoolManager. Lembre-se que o Swap na V4 usa `int128` para amounts (negativo = entrada, positivo = saída).
Exemplo de Query (The Graph - Padrão V4):
```text
{
  pool(id: "pool_id_hash") {
    totalValueLockedUSD
    volumeUSD
    feesUSD
    hookAddress
  }
}
```

Desafios e Soluções:
Fragmentação: Agrupe pools por token pair (ex: todos ETH/USDC V4 somados).
Sync Lento: Use webhooks para updates reais-time via Alchemy.
Hooks Custom: Para novos hooks, monitore X/Twitter para announcements e adicione suporte manual.


Integração Híbrida V3 + V4 no Dashboard:
Agregação: Crie views unificadas (ex: "Total TVL ETH/USDC" = V3 + soma de todos V4 pools para o par).
Frontend: Use React/Vue com Chart.js para gráficos. Mostre tabs: "V3 Only", "V4 Only", "Combined".
Automação: Script Python (com web3.py) para pull diário de dados on-chain e push para DB (ex: PostgreSQL).
Exemplo Simples:
```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://rpc.endpoint'))
pool_manager = w3.eth.contract(address='pool_manager_addr', abi=POOL_MANAGER_ABI)
# Query estado de pool específico via PoolId
```

Custo: V4 queries usam mais gas; otimize com batching.
Testes: Comece com mainnet Ethereum, depois expanda para L2s (Optimism, Base) onde V4 é mais comum.


Dicas Finais

Priorize Pools Relevantes: Foque em top 50 pools por TVL (use DefiLlama para seed inicial).
Monitoramento: Configure alerts para novos pools V4 via eventos.
Recursos: Docs oficiais Uniswap (docs.uniswap.org), GitHub Uniswap V4 (github.com/Uniswap/v4-core). Para ajuda, pergunte no Discord da Uniswap ou contrate dev via Upwork.
Atualizações: Em 2026, ferramentas como Dune estão melhorando suporte V4; cheque mensalmente.

Se precisar de código exemplo mais detalhado ou ajustes, avise!
