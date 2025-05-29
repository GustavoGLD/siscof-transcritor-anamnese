import sys
import time
import azure.cognitiveservices.speech as speechsdk
import win32com.client
from azure.cognitiveservices.speech.audio import AudioInputStream
from ipywebrtc import CameraStream, AudioRecorder
from openai import OpenAI

from openai import OpenAI

from IPython.display import display

class MicMessage:
    message = ''
    transcribing_stop = False


def listar_dispositivos_e_paths():
    wmi = win32com.client.GetObject("winmgmts:")
    dispositivos = wmi.InstancesOf("Win32_PnPEntity")
    dispositivos_e_paths = {}

    for dispositivo in dispositivos:
        if "MMDEVAPI" in dispositivo.DeviceID:
            dispositivos_e_paths[dispositivo.Name] = dispositivo.DeviceID

    return dispositivos_e_paths


def conversation_transcriber_recognition_canceled_cb(evt: speechsdk.SessionEventArgs):
    print('Canceled event')


def conversation_transcriber_session_stopped_cb(evt: speechsdk.SessionEventArgs):
    print('SessionStopped event')


def conversation_transcriber_transcribed_cb(evt: speechsdk.SpeechRecognitionEventArgs):
    print('TRANSCRIBED:')
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print('\tText={}'.format(evt.result.text))
        print('\tSpeaker ID={}'.format(evt.result.speaker_id))
        MicMessage.message += f'Pessoa {evt.result.speaker_id}: "{evt.result.text}"\n\n'
        if 'encerrar sessão' in evt.result.text.lower():
            MicMessage.transcribing_stop = True
    elif evt.result.reason == speechsdk.ResultReason.NoMatch:
        print('\tNOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))


def conversation_transcriber_session_started_cb(evt: speechsdk.SessionEventArgs):
    print('SessionStarted event')


def recognize_from_device(device_instance_path):
    speech_config = speechsdk.SpeechConfig(subscription="***", region="brazilsouth")
    speech_config.speech_recognition_language = "pt-BR"

    
    #print(f'{device_instance_path=}')
    camera = CameraStream(constraints={'audio': True, 'video': False})
    recorder = AudioRecorder(stream=camera)
    stream = AudioInputStream(recorder.codecs)
    audio_config = speechsdk.audio.AudioConfig(stream=stream)
    #audio_config = speechsdk.audio.AudioConfig(device_name='{0.0.1.00000000}.{3307B578-E12D-4064-9771-0D8F04E834C1}')
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config,
                                                                               audio_config=audio_config)

    def stop_cb(evt: speechsdk.SessionEventArgs):
        print('CLOSING on {}'.format(evt))
        MicMessage.transcribing_stop = True

    conversation_transcriber.transcribed.connect(conversation_transcriber_transcribed_cb)
    conversation_transcriber.session_started.connect(conversation_transcriber_session_started_cb)
    conversation_transcriber.session_stopped.connect(conversation_transcriber_session_stopped_cb)
    conversation_transcriber.canceled.connect(conversation_transcriber_recognition_canceled_cb)
    conversation_transcriber.session_stopped.connect(stop_cb)
    conversation_transcriber.canceled.connect(stop_cb)

    conversation_transcriber.start_transcribing_async()

    while not MicMessage.transcribing_stop:
        time.sleep(.5)

    conversation_transcriber.stop_transcribing_async()

    MicMessage.transcribing_stop = False


if __name__ == '__main__':
    device_instance_path_selected = "sys.argv[1]"
    print(f'{device_instance_path_selected=}')
    try:
        print('Diga "encerrar sessão" para finalizar.')
        recognize_from_device(device_instance_path_selected)
    except Exception as err:
        print(f"Encontrado uma exceção: {err}")

    client = OpenAI(
        api_key='***',
        organization='***',
        project='***',
    )

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content":
            f"Sabendo que esse é um texto transcrito por IA, podendo ter erros de pontuação e palavras erradas "
            f"por pronúncias semelhantes, pelo o contexto, resuma o que é essa conversa: ```{MicMessage.message}```"
            f"ignore a frase 'Encerrar sessão'"}],
        stream=True,
    )
    print("~" * 30)
    print("*RESUMO DA CONVERSA*\n")
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
