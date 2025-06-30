package com.arabicanalyzer.service

import com.github.msarhan.lucene.ArabicRootExtractorAnalyzer
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute
import org.springframework.stereotype.Service
import java.io.StringReader

@Service
class AnalysisService {

    fun getRoot(word: String): String? {
        ArabicRootExtractorAnalyzer().use { analyzer ->
            val tokenStream = analyzer.tokenStream(null, StringReader(word))
            val termAtt = tokenStream.addAttribute(CharTermAttribute::class.java)
            tokenStream.reset()
            var root: String? = null
            while (tokenStream.incrementToken()) {
                root = termAtt.toString()
            }
            tokenStream.end()
            return root
        }
    }
}