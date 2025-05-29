import io
import threading
import zipfile

import solara
import solara.lab
from openai import OpenAI
from solara.components.file_drop import FileInfo
import time
import win32com.client

import os
import time
import azure.cognitiveservices.speech as speechsdk
import pyaudio
import solara

from functions.ouvir_audio import recognize_from_file

file = '../uploaded.wav'

print("```")

class Message:
    message = ''
    output = ''


def conversation_transcriber_recognition_canceled_cb(evt: speechsdk.SessionEventArgs):
    print('🛈 Canceled event')


def conversation_transcriber_session_stopped_cb(evt: speechsdk.SessionEventArgs):
    print('🛈 SessionStopped event')
    Message.message += f'```'


def conversation_transcriber_transcribed_cb(evt: speechsdk.SpeechRecognitionEventArgs):
    #print('TRANSCRIBED:')
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        #print('\tText={}'.format(evt.result.text))
        #print('\tSpeaker ID={}'.format(evt.result.speaker_id))
        Message.message += f'Pessoa {evt.result.speaker_id}: "{evt.result.text}"\n\n'
        print(f'{evt.result.speaker_id}: "{evt.result.text}"')
    elif evt.result.reason == speechsdk.ResultReason.NoMatch:
        print('\tNOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))


def conversation_transcriber_session_started_cb(evt: speechsdk.SessionEventArgs):
    print('SessionStarted event')


from functions.ouvir_microfone import MicMessage, recognize_from_device


client = OpenAI(
    api_key='***',
    organization='***',
    project='***',
)


def listar_dispositivos_e_paths():
    wmi = win32com.client.GetObject("winmgmts:")
    dispositivos = wmi.InstancesOf("Win32_PnPEntity")
    dispositivos_e_paths = {}

    for dispositivo in dispositivos:
        if "MMDEVAPI" in dispositivo.DeviceID:
            dispositivos_e_paths[dispositivo.Name] = dispositivo.DeviceID

    return dispositivos_e_paths


class SessionState:
    audio_output = solara.reactive("")
    mic_output = solara.reactive("")

    novo = solara.reactive(0)
    stroutput = ''

    selected_device = solara.reactive('')

    audio_monitoring = solara.reactive(False)
    mic_monitoring = solara.reactive(False)
    mic_capturing = solara.reactive(False)

    mic_again = solara.reactive(False)

    overview_audio = solara.reactive('')
    overview_mic = solara.reactive('')

    audio_transc_filename = solara.reactive('trascricao')
    mic_transc_filename = solara.reactive('trascricao')


def audio_monitor_output():
    if not SessionState.audio_monitoring.value:
        SessionState.audio_monitoring.value = True
        while True:
            SessionState.audio_output.value = Message.message
            time.sleep(0.2)


def mic_monitor_output(process):
    if not SessionState.mic_monitoring.value:
        SessionState.mic_monitoring.value = True
        while True:
            SessionState.mic_output.value = MicMessage.message
            time.sleep(0.2)

            if not SessionState.mic_monitoring.value:
                print('Encerrando processo...')
                break


def on_file(file: FileInfo):
    if file["name"][-3:] == 'wav':
        with open('uploaded.wav', 'wb') as f:
            f.write(file["data"])
        thread = threading.Thread(target=recognize_from_file, args=('uploaded.wav',))
        thread.start()
        if not SessionState.audio_monitoring.value:
            SessionState.novo.value = True
            thread = threading.Thread(target=audio_monitor_output)
            thread.start()
    else:
        raise ValueError("Arquivo inválido. Por favor, envie um arquivo '.wav'.")


def start_mic():
    if not SessionState.mic_monitoring.value:
        print(f'Iniciando captura... {SessionState.selected_device.value=}')
        # '{0.0.1.00000000}.{3307B578-E12D-4064-9771-0D8F04E834C1}'
        thread = threading.Thread(target=recognize_from_device, args=(SessionState.selected_device.value,))
        thread.start()

        SessionState.novo.value = True
        thread = threading.Thread(target=mic_monitor_output, args=(thread,))
        thread.start()


def exit_mic():
    SessionState.mic_monitoring.value = False
    MicMessage.transcribing_stop = True
    SessionState.mic_again.value = True


def on_value(lista: dict):
    def f(value):
        SessionState.selected_device.value = lista[value].split('\\')[-1]
        print(f"{SessionState.selected_device.value=}")
    return f


def resumo_audio():
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content":
            f"Sabendo que esse é um texto transcrito por IA, podendo ter erros de pontuação e palavras erradas "
            f"por pronúncias semelhantes, pelo o contexto, resuma o que é essa conversa: ```{Message.message}```"}],
        stream=True,
    )

    def func():
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                SessionState.overview_audio.value += chunk.choices[0].delta.content

    thread = threading.Thread(target=func)
    thread.start()


def resumo_mic():
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content":
            f"Sabendo que esse é um texto transcrito por IA, podendo ter erros de pontuação e palavras erradas "
            f"por pronúncias semelhantes, pelo o contexto, resuma o que é essa conversa: ```{MicMessage.message}```"}],
        stream=True,
    )

    def func():
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                SessionState.overview_mic.value += chunk.choices[0].delta.content

    thread = threading.Thread(target=func)
    thread.start()


def clear_audio():
    SessionState.audio_output.value = ''
    SessionState.overview_audio.value = ''
    SessionState.audio_transc_filename.value = 'transcricao'
    SessionState.audio_monitoring.value = False


def clear_mic():
    SessionState.mic_output.value = ''
    SessionState.overview_mic.value = ''
    SessionState.mic_transc_filename.value = 'transcricao'
    SessionState.mic_monitoring.value = False
    SessionState.mic_again.value = False
    MicMessage.message = ''


def create_zip(string1, string2):
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w') as zip_file:
        zip_file.writestr('transcricao.txt', string1)
        zip_file.writestr('resumo.txt', string2)

    buffer.seek(0)
    return buffer





@solara.component
def Page():
    with solara.Column() as main:
        solara.Info("Aplicação ainda em desenvolvimento.", dense=True)

    with solara.AppBarTitle():
        solara.Text("SISCOF Transcritor")

    with solara.Row():
        with solara.lab.Tabs(background_color="primary", dark=True):
            with solara.lab.Tab("Ouvir Áudio", icon_name="mdi-folder"):
                solara.Markdown("### **Transcrever um arquivo de áudio**\n\n")
                solara.FileDrop("Arraste para aqui o áudio em '.wav'", on_file=on_file, lazy=False)
                with solara.Row():
                    solara.Markdown("----")

                if len(SessionState.audio_output.value) >= 3:
                    if str(SessionState.audio_output.value)[-3:] != '```':
                        solara.Info(label='Transcrição em andamento...', text=True, dense=False, outlined=False, icon=True)
                    else:
                        solara.Success(label='Transcrição finalizada.', text=True, dense=False, outlined=False, icon=True)

                    solara.Markdown(str(SessionState.audio_output.value))
                    solara.Markdown("----")

                    with solara.Row():
                        solara.InputText(label="Nome do arquivo", value=SessionState.audio_transc_filename)
                    with solara.Row():
                        solara.FileDownload(
                            str(SessionState.audio_output.value),
                            filename=f"{SessionState.audio_transc_filename.value}.txt",
                            label=f"Download {SessionState.audio_transc_filename.value}.txt"
                        )
                        solara.Button('Gerar Resumo', icon_name='mdi-script-text-outline', on_click=resumo_audio)
                        solara.Button('Limpar', icon_name='mdi-delete', on_click=clear_audio)

                    if len(SessionState.overview_audio.value) > 0:
                        solara.Markdown("### **Resumo da transcrição**\n\n")
                        solara.Markdown(SessionState.overview_audio.value)

                        with solara.Row():
                            solara.FileDownload(
                                create_zip(str(SessionState.audio_output.value), str(SessionState.overview_audio.value)),
                                filename=f"{SessionState.audio_transc_filename.value}.zip",
                                label=f"Download {SessionState.audio_transc_filename.value}.zip"
                            )
                            solara.FileDownload(
                                str(SessionState.overview_audio.value),
                                filename=f"{SessionState.audio_transc_filename.value}_resumo.txt",
                                label=f"Download {SessionState.audio_transc_filename.value}_resumo.txt"
                            )

                    solara.Markdown("\n\n\n\n")

            with solara.lab.Tab("Ouvir Microfone", icon_name="mdi-microphone"):
                solara.Markdown("### **Transcrever o áudio do microfone**\n\n")
                aaa = listar_dispositivos_e_paths()
                with solara.Row():
                    solara.Select(label="Selecione o Microfone", values=list(aaa.keys()), on_value=on_value(aaa))
                with solara.Row():
                    solara.Button("Iniciar captura", on_click=start_mic, disabled=SessionState.mic_monitoring.value, icon_name='mdi-play')
                    solara.Button("Finalizar captura", on_click=exit_mic, disabled=not SessionState.mic_monitoring.value, icon_name='mdi-stop')
                solara.Markdown("\n\n\n\n")

                if SessionState.mic_again.value or SessionState.mic_monitoring.value:
                    solara.Markdown("----")
                    if SessionState.mic_monitoring.value and SessionState.mic_again.value:
                        solara.Success(label='Captura finalizada.', text=True, dense=False, outlined=False, icon=True)
                    elif SessionState.mic_monitoring.value:
                        solara.Info(label='Capturando áudio...', text=True, dense=False, outlined=False, icon=True)

                    with solara.Row():
                        solara.Markdown("\n\n" + str(SessionState.mic_output.value) + "\n\n")
                    solara.Markdown("----")

                    with solara.Row():
                        solara.InputText(
                            label="Nome do arquivo",
                            value=SessionState.mic_transc_filename
                        )
                    with solara.Row():
                        solara.FileDownload(
                            str(SessionState.mic_output.value),
                            filename=f"{SessionState.mic_transc_filename.value}.txt",
                            label=f"Download {SessionState.mic_transc_filename.value}.txt"
                        )
                        solara.Button('Gerar Resumo', icon_name='mdi-script-text-outline', on_click=resumo_mic, disabled=bool(SessionState.overview_mic.value))
                        solara.Button('Limpar', icon_name='mdi-delete', on_click=clear_mic)

                    if len(SessionState.overview_mic.value) > 0:
                        solara.Markdown("### **Resumo da transcrição**\n\n")
                        solara.Markdown(SessionState.overview_mic.value)

                        with solara.Row():
                            solara.FileDownload(
                                create_zip(str(SessionState.mic_output.value), str(SessionState.overview_mic.value)),
                                filename=f"{SessionState.mic_transc_filename.value}.zip",
                                label=f"Download {SessionState.mic_transc_filename.value}.zip"
                            )
                            solara.FileDownload(
                                str(SessionState.overview_mic.value),
                                filename=f"{SessionState.mic_transc_filename.value}_resumo.txt",
                                label=f"Download {SessionState.mic_transc_filename.value}_resumo.txt"
                            )

                    solara.Markdown("\n\n\n\n")
