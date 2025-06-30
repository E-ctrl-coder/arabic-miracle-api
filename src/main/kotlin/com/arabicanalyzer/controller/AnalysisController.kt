package com.arabicanalyzer.controller

import com.arabicanalyzer.model.AnalyzeRequest
import com.arabicanalyzer.model.AnalyzeResponse
import com.arabicanalyzer.model.ErrorResponse
import com.arabicanalyzer.service.AnalysisService
import com.arabicanalyzer.service.QuranService
import com.arabicanalyzer.service.TranslationService
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/")
// Enables CORS for the frontend to connect
@CrossOrigin(origins = ["*"])
class AnalysisController(
    private val analysisService: AnalysisService,
    private val quranService: QuranService,
    private val translationService: TranslationService
) {

    @GetMapping
    fun home(): String {
        return "Arabic Miracle (Spring Boot) backend is running."
    }

    @PostMapping("/analyze")
    suspend fun analyze(@RequestBody request: AnalyzeRequest): ResponseEntity<Any> {
        val word = request.word.trim()
        if (word.isBlank()) {
            return ResponseEntity
                .badRequest()
                .body(ErrorResponse("No word provided"))
        }

        val root = analysisService.getRoot(word)
            ?: return ResponseEntity
                .badRequest()
                .body(ErrorResponse("Could not determine root for the word."))

        val translation = translationService.getTranslation(word, root)
        val occurrences = quranService.findOccurrences(root)

        val response = AnalyzeResponse(
            word = word,
            root = root,
            translation = translation,
            quranOccurrences = occurrences,
            occurrenceCount = occurrences.size
        )

        return ResponseEntity.ok(response)
    }
}

@RestControllerAdvice
class GlobalExceptionHandler {
    private val logger = LoggerFactory.getLogger(javaClass)

    @ExceptionHandler(Exception::class)
    fun handleAllExceptions(e: Exception): ResponseEntity<ErrorResponse> {
        logger.error("An unhandled exception occurred", e)
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse("An internal error occurred: ${e.message}"))
    }
}