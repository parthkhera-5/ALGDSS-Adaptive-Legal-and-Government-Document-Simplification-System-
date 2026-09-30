```mermaid
flowchart TD
    classDef startEnd fill:#2E7D32,color:#fff,stroke:#1B5E20,stroke-width:2px;
    classDef decision fill:#EF6C00,color:#fff,stroke:#E65100,stroke-width:2px;
    classDef process fill:#1565C0,color:#fff,stroke:#0D47A1,stroke-width:1px;
    classDef llmNode fill:#7B1FA2,color:#fff,stroke:#4A148C,stroke-width:2px;

    %% STAGE 1: FRONTEND & INPUT PIPELINE
    START([START: User Access via Flask Interface]) :::startEnd
    START --> InputType{Input Type?} :::decision
    
    InputType -->|Voice| STT[Speech-to-Text STT] :::process
    InputType -->|Text| DirectText[Direct Text Processing] :::process
    
    STT --> LangCheck{Select Language} :::decision
    DirectText --> LangCheck
    
    LangCheck -->|Hindi| TransIn[Translate Hindi to English] :::process
    LangCheck -->|English| NormText[Normalize & Clean Text RapidFuzz] :::process
    TransIn --> NormText

    %% STAGE 2: MODULE SELECTION
    NormText --> SelectModule{Select Module} :::decision

    %% MODULE 1: LEGAL AI
    SelectModule -->|Module 1: Legal AI| UploadDoc[Upload Document PDF/DOCX/TXT] :::process
    UploadDoc --> DocSize{Document Size?} :::decision
    DocSize -->|Large| EmbedDoc[Embed BAAI/bge-en-v1.5 & Index FAISS] :::process
    DocSize -->|Small| FullText[Extract Full Raw Context] :::process
    
    EmbedDoc --> QueryExp[Query Expansion: 3 Alternate Queries] :::process
    FullText --> QueryExp
    
    QueryExp --> RouteCheck{Determine Route} :::decision
    RouteCheck -->|DOCUMENT| DocSearch[Search Uploaded Document FAISS] :::process
    RouteCheck -->|KNOWLEDGE| LegalSearch[Search Legal Knowledge FAISS] :::process
    RouteCheck -->|BOTH| BothSearch[Search Doc + Legal Knowledge FAISS] :::process

    DocSearch --> Rerank[Cross-Encoder Reranking ms-marco-MiniLM-L-6-v2] :::process
    LegalSearch --> Rerank
    BothSearch --> Rerank

    Rerank --> FilterCtx[Context Selection & Filtering] :::process
    FilterCtx --> ConstructPrompt[Build Task-Specific Prompt] :::process

    %% MODULE 2: LEGAL NOTICE GENERATOR
    SelectModule -->|Module 2: Legal Notice Generator| SearchTmpl[Embed Query BAAI/bge-small-en-v1.5] :::process
    SearchTmpl --> ChromaSearch[Semantic Search ChromaDB Templates] :::process
    ChromaSearch --> TmplThresh{Template Found above Threshold?} :::decision
    
    TmplThresh -->|NO| NoTmpl[Return Document Not Available Message] :::process
    NoTmpl --> END([END]) :::startEnd

    TmplThresh -->|YES| ModeCheck{Select Action} :::decision
    ModeCheck -->|Download Blank| BlankDoc[Replace Placeholders with Blank & Save DOCX] :::process
    BlankDoc --> DownloadDirect[Download Blank Template] :::process
    DownloadDirect --> END

    ModeCheck -->|Fill & Download| DynamicForm[Display Dynamic Form & Collect Details] :::process
    DynamicForm --> FillDoc[Generate Filled DOCX Document] :::process
    FillDoc --> GroundedPrompt[Build Prompt Grounded in Template Data] :::process

    %% MODULE 3: GOVERNMENT SCHEME RECOMMENDATION
    SelectModule -->|Module 3: Govt Scheme| IntentHistory[Parse Intent & Fetch History Mem0/Qdrant] :::process
    IntentHistory --> SchemeEmbed[Embed Query BAAI/bge-en-v1.5] :::process
    SchemeEmbed --> SchemeFAISS[Search Scheme FAISS Vector DB] :::process
    SchemeFAISS --> ConfCheck{Similarity Score >= Threshold?} :::decision
    
    ConfCheck -->|NO| WebSearch[Web Search Official Govt Sites & Scrape] :::process
    ConfCheck -->|YES| LocalMatch[Extract Scheme Chunks] :::process

    WebSearch --> UserDemographics[Collect Demographic Profile Data] :::process
    LocalMatch --> UserDemographics

    UserDemographics --> RuleMatrix[Apply Rule-Based Eligibility Filter Matrix] :::process
    RuleMatrix --> PriorityRank[Score & Rank Schemes Home State First] :::process
    PriorityRank --> SchemePrompt[Build Prompt with Profile + Ranked Schemes] :::process

    %% STAGE 3: SHARED CENTRAL LLM ENGINE
    ConstructPrompt --> UnifiedLLM[Central LLM Engine: openai/gpt-oss-120b] :::llmNode
    GroundedPrompt --> UnifiedLLM
    SchemePrompt --> UnifiedLLM

    %% STAGE 4: OUTPUT & INTERACTION LAYER
    UnifiedLLM --> JSONResp[Generate Response in JSON Format] :::process
    JSONResp --> TargetLang{User Target Language?} :::decision
    
    TargetLang -->|Hindi| TransOut[Translate Response to Hindi] :::process
    TargetLang -->|English| RenderUI[Render Response on Flask Interface] :::process
    TransOut --> RenderUI

    RenderUI --> VoiceOut{Voice Output Enabled?} :::decision
    VoiceOut -->|YES| TTS[Execute Text-to-Speech TTS] :::process
    VoiceOut -->|NO| SaveMem[Update Conversation Memory Mem0/Qdrant] :::process
    TTS --> SaveMem

    SaveMem --> Continue{Start New Request?} :::decision
    Continue -->|YES| SelectModule
    Continue -->|NO| END
```


