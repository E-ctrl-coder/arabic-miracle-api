package com.arabicanalyzer.model

data class AnalyzeRequest(val word: String)

data class QuranOccurrence(
    val surah: Int,
    val ayah: Int,
    val text: String
)

data class AnalyzeResponse(
    val word: String,
    val root: String?,
    val translation: String,
    val quranOccurrences: List<QuranOccurrence>,
    val occurrenceCount: Int
)

data class ErrorResponse(val error: String)