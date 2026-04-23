package com.sb.code.demo.controller;

import java.util.List;
import java.util.Map;

import org.jspecify.annotations.Nullable;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.Generation;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.ai.converter.BeanOutputConverter;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.sb.code.demo.model.Achievements;
import com.sb.code.demo.model.Player;

@RestController
public class PlayerController {

	private final ChatClient chatClient;

	public PlayerController(ChatClient.Builder builder) {
		this.chatClient = builder.build();
	}

	@GetMapping("/player")
	public List<Player> getPlayerAchievement(@RequestParam String name) {

		BeanOutputConverter<List<Player>> converter = new BeanOutputConverter<>(
				new ParameterizedTypeReference<List<Player>>() {
				});

		String message = """
				Generate career achievements for the sportsperson {sport}.
				Return a list where each item has:
				- playerName: the name of the sportsperson
				- achievements: a list of their career achievements
				Return the response strictly in the following JSON format:
				{format}
				""";

		PromptTemplate template = new PromptTemplate(message);
		Prompt prompt = template.create(Map.of("sport", name, "format", converter.getFormat()));

//		ChatResponse response = chatClient.prompt(prompt).call().chatResponse();
//		return response.getResult().getOutput().getText();

		Generation result = chatClient.prompt(prompt).call().chatResponse().getResult();

		String text = result.getOutput().getText();
		System.out.println("Raw AI Response:\n" + text); // 👈 check console

		return converter.convert(text);
	}

	@GetMapping("/achievement/player")
	public @Nullable List<Achievements> getAchievvements(@RequestParam String name) {
		String message = """
					Provide List of achievements for {player}
				""";

		PromptTemplate template = new PromptTemplate(message);
		Prompt prompt = template.create(Map.of("player", name));

		return chatClient.prompt(prompt).call().entity(new ParameterizedTypeReference<List<Achievements>>() {
		});

	}
}