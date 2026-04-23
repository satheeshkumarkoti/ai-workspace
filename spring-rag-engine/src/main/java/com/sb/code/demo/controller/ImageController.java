package com.sb.code.demo.controller;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;        
import org.springframework.ai.image.ImageModel;
import org.springframework.ai.image.ImagePrompt;
import org.springframework.ai.image.ImageResponse;
import org.springframework.ai.openai.OpenAiImageOptions;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.MimeTypeUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

// Open AI link for https://platform.openai.com/docs/api-reference/images/create

@RestController
public class ImageController {

    private final ChatModel chatModel;
    private final ImageModel imageModel;

    public ImageController(ChatModel chatModel, ImageModel imageModel) {
        this.chatModel = chatModel;
        this.imageModel = imageModel;
    }

    // GET /image-to-textImage → AI text description
    @GetMapping("image-to-text")
    public String describeImage() {
        String response = ChatClient.create(chatModel).prompt()
                .user(useSpec -> useSpec
                        .text("Explain what you see in this Image")
                        .media(MimeTypeUtils.IMAGE_JPEG, new ClassPathResource("images/elephant_lion.jpg")))
                .call()
                .content();
        return response;
    }

    
    //GET /image/{prompt}Text prompt → DALL-E image
    @GetMapping("/image/{prompt}")
    public ResponseEntity<String> generateImage(@PathVariable String prompt) {

        ImageResponse response = imageModel.call(
                new ImagePrompt(prompt,
                        OpenAiImageOptions
                                .builder()
                                .N(1)
                                .width(1024)
                                .height(1024)
                                .quality("hd")
                                .build())
        );

        String imageUrl = response.getResult().getOutput().getUrl();
        String html = "<html><body><img src='" + imageUrl + "' width='1024'/></body></html>";

        return ResponseEntity.ok()
                .contentType(MediaType.TEXT_HTML)
                .body(html);
    }
}



