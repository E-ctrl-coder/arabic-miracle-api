package com.arabicanalyzer.service

import com.openai.client.OpenAIClient
import com.openai.models.*
import org.springframework.stereotype.Service

@Service
class TranslationService(private val openAI: OpenAIClient) {

    suspend fun getTranslation(word: String, root: String): String {
        val systemMessage = ChatCompletionSystemMessageParam.Content.ofText(
            "You are an expert in Arabic linguistics and etymology. Provide a concise English translation and a brief explanation of the word's origin from its root."
        )

        val userMessage = ChatCompletionUserMessageParam.Content.ofText(
            "Analyze the Arabic word '$word' which comes from the root '$root'."
        )

        val request = ChatCompletionCreateParams.builder()
            .addSystemMessage(systemMessage)
            .addUserMessage(userMessage)
            .model("gpt-4o-mini")
            .temperature(0.3)
            .maxTokens(150) // Increased slightly for better explanations
            .build()

        return try {
            val response = openAI.chat().completions().create(request)

            // Safely extract the content from the response. This is much more robust.
            response.choices()
                .firstOrNull()
                ?.message()
                ?.content()
                ?.orElse("No translation available from API.") // Handle empty Optional
                ?: "No choice or message returned from API." // Handle null choice/message
        } catch (e: Exception) {
            // Handle potential API errors gracefully
            "Error fetching translation: ${e.message}"
        }
    }
}