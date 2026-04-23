package com.sb.code.demo.config;

import org.springframework.ai.reader.pdf.PagePdfDocumentReader;
import org.springframework.ai.reader.pdf.config.PdfDocumentReaderConfig;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;

@Component
public class PGVectorLoader {

	 @Value("classpath:/Indian_Constitution.pdf")
	    private Resource pdfResource;
	 
	 private final VectorStore vectorStore;
	 private final JdbcClient jdbcClient;
	 
	public PGVectorLoader(VectorStore vectorStore, JdbcClient jdbcClient) {
		super();
		this.vectorStore = vectorStore;
		this.jdbcClient = jdbcClient;
	}
	
	@PostConstruct
	public void init(){
		Integer count = jdbcClient.sql("select COUNT(*) from vector_store").query(Integer.class).single();
		System.out.println("No. of documents in pgVector DB Count: "+count);
		
		if(count == 0) {
			System.out.println("Initilizing PG Vecotr Store Load !!!");
			
			 PdfDocumentReaderConfig pdfDocConfig = PdfDocumentReaderConfig.builder()
	                    .withPagesPerDocument(1)
	                    .build();

	            PagePdfDocumentReader reader =
	                    new PagePdfDocumentReader(pdfResource, pdfDocConfig);
	            
	            var textSplitter = new TokenTextSplitter();
	            
	            vectorStore.accept(textSplitter.apply(reader.get()));
	            
	            System.out.println("Applicaiton is started and Ready to serve!!!");
		}
	}
	 
	 
}
