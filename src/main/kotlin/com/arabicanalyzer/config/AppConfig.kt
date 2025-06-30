package com.arabicanalyzer.config

import com.openai.client.OpenAIClient
import com.openai.client.okhttp.OpenAIOkHttpClient
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class AppConfig {

    @Value("\${openai.api-key}")
    private lateinit var openAIKey: String

    @Bean
    fun openAIClient(): OpenAIClient {
        return OpenAIOkHttpClient.builder().apiKey(openAIKey).build()
    }
}