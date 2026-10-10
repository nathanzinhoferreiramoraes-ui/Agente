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
