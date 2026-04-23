package com.sb.code.demo.controller;

import java.util.List;
import java.util.Map;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {
	private final ChatClient chatClient;

	@Value("classpath:/prompts/celeb-details.st")
	private Resource celebPrompt;

	public HelloController(ChatClient.Builder builder) {
		this.chatClient = builder.build();
	}

	@GetMapping("/chat")
	public String prompt(@RequestParam String message) {
//		String promptResponse = chatClient
//		.prompt()// ChatClientRequestSpec 
//        .system("You are a helpful assistant who replies concisely.")
//        .user(message)
//        .call()// CallResponseSpec
//		.content();		
		String promptResponse = chatClient.prompt(message).call().chatResponse().getResult().getOutput().getText();
		System.out.println("Prompt: " + message + "\nResponse: " + promptResponse);

		return promptResponse;
	}

//	chatClient
//    .prompt()          // 1️ Start building the prompt
//    .system("...")     // 2️ Set AI behaviour/persona
//    .user(message)     // 3️ Pass the user's actual question
//    .call()            // 4️ Send request to OpenAI API
//    .content();        // 5️ Extract plain text from response

	@GetMapping("/celeb")
	public String getCelebDetails(@RequestParam String name) {

		PromptTemplate template = new PromptTemplate(celebPrompt);
		Prompt prompt = template.create(Map.of("name", name));

		return chatClient.prompt(prompt) // ✅ fixed typo: promp → prompt
				.call().chatResponse().getResult().getOutput().getText(); // ✅ getContent() → getText()
	}

	@GetMapping("/sports")
	public String getSportsDetails(@RequestParam String name) {

		String message = """
				List the details of the Sport %s along with their
				Career achievements. Show the details in a readable format.
				""";

		String systemPrompt = """
				You are a smart Virtual Assistant.
				Your task is to give the details about Sports.
				If someone asks about something else and you do not know,
				just say that you do not know the answer.
				""";

		UserMessage userMessage = new UserMessage(String.format(message, name));
		SystemMessage systemMessage = new SystemMessage(systemPrompt);

		Prompt prompt = new Prompt(List.of(systemMessage, userMessage)); // ✅ system first, user second

		return chatClient.prompt(prompt) // ✅ typo fixed: promp → prompt
				         .call()
				         .chatResponse()
				         .getResult()
				         .getOutput()
				         .getText(); // ✅ getContent() → getText()
	}
}
