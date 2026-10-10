# Agente 100 + Robô 100 — V1

Protótipo **exclusivamente em simulação (paper trading)**. Nenhuma conexão com corretora ou operação real.

## Fluxo

Mercado + notícias → Agente 100 (escolhe oportunidade, direção, Take Profit e Stop Loss) → autorização explícita do usuário → Robô 100 (registra ordem fictícia com valor fixo programado no robô).

O Agente 100 não define tamanho de posição. O Robô 100 não analisa mercado. Dados da demonstração são sintéticos e o sentimento de notícias é informado manualmente, não coletado em tempo real.

## Executar localmente

Python 3.11+; sem dependências externas:

```bash
python -m unittest discover -s tests -v
python -m agente100.demo
```

**Importante:** A demonstração concede aprovação programática apenas para exemplificar o fluxo; em um produto interativo, a aprovação deve vir de uma ação explícita do usuário. A implementação atual apenas registra ordens abertas, sem fechamento, P&L, slippage ou custos. Não há garantia de retorno.

## Próximas etapas

Integrar dados verificáveis de preços e notícias; construir interface de autorização humana; implementar ciclo de vida de posições, risco e backtest; adicionar execução automática dos testes no GitHub Actions. Manter isolamento total de ordens reais.

## Aprovação interativa (simulação)

```bash
python -m agente100.cli
```

O terminal mostra um sinal baseado em dados sintéticos e exige digitar o ID exato antes de registrar a ordem fictícia. O arquivo `agente100/demo.py` continua sendo uma demonstração programática sem interação. O GitHub Actions em `.github/workflows/tests.yml` executa os testes a cada push/PR; verifique a aba **Actions** para conferir o resultado.

## Consultar mercado público (somente leitura)

```bash
python -m agente100.market_cli
```

Essa execução faz requisições HTTP públicas para candles de 15 minutos de BTC-USD, ETH-USD e SOL-USD da Coinbase Exchange, calcula RSI e rompimento de Bandas de Bollinger e apresenta **somente uma análise**. Não solicita autorização e **não executa nem simula uma ordem**. A fonte pode falhar ou bloquear requisições; a rotina relata indisponibilidade em vez de inventar preços. Sentimento de notícias ainda é neutro (0), pois não há coletor de notícias conectado. A estratégia e os indicadores são experimentais, não validados para investimentos.

## Pesquisa de mercado + notícias (somente leitura)

```bash
python -m agente100.research_cli
```

A rotina tenta consultar candles públicos da Coinbase Exchange e manchetes RSS públicas do CoinDesk. Calcula um sentimento **heurístico** por palavras-chave, por ativo, com manchetes datadas das últimas 24 horas. Na falha do feed, usa sentimento neutro e informa a indisponibilidade; não inventa notícias. Fontes podem mudar, ficar indisponíveis ou bloquear acesso. O código **não abre posições**, nem mesmo simuladas, neste comando. A validade dos dados externos e o desempenho da estratégia ainda precisam ser testados.

## Backtesting offline (dados sintéticos)

```bash
python -m agente100.backtest_cli
```

O backtest experimental usa rompimento do máximo/mínimo dos 20 candles anteriores, entrada na abertura do candle seguinte, TP de 0,5%, SL de 1%, custos, slippage, duração máxima de 8 candles e valor nocional fixo de 10 unidades fictícias. Em candles que atingem TP e SL, assume SL primeiro. **Este backtest ainda não usa os sinais completos do Agente 100, nem notícias ou dados históricos reais.** Os resultados da demonstração não representam desempenho passado ou esperado. Não há conexão com corretoras. Execute os testes com `python -m unittest discover -s tests -v`.

## Backtest walk-forward do Agente 100

O módulo `agente100.agent_backtest.simulate_agent_history` aceita candles OHLC históricos sincronizados de 15 minutos, calcula os candidatos em cada ponto do tempo com candles já fechados e usa `Agente100.choose` para selecionar o ativo. As entradas hipotéticas ocorrem na abertura do candle seguinte. O tamanho da operação é configurado no simulador; não é decidido pelo agente. Não há execução no Robô 100 nem autorização fictícia: este é apenas um cálculo contrafactual offline.

**Limitações:** não há carregador de histórico remoto nem arquivo histórico incluído; o sentimento de notícias históricas permanece neutro para evitar viés de antecipação; a estratégia não foi validada estatisticamente. Testes automatizados estão em `tests/test_agent_backtest.py`. Para rodar todos: `python -m unittest discover -s tests -v`.

## Histórico público real (pesquisa, sem ordens)

```bash
python -m agente100.history_cli
```

Consulta 120 candles completos de 15 minutos por ativo (BTC-USD, ETH-USD e SOL-USD) da API pública da Coinbase e executa a simulação walk-forward do agente. O carregador `agente100.history.fetch_history` permite de 24 a 300 candles por requisição, exige períodos contínuos e rejeita duplicatas ou lacunas. O comando não cria ordens e não exige credenciais. **Se a API não fornecer todos os candles, o teste é interrompido**, sem inventar dados. O feed pode sofrer limites, bloqueios ou mudanças. Notícias históricas não estão integradas (sentimento neutro); resultados são experimentais, não previsões. Os testes de integração HTTP são mockados e a execução contra a API ainda precisa ser verificada.
