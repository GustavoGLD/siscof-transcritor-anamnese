# SISCOF Transcrição e Anamnese

**Março–Julho de 2024 • Transcrição e Resumo de Áudio Médico/Clínico em Tempo Real**

---

## 🩺 Visão Geral

O **SISCOF Transcriber** é uma aplicação web baseada em Python, projetada para ajudar médicos e psicólogos a acelerarem a anamnese de pacientes por meio de:

* Captura e transcrição de consultas em tempo real
* Transcrição com diarização de falantes (identificando “Pessoa 1”, “Pessoa 2”, etc.)
* Geração de resumos concisos do diálogo via GPT-3.5
* Disponibilização de transcrições, resumos ou arquivos ZIP para download

Desenvolvido com os **Serviços Cognitivos da Azure** para transcrição de voz, a API de Chat da OpenAI para resumo, e **Solara** para a interface web em tempo real.

---

## 🚀 Funcionalidades Principais

1. **Transcrição de Arquivos**

   * Arraste e solte arquivos `.wav`
   * Transcrição assíncrona com diarização via `ConversationTranscriber` da Azure
   * Indicador de progresso em tempo real
   * Download da transcrição completa (.txt)

2. **Transcrição ao Vivo pelo Microfone**

   * Lista dispositivos de áudio do Windows (via WMI)
   * Captura de áudio ao vivo com PyAudio e IPyWebRTC
   * Encerramento da sessão por voz (“encerrar sessão”) ou manual
   * Exibição da transcrição com diarização em tempo real

3. **Resumos com IA**

   * Resumo de transcrições imperfeitas e ruidosas com GPT-3.5-turbo
   * Resposta transmitida ao vivo na interface
   * Download do resumo individual ou junto com a transcrição em um ZIP

4. **Interface Interativa**

   * Desenvolvido com [Solara](https://github.com/solara-dev/solara) para UI rápida somente com Python
   * Abas, botões, área de upload, atualizações de log em tempo real
   * Gerenciamento de estado seguro entre threads

---

## 🏗 Arquitetura & Estrutura de Código

* **app.py**

  * Componentes Solara: abas para “Ouvir Áudio” (arquivo) e “Ouvir Microfone” (ao vivo)
  * `SessionState`: variáveis reativas para texto da transcrição, resumos, nomes de arquivos e flags de monitoramento
  * Loops em threads para transmitir a saída da Azure e OpenAI para a interface

* **functions/ouvir\_audio.py**

  * `recognize_from_file(file: str)`
  * Configurações de `SpeechConfig` e `AudioConfig` da Azure
  * Eventos do `ConversationTranscriber`: início, transcrição, parada, cancelamento
  * Agregação do texto com marcação de falantes na variável global `Message.message`

* **functions/ouvir\_microfone.py**

  * `recognize_from_device(device_path: str)`
  * Configura o áudio ao vivo do microfone via IPyWebRTC e `AudioInputStream`
  * Controles de parada por voz ou manual com `MicMessage.transcribing_stop`
  * Agregação em `MicMessage.message`

* **Utilitários**

  * Enumeração de dispositivos com `win32com.client` (WMI)
  * Criação de ZIP (`io.BytesIO`, `zipfile`) para transcrição + resumo
  * Streaming da OpenAI com `openai.OpenAI.chat.completions.create(..., stream=True)`

---

## 🛠 Tecnologias Utilizadas

* Python 3.9+
* Azure Cognitive Services Speech SDK
* SDK Python da OpenAI (GPT-3.5-turbo)
* Solara (UI estilo React em Python puro)
* PyAudio, IPyWebRTC (captura de áudio ao vivo)
* win32com (enumeração de dispositivos no Windows)
* Padrões com `threading` e `asyncio`

---

## ⚙️ Instalação e Configuração

1. **Clone o repositório**

   ```bash
   git clone https://github.com/your-org/siscof-transcriber.git
   cd siscof-transcriber
   ```

2. **Crie e ative um ambiente virtual**

   ```bash
   python -m venv venv
   # macOS/Linux
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

3. **Instale as dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**

   ```bash
   export AZURE_SPEECH_KEY=SUA_CHAVE_AZURE
   export AZURE_SPEECH_REGION=brazilsouth
   export OPENAI_API_KEY=SUA_CHAVE_OPENAI
   export OPENAI_ORGANIZATION=...
   export OPENAI_PROJECT=...
   ```

5. **Execute o aplicativo**

   ```bash
   solara run app.py
   ```

6. **Abra seu navegador** em `http://localhost:8080`

---

## 👩‍💻 Como Usar

1. **Ouvir Áudio**

   * Arraste e solte um arquivo `.wav`
   * Aguarde a mensagem “Transcrição em andamento…” até finalizar
   * Baixe a transcrição `.txt` ou gere/baixe o resumo

2. **Ouvir Microfone**

   * Selecione seu microfone no menu
   * Clique em **Iniciar captura**, fale normalmente
   * Diga **“encerrar sessão”** ou clique em **Finalizar captura**
   * Baixe a transcrição e/ou o resumo

---

## 🔍 Desafios & Aprendizados

* Integração da **diarização de falantes** com o `ConversationTranscriber` da Azure
* Atualizações de interface via streaming com **Solara** e threads em Python
* Captura de áudio ao vivo no navegador com **IPyWebRTC**
* Controle robusto de eventos assíncronos para início/parada
* Tratamento de dados de fala imperfeitos para resumos eficazes

---

## 🚧 Trabalhos Futuros

* Pipeline completo de diagnóstico e sugestões de tratamento via LLM
* Correção automática de pontuação e erros pós-processamento
* Suporte a múltiplos idiomas e formatos de áudio adicionais
* Cliente desktop/mobile com funcionalidades offline

---

**Autor:** Gustavo Lídio Damaceno • [Linkedin](https://www.linkedin.com/in/gustavo-lidio-damaceno/)

**Projeto da Empresa:** SISCOF
