
# Presidente Simulator — V0.1

Protótipo de um simulador geopolítico mobile em Python/Kivy.

## O que já existe

- Gabinete presidencial com interface visual em estilo 3D/diegético
- Telejornal e manchetes dinâmicas
- Sistema econômico básico
- Aprovação popular
- Apoio no Congresso
- Risco de impeachment
- Risco de golpe
- Eventos nacionais
- Coletiva de imprensa
- Feed social fictício
- Capas/manchetes de mídia
- Diplomacia entre países
- Mapa-múndi estilizado
- Sistema militar abstrato
- Passagem de tempo
- Salvamento/carregamento local

## Rodar no PC para teste

```bash
python -m pip install kivy==2.3.0
python main.py
```

## Gerar APK no GitHub Actions

1. Crie um repositório no GitHub.
2. Envie todos os arquivos deste projeto.
3. Abra a aba **Actions**.
4. Selecione **Build Presidente Simulator APK**.
5. Clique em **Run workflow**.
6. Quando terminar, abra o job concluído.
7. Na seção **Artifacts**, baixe `Presidente-Simulator-V0.1-APK`.

Também é possível criar uma tag `v0.1.0`; o workflow será executado automaticamente.
Durante a estabilização do empacotamento Android, pushes para a branch `main`
também iniciam o build. O APK gerado é exclusivamente para aparelhos
`arm64-v8a`.

## Observação

A V0.1 prioriza o motor e a interface jogável. O mapa é propositalmente estilizado e não é ainda o mapa geográfico 3D final. As próximas versões podem adicionar dados geográficos reais, cidades, unidades militares, IA internacional, mercado, eleições e mídia 3D mais avançada.
