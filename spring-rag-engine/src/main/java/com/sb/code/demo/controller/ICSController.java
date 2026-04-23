package com.sb.code.demo.controller;


import java.util.HashMap;        // ✅ was missing
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@SuppressWarnings("unused")
@RestController
public class ICSController {

    private final ChatClient chatClient;
    @SuppressWarnings("unused")
    private final VectorStore vectorStore;

    public ICSController(ChatClient.Builder builder, VectorStore vectorStore) {
        this.vectorStore = vectorStore;
        this.chatClient = builder.build();
    }

    private String prompt = """
            Your task is to answer the questions about Indian Constitution. Use the information from the DOCUMENTS
            section to provide accurate answers. If unsure or if the answer isn't found in the DOCUMENTS section,
            simply state that you don't know the answer.

            QUESTION:
            {input}

            DOCUMENTS:
            {documents}

            """;

    @GetMapping("/ics")
    public String icsQuestion(@RequestParam String q) {
        System.out.println("Question: " + q + " Answer: " + chatClient.prompt().user(q).call().content());
        return chatClient.prompt().user(q).call().content();
    }

    @GetMapping("/ic")
    public String simplifyIC(@RequestParam String q) {
        PromptTemplate template = new PromptTemplate(prompt);
        Map<String, Object> promptParams = new HashMap<>();
        promptParams.put("input", q);
        promptParams.put("documents", findSimilarData(q));  // ✅ was incorrectly passing `q` instead of retrieved docs

        return chatClient.prompt(template.create(promptParams)).call().content();
    }

    private String findSimilarData(String q) {
        List<Document> documents =
                vectorStore.similaritySearch(
                        SearchRequest.builder() 
                            .query(q)
                            .topK(5) 
                            .build());

        return documents
                .stream()
                .map(Document::getText)
                .collect(Collectors.joining("\n"));
    }
  }