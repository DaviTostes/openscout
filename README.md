# 🔍 OpenScout

Buscador inteligente de vagas de tecnologia personalizado baseado no seu currículo.

## Para que serve

OpenScout analisa seu currículo automaticamente e busca vagas de tecnologia relevantes no LinkedIn que correspondam às suas habilidades, experiência e localização.

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:

```bash
OPENAI_API_KEY=sua_chave_aqui
SERPER_API_KEY=sua_chave_aqui
```

**Onde conseguir:**
- **OpenAI API Key**: https://platform.openai.com/api-keys
- **Serper API Key**: https://serper.dev/api-key (para busca no Google)

### Instalação

```bash
pip install -r requirements.txt
```

## Como Rodar

```bash
streamlit run main.py
```

Acesse `http://localhost:8501` no navegador.

## Como Usar

1. Envie seu currículo (PDF ou DOCX)
2. Clique em "🚀 Buscar Vagas"
3. Veja a análise do seu perfil e vagas encontradas
4. Filtre por plataforma ou nível de experiência

## Tecnologias

- **Streamlit**: Interface web
- **CrewAI**: Orquestração de agentes IA
- **OpenAI**: Análise de currículo
- **Serper**: Busca de vagas
