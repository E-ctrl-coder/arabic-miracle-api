package com.arabicanalyzer

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class ArabicAnalyzerApplication

fun main(args: Array<String>) {
    runApplication<ArabicAnalyzerApplication>(*args)
}