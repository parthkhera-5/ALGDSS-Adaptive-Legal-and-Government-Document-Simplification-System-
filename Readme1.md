Here's a clean, professional README.md for your Legal Document Generator (ALGDSS) without any images or diagrams. It's suitable for GitHub and reflects your current implementation.

# Legal Document Generator (ALGDSS)

An AI-powered Legal Document Generator that helps users search, retrieve, and generate legal document templates through a bilingual conversational interface. The system combines Retrieval-Augmented Generation (RAG) with ChromaDB, LangChain, and Groq GPT OSS to provide accurate document retrieval while preserving official document templates for download and customization.

## Features

* AI-powered legal document retrieval using RAG.

* Bilingual support (English and Hindi).

* Speech-to-Text using Groq Whisper API.

* Dynamic document generation with auto-filled DOCX templates.

* Download Blank Template or Fill & Download functionality.

* Semantic search using ChromaDB.

* Fuzzy matching for Hindi, Roman Hindi, and spelling variations.

* Responsive chat interface built with HTML, CSS, and JavaScript.

* Temporary audio handling for voice input.

## Supported Documents

* Affidavit

* General Legal Notice

* Legal Notice for Non-Payment of Dues

* Rent Agreement

* Leave and License Agreement

* Certificate of Taxation

* Writ of Commission

## Tech Stack

|
Category

|

Technology

|
| --- | --- |
|

Backend

|

Python, Flask

|
|

Frontend

|

HTML, CSS, JavaScript (ES6)

|
|

LLM

|

Groq GPT OSS

|
|

Speech-to-Text

|

Groq Whisper API (`whisper-large-v3-turbo`)

|
|

RAG Framework

|

LangChain

|
|

Vector Database

|

ChromaDB

|
|

Embedding Model

|

BAAI/bge-small-en-v1.5

|
|

Similarity Matching

|

RapidFuzz

|
|

Document Generation

|

python-docx

|
|

Environment Management

|

python-dotenv

|

## Project Structure

```
Legal-Document-Generator/
│
├── app.py
├── create_database.py
├── requirements.txt
├── .env
│
├── config/
│   └── config.py
│
├── routes/
│   ├── chatbot.py
│   ├── documents.py
│   ├── forms.py
│   └── voice.py
│
├── rag/
│   ├── rag_chain.py
│   ├── rag_utils.py
│   └── prompts.py
│
├── voice/
│   └── whisper_service.py
│
├── metadata/
│   └── metadata.py
│
├── data/
│   ├── metadata/
│   ├── templates/
│   └── original/
│
├── database/
│   └── chroma/
│
├── generated/
│   ├── blank/
│   └── filled/
│
├── static/
│   ├── css/
│   └── js/
│
└── templates/
    ├── chat.html
    ├── form.html
    └── result.html
```

## How It Works

### Text Query Workflow

1. User submits a query in English, Hindi, or Roman Hindi.

2. The query is normalized using alias matching and fuzzy correction.

3. ChromaDB retrieves the most relevant legal document.

4. Groq GPT OSS generates a short response in the selected language.

5. Users can download the original template or generate a filled document.

### Voice Query Workflow

1. User starts recording from the chat interface.

2. Recording stops manually using the Stop button.

3. Audio is sent to the Groq Whisper API.

4. The transcript is processed through the RAG pipeline.

5. The temporary audio file is deleted after transcription.

6. The chatbot responds in the selected language.

## Installation

### 1. Clone the Repository

Bash

```
git clone https://github.com/your-username/legal-document-generator.git
cd legal-document-generator
```

### 2. Create a Virtual Environment

Bash

```
python -m venv venv
```

Activate it.

Windows

Bash

```
venv\Scripts\activate
```

### 3. Install Dependencies

Bash

```
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

env

```
GROQ_API_KEY=your_groq_api_key
```

## Create the Chroma Database

Run this once after adding or modifying metadata or document templates.

Bash

```
python create_database.py
```

## Run the Application

Bash

```
python app.py
```

Open the application in your browser.

```
http://127.0.0.1:5000
```

## Example Queries

### English

* Give me the format of Affidavit.

* I need a Rent Agreement.

* Send me a General Legal Notice.

* I need a Writ of Commission.

### Hindi

* मुझे शपथ पत्र चाहिए।

* मुझे रेंट एग्रीमेंट का फॉर्मेट भेज दो।

* मुझे टैक्स प्रमाणपत्र चाहिए।

* मुझे कानूनी नोटिस चाहिए।

### Roman Hindi

* mujhe affidavit chahiye

* mujhe rent agreement ka format bhej do

* mujhe writ of commission chahiye

* mujhe legal notice chahiye

## Deployment

This project can be deployed on platforms such as Render.

### Required Environment Variable

env

```
GROQ_API_KEY=your_groq_api_key
```

## License

This project is developed for educational and research purposes.
