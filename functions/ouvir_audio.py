import os
import time
import azure.cognitiveservices.speech as speechsdk
import pyaudio
import solara

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


def recognize_from_file(file: str):
    Message.message = '```\n\n'
    speech_config = speechsdk.SpeechConfig(subscription="***", region="brazilsouth")
    speech_config.speech_recognition_language = "pt-BR"

    audio_config = speechsdk.audio.AudioConfig(filename=file)
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config,
                                                                               audio_config=audio_config)

    transcribing_stop = False

    def stop_cb(evt: speechsdk.SessionEventArgs):
        #print('CLOSING on {}'.format(evt))
        nonlocal transcribing_stop
        transcribing_stop = True

    conversation_transcriber.transcribed.connect(conversation_transcriber_transcribed_cb)
    conversation_transcriber.session_started.connect(conversation_transcriber_session_started_cb)
    conversation_transcriber.session_stopped.connect(conversation_transcriber_session_stopped_cb)
    conversation_transcriber.canceled.connect(conversation_transcriber_recognition_canceled_cb)
    # stop transcribing on either session stopped or canceled events
    conversation_transcriber.session_stopped.connect(stop_cb)
    conversation_transcriber.canceled.connect(stop_cb)

    conversation_transcriber.start_transcribing_async()

    # Waits for completion.
    while not transcribing_stop:
        time.sleep(.5)

    conversation_transcriber.stop_transcribing_async()


if __name__ == '__main__':
    try:
        recognize_from_file(file=file)
    except Exception as err:
        print("Encountered exception. {}".format(err))

    print("```")

    from openai import OpenAI

    client = OpenAI(
        api_key='***',
        organization='***',
        project='***',
    )

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content":
            f"Sabendo que esse é um texto transcrito por IA, podendo ter erros de pontuação e palavras erradas "
            f"por pronúncias semelhantes, pelo o contexto, resuma o que é essa conversa: ```{Message.message}```"}],
        stream=True,
    )
    print("~" * 30)
    print("*RESUMO DA CONVERSA*\n")
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
