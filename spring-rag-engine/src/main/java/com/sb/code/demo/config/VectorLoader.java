package com.sb.code.demo.config;

import java.io.File;
import java.util.List;

import org.springframework.ai.document.Document;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.reader.pdf.PagePdfDocumentReader;
import org.springframework.ai.reader.pdf.config.PdfDocumentReaderConfig;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.SimpleVectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
//import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;

// Initially testing propose the @Configuration has been used.. now moving to pgvector ( Postgres Vector Database) 
//@Configuration
public class VectorLoader {

    @Value("classpath:/Indian_Constitution.pdf")
    private Resource pdfResource;

    @Bean
    public SimpleVectorStore vectorStore(EmbeddingModel embeddingModel) {

        // Builder requires the embedding model
        SimpleVectorStore vectorStore = SimpleVectorStore.builder(embeddingModel)
                .build();

        File vectorStoreFile = new File("vector_store.json");

        if (vectorStoreFile.exists()) {
            System.out.println("Loaded Vector Store File!");
            vectorStore.load(vectorStoreFile);
        } else {
            System.out.println("Creating Vector Store!");

            PdfDocumentReaderConfig pdfDocConfig = PdfDocumentReaderConfig.builder()
                    .withPagesPerDocument(1)
                    .build();

            PagePdfDocumentReader reader =
                    new PagePdfDocumentReader(pdfResource, pdfDocConfig);

            TokenTextSplitter textSplitter = new TokenTextSplitter();

            List<Document> documents = textSplitter.apply(reader.get());

            vectorStore.add(documents);

            vectorStore.save(vectorStoreFile);
        }

        return vectorStore;
    }
}