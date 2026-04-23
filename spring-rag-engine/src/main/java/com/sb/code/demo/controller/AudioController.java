package com.sb.code.demo.controller;

import org.springframework.ai.openai.audio.speech.SpeechPrompt;  
import org.springframework.ai.audio.transcription.AudioTranscriptionPrompt;
import org.springframework.ai.openai.OpenAiAudioSpeechModel;
import org.springframework.ai.openai.OpenAiAudioSpeechOptions;
import org.springframework.ai.openai.OpenAiAudioTranscriptionModel;
import org.springframework.ai.openai.OpenAiAudioTranscriptionOptions;
import org.springframework.ai.openai.api.OpenAiAudioApi;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AudioController {

 private final OpenAiAudioTranscriptionModel openAiAudioTranscriptionModel;
 private final OpenAiAudioSpeechModel openAiAudioSpeechModel;

 public AudioController(OpenAiAudioTranscriptionModel transcriptionModel,
                        OpenAiAudioSpeechModel speechModel) {
     this.openAiAudioTranscriptionModel = transcriptionModel;
     this.openAiAudioSpeechModel = speechModel;
 }

 @GetMapping("/audio-to-text")
 public String audioTranscription() {

     OpenAiAudioTranscriptionOptions options =
             OpenAiAudioTranscriptionOptions.builder()
                     .language("en")
                     .responseFormat(OpenAiAudioApi.TranscriptResponseFormat.TEXT)
                     .temperature(0f)
                     .build();

     AudioTranscriptionPrompt prompt =
             new AudioTranscriptionPrompt(
                     new ClassPathResource("audio/sample_audio1.mp3"),
                     options
             );

     return openAiAudioTranscriptionModel
             .call(prompt)
             .getResult()
             .getOutput();
 }

 @GetMapping("/text-to-audio/{prompt}")
 public ResponseEntity<byte[]> generateAudio(@PathVariable String prompt) {

     OpenAiAudioSpeechOptions options =
             OpenAiAudioSpeechOptions.builder()
                     .model(OpenAiAudioApi.TtsModel.TTS_1.getValue())
                     .responseFormat(OpenAiAudioApi.SpeechRequest.AudioResponseFormat.MP3)
                     .voice(OpenAiAudioApi.SpeechRequest.Voice.ALLOY)
                     .speed(1.0f)
                     .build();

     SpeechPrompt speechPrompt = new SpeechPrompt(prompt, options); // ✅ Fixed

     byte[] audioBytes = openAiAudioSpeechModel
             .call(speechPrompt)
             .getResult()
             .getOutput();

     return ResponseEntity.ok()
             .header(HttpHeaders.CONTENT_TYPE, "audio/mpeg")
             .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=output.mp3")
             .body(audioBytes);
 }
}