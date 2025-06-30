package com.arabicanalyzer.service

import com.arabicanalyzer.model.QuranOccurrence
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import jakarta.annotation.PostConstruct
import org.springframework.core.io.ClassPathResource
import org.springframework.stereotype.Service

@Service
class QuranService {

    private data class QuranVerse(val surah: Int, val ayah: Int, val word: String, val root: String, val line: String)

    private lateinit var quranData: List<QuranVerse>

    @PostConstruct
    fun loadData() {
        val jsonText = ClassPathResource("quraan_rooted.json").inputStream.readBytes().toString(Charsets.UTF_8)
        val mapper = jacksonObjectMapper()
        quranData = mapper.readValue(jsonText)
    }

    fun findOccurrences(root: String): List<QuranOccurrence> {
        return quranData.filter { it.root == root }.map { verse ->
            QuranOccurrence(
                surah = verse.surah,
                ayah = verse.ayah,
                text = highlightRoot(verse.line, root)
            )
        }
    }

    private fun highlightRoot(verse: String, root: String): String {
        // Using an immutable Set is cleaner and fixes the bug
        val rootCharSet = root.toSet()

        // Use map and joinToString for a more functional approach
        return verse.map { char ->
            if (char in rootCharSet) {
                """<span style="color:red;font-weight:bold;">$char</span>"""
            } else {
                char.toString()
            }
        }.joinToString("")
    }
}