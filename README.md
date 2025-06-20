# Arabic Miracle UI

Welcome to the Arabic Miracle UI repository. This is the frontend component of the Arabic Miracle project, a tool designed to analyze Arabic text with features like morphological analysis, context-aware translation, and Quranic analysis.

## Overview

Arabic Miracle UI is built with Vite and React. It offers users an intuitive interface to:
- **Analyze Arabic Text:** Extract root letters, identify their meanings, and highlight the morphological pattern.
- **Context-Aware Translation:** Receive full context-oriented translations.
- **Quranic Analysis:** Discover how frequently the Arabic root appears in the Quran, along with sample verses.
- **Morphological Weighting:** Visualize the word’s pattern (وزن صرفي) with highlighted key letters.

This UI communicates with the backend API (located in the [arabic-miracle-api](https://github.com/E-ctrl-coder/arabic-miracle-api) repository) via HTTP POST requests, forming a loosely coupled system that allows each part to evolve independently.

## Documentation

For a detailed explanation of the overall project architecture and how the UI and API interact, please refer to our centralized documentation:
- [Centralized Project Documentation (context.md)](context.md)

## Getting Started

### Prerequisites

- **Node.js:** v14 or later (recommended)
- **npm or yarn**

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/E-ctrl-coder/arabic-miracle-ui.git
   cd arabic-miracle-ui
