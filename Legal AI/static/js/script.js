// ============================================================
// STATE
// ============================================================

let selectedOperation = "DOCUMENT_QA";
let documentLoaded = false;
let isProcessing = false;


// ============================================================
// ELEMENTS
// ============================================================

const fileInput =
    document.getElementById("fileInput");

const chooseFileBtn =
    document.getElementById("chooseFileBtn");

const uploadBox =
    document.getElementById("uploadBox");

const documentInfo =
    document.getElementById("documentInfo");

const fileName =
    document.getElementById("fileName");

const fileStatus =
    document.getElementById("fileStatus");

const removeFileBtn =
    document.getElementById("removeFileBtn");

const statusDot =
    document.getElementById("statusDot");

const statusText =
    document.getElementById("statusText");

const queryInput =
    document.getElementById("queryInput");

const sendBtn =
    document.getElementById("sendBtn");

const micBtn =
    document.getElementById("micBtn");

const messages =
    document.getElementById("messages");

const languageSelect =
    document.getElementById("languageSelect");

const welcome =
    document.getElementById("welcome");

const operationCards =
    document.querySelectorAll(".operation-card");


// ============================================================
// TEXTAREA AUTO RESIZE
// ============================================================

queryInput.addEventListener(
    "input",
    () => {

        queryInput.style.height =
            "auto";

        queryInput.style.height =
            Math.min(
                queryInput.scrollHeight,
                120
            ) + "px";

    }
);



// ============================================================
// SPEECH TO TEXT
// Browser Microphone → Flask → Groq Whisper → Text
// ============================================================

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;


// ============================================================
// MICROPHONE BUTTON
// ============================================================

micBtn.addEventListener(
    "click",
    toggleRecording
);


// ============================================================
// START / STOP RECORDING
// ============================================================

async function toggleRecording() {

    // --------------------------------------------------------
    // STOP RECORDING
    // --------------------------------------------------------

    if (isRecording) {

        stopRecording();

        return;

    }


    // --------------------------------------------------------
    // START RECORDING
    // --------------------------------------------------------

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });


        audioChunks = [];


        mediaRecorder =
            new MediaRecorder(
                stream,
                {
                    mimeType: "audio/webm"
                }
            );


        // ----------------------------------------------------
        // Collect audio data
        // ----------------------------------------------------

        mediaRecorder.addEventListener(
            "dataavailable",
            (event) => {

                if (
                    event.data.size > 0
                ) {

                    audioChunks.push(
                        event.data
                    );

                }

            }
        );


        // ----------------------------------------------------
        // Recording stopped
        // ----------------------------------------------------

        mediaRecorder.addEventListener(
            "stop",
            async () => {

                // Stop microphone
                stream
                    .getTracks()
                    .forEach(
                        track => track.stop()
                    );


                const audioBlob =
                    new Blob(
                        audioChunks,
                        {
                            type: "audio/webm"
                        }
                    );


                await sendAudioToGroq(
                    audioBlob
                );

            }
        );


        // ----------------------------------------------------
        // Start recording
        // ----------------------------------------------------

        mediaRecorder.start();

        isRecording = true;


        micBtn.textContent =
            "⏹";

        micBtn.title =
            "Stop recording";

        micBtn.classList.add(
            "recording"
        );


        queryInput.placeholder =
            "Listening... Speak now";


    } catch (error) {

        console.error(
            "Microphone error:",
            error
        );


        if (
            error.name ===
            "NotAllowedError"
        ) {

            alert(
                "Microphone permission was denied. " +
                "Please allow microphone access."
            );

        } else {

            alert(
                "Unable to access the microphone: " +
                error.message
            );

        }

    }

}


// ============================================================
// STOP RECORDING
// ============================================================

function stopRecording() {

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        mediaRecorder.stop();

    }


    isRecording = false;


    micBtn.textContent =
        "⏳";

    micBtn.title =
        "Transcribing...";

    micBtn.disabled =
        true;

    micBtn.classList.remove(
        "recording"
    );


    queryInput.placeholder =
        "Transcribing speech...";

}


// ============================================================
// SEND AUDIO TO FLASK
// ============================================================

async function sendAudioToGroq(
    audioBlob
) {

    try {

        const formData =
            new FormData();


        // ----------------------------------------------------
        // Add audio
        // ----------------------------------------------------

        formData.append(
            "audio",
            audioBlob,
            "recording.webm"
        );


        // ----------------------------------------------------
        // Add selected language
        // ----------------------------------------------------

        const selectedLanguage =
            languageSelect
                ? languageSelect.value
                : "en";


        /*
         * IMPORTANT:
         *
         * For now we send the selected language.
         *
         * English → "en"
         * Hindi   → "hi"
         *
         * If you want automatic detection for
         * Hinglish, we can send an empty value later.
         */

        formData.append(
            "language",
            selectedLanguage
        );


        // ----------------------------------------------------
        // Send to Flask
        // ----------------------------------------------------

        const response =
            await fetch(
                "/speech-to-text",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        // ----------------------------------------------------
        // Check response
        // ----------------------------------------------------

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Speech-to-text failed."
            );

        }


        // ----------------------------------------------------
        // Get transcription
        // ----------------------------------------------------

        const text =
            (data.text || "").trim();


        if (!text) {

            throw new Error(
                "No speech detected."
            );

        }


        // ----------------------------------------------------
        // Put transcription in input
        // ----------------------------------------------------

        queryInput.value =
            text;


        // ----------------------------------------------------
        // Resize textarea
        // ----------------------------------------------------

        queryInput.style.height =
            "auto";

        queryInput.style.height =
            Math.min(
                queryInput.scrollHeight,
                120
            ) + "px";


        // ----------------------------------------------------
        // Reset microphone
        // ----------------------------------------------------

        micBtn.textContent =
            "🎤";

        micBtn.title =
            "Speak";

        micBtn.disabled =
            false;


        queryInput.placeholder =
            "Ask something about your document...";


        // ----------------------------------------------------
        // Focus input
        // ----------------------------------------------------

        queryInput.focus();


    } catch (error) {

        console.error(
            "Speech-to-text error:",
            error
        );


        alert(
            "Unable to transcribe speech: " +
            error.message
        );


        // ----------------------------------------------------
        // Reset microphone
        // ----------------------------------------------------

        micBtn.textContent =
            "🎤";

        micBtn.title =
            "Speak";

        micBtn.disabled =
            false;


        queryInput.placeholder =
            "Ask something about your document...";

    }

}





// ============================================================
// FILE SELECTION
// ============================================================

chooseFileBtn.addEventListener(
    "click",
    () => {

        fileInput.click();

    }
);


fileInput.addEventListener(
    "change",
    () => {

        if (fileInput.files.length > 0) {

            uploadDocument(
                fileInput.files[0]
            );

        }

    }
);


// ============================================================
// DRAG & DROP
// ============================================================

uploadBox.addEventListener(
    "dragover",
    (event) => {

        event.preventDefault();

        uploadBox.classList.add(
            "dragover"
        );

    }
);


uploadBox.addEventListener(
    "dragleave",
    () => {

        uploadBox.classList.remove(
            "dragover"
        );

    }
);


uploadBox.addEventListener(
    "drop",
    (event) => {

        event.preventDefault();

        uploadBox.classList.remove(
            "dragover"
        );

        const files =
            event.dataTransfer.files;

        if (files.length > 0) {

            uploadDocument(
                files[0]
            );

        }

    }
);


// ============================================================
// UPLOAD DOCUMENT
// ============================================================

async function uploadDocument(file) {

    const extension =
        file.name
            .split(".")
            .pop()
            .toLowerCase();


    if (
        extension !== "pdf" &&
        extension !== "docx"
    ) {

        alert(
            "Please upload a PDF or DOCX file."
        );

        return;

    }


    // Display file

    uploadBox.classList.add(
        "hidden"
    );

    documentInfo.classList.remove(
        "hidden"
    );

    fileName.textContent =
        file.name;

    fileStatus.textContent =
        "Processing document...";

    statusText.textContent =
        "Processing document...";

    statusDot.classList.remove(
        "loaded"
    );


    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    try {

        const response =
            await fetch(
                "/upload",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Document upload failed."
            );

        }


        // Success

        documentLoaded = true;
        updatePlaceholder();

        fileStatus.textContent =
            `${data.records} document records loaded`;

        statusText.textContent =
            "Document loaded";

        statusDot.classList.add(
            "loaded"
        );


        welcome.classList.add(
            "hidden"
        );


        addAssistantMessage(
            "Your document has been loaded successfully. What would you like me to analyze?"
        );


    } catch (error) {

        console.error(error);

        fileStatus.textContent =
            "Upload failed";

        statusText.textContent =
            "Upload failed";

        alert(
            error.message
        );

    }

}


// ============================================================
// REMOVE DOCUMENT
// ============================================================

removeFileBtn.addEventListener(
    "click",
    () => {

        documentLoaded = false;
        updatePlaceholder();

        fileInput.value = "";

        documentInfo.classList.add(
            "hidden"
        );

        uploadBox.classList.remove(
            "hidden"
        );

        statusDot.classList.remove(
            "loaded"
        );

        statusText.textContent =
            "No document loaded";

        messages.innerHTML = "";

        welcome.classList.remove(
            "hidden"
        );

    }
);


// ============================================================
// OPERATION SELECTION
// ============================================================

operationCards.forEach(
    (card) => {

        card.addEventListener(
            "click",
            () => {

                operationCards.forEach(
                    (item) => {

                        item.classList.remove(
                            "active"
                        );

                    }
                );


                card.classList.add(
                    "active"
                );


                selectedOperation =
                    card.dataset.operation;


                updatePlaceholder();

            }
        );

    }
);


// ============================================================
// PLACEHOLDER
// ============================================================
function updatePlaceholder() {

    const placeholders = {

        "DOCUMENT_QA":
            documentLoaded
                ? "Ask something about your document..."
                : "Ask a general legal question...",

        "SUMMARY":
            documentLoaded
                ? "Ask for a summary or leave your request empty..."
                : "Upload a document to generate a summary...",

        "RISK_DETECTION":
            "Ask about risks in the agreement...",

        "CLAUSE_EXPLANATION":
            "Which clause would you like explained?",

        "LEGAL_VALIDATION":
            "What would you like to validate?"

    };


    queryInput.placeholder =
        placeholders[selectedOperation] ||
        "Ask a legal question...";

}

// ============================================================
// SEND MESSAGE
// ============================================================

sendBtn.addEventListener(
    "click",
    sendMessage
);


queryInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();

        }

    }
);


// ============================================================
// SEND MESSAGE FUNCTION
// ============================================================

async function sendMessage() {

    if (isProcessing) {
        return;
    }


    // if (!documentLoaded) {

    //     alert(
    //         "Please upload a document first."
    //     );

    //     return;

    // }


    const query =
        queryInput.value.trim();


    // Summary can potentially work without
    // a user query.

    if (
        !query &&
        selectedOperation !== "SUMMARY"
    ) {

        alert(
            "Please enter a question."
        );

        return;

    }


     // Summary without a document is not allowed.

    if (
        selectedOperation === "SUMMARY" &&
        !documentLoaded
    ) {

        alert(
            "Please upload a document before requesting a summary."
        );

        return;

    }



    const displayQuery =
        query ||
        "Summarize this document.";


    // Add user message

    addUserMessage(
        displayQuery
    );


    queryInput.value = "";

    queryInput.style.height = "auto";

    isProcessing = true;

    sendBtn.disabled = true;


    const loadingMessage =
        addLoadingMessage();


    try {

        const response =
            await fetch(
                "/chat",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        query:
                            displayQuery,

                        operation:
                            selectedOperation,

                        language:
                            languageSelect.value

                    })

                }
            );


        const data =
            await response.json();


        loadingMessage.remove();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Something went wrong."
            );

        }


        displayResult(
            data
        );


    } catch (error) {

        console.error(error);

        loadingMessage.remove();

        addAssistantMessage(
            `Error: ${error.message}`
        );

    } finally {

        isProcessing = false;

        sendBtn.disabled = false;

        queryInput.focus();

    }

}


// ============================================================
// ADD USER MESSAGE
// ============================================================

function addUserMessage(text) {

    const message =
        document.createElement("div");

    message.className =
        "message user";


    const content =
        document.createElement("div");

    content.className =
        "message-content";


    content.textContent =
        text;


    message.appendChild(
        content
    );


    messages.appendChild(
        message
    );


    requestAnimationFrame(() => {
        scrollToBottom();
    });

}
// ============================================================
// ADD ASSISTANT MESSAGE
// ============================================================

function addAssistantMessage(text) {

    const message =
        document.createElement("div");

    message.className =
        "message assistant";


    const content =
        document.createElement("div");

    content.className =
        "message-content";


    content.textContent =
        text;


    message.appendChild(
        content
    );


    messages.appendChild(
        message
    );


    requestAnimationFrame(() => {
        scrollToBottom();
    });

}

// ============================================================
// LOADING MESSAGE
// ============================================================

function addLoadingMessage() {

    const message =
        document.createElement("div");

    message.className =
        "message assistant";


    const content =
        document.createElement("div");

    content.className =
        "message-content loading";


    content.innerHTML = `
        <span>Analyzing</span>
        <span class="loading-dot"></span>
        <span class="loading-dot"></span>
        <span class="loading-dot"></span>
    `;


    message.appendChild(
        content
    );


    messages.appendChild(
        message
    );


    requestAnimationFrame(() => {
        scrollToBottom();
    });


    return message;
}

// // ============================================================
// // DISPLAY RESULT
// // ============================================================

// ============================================================
// DISPLAY RESULT
// ============================================================

function displayResult(data) {

    const message =
        document.createElement("div");

    let speechText = "";

    message.className =
        "message assistant";


    const content =
        document.createElement("div");

    content.className =
        "message-content legal-response";


    // ========================================================
    // STRUCTURED RESPONSE
    // ========================================================

    if (
        data.answer &&
        Array.isArray(data.answer.content)
    ) {

        data.answer.content.forEach((item) => {

            // =================================================
            // HEADING
            // =================================================

            if (
                item.type === "heading"
            ) {

                const heading =
                    document.createElement("h3");

                heading.className =
                    "result-heading";

                heading.textContent =
                    item.text || "";

                content.appendChild(
                    heading
                );

                speechText +=
                    (item.text || "") + ". ";

            }


            // =================================================
            // PARAGRAPH
            // =================================================

            else if (
                item.type === "paragraph"
            ) {

                const paragraph =
                    document.createElement("p");

                paragraph.className =
                    "result-paragraph";

                paragraph.textContent =
                    item.text || "";

                content.appendChild(
                    paragraph
                );

                speechText +=
                    (item.text || "") + " ";

            }


            // =================================================
            // BULLET LIST
            // =================================================

            else if (
                item.type === "bullet_list"
            ) {

                const list =
                    document.createElement("ul");

                list.className =
                    "result-list";


                if (
                    Array.isArray(item.items)
                ) {

                    item.items.forEach((originalText) => {

                        const li =
                            document.createElement("li");


                        // -------------------------------------
                        // RISK DETECTION SPECIAL FORMAT
                        // -------------------------------------

                        if (
                            selectedOperation === "RISK_DETECTION" &&
                            typeof originalText === "string"
                        ) {

                            let text =
                                originalText.replace(
                                    /\*\*/g,
                                    ""
                                );


                            // Split BEFORE Risk / Affected party /
                            // Consequence labels
                            const parts =
                                text.split(
                                    /(?=(?:Risk|Affected party|Consequence):)/i
                                );


                            parts.forEach((part) => {

                                part =
                                    part.trim();


                                if (!part) {
                                    return;
                                }


                                const match =
                                    part.match(
                                        /^(Risk|Affected party|Consequence):\s*(.*)$/is
                                    );


                                if (match) {

                                    const label =
                                        document.createElement("strong");

                                    label.className =
                                        "risk-label";

                                    label.textContent =
                                        match[1] + ":";


                                    const value =
                                        document.createElement("span");

                                    value.className =
                                        "risk-value";

                                    value.textContent =
                                        match[2].trim();


                                    const block =
                                        document.createElement("div");

                                    block.className =
                                        "risk-detail";


                                    block.appendChild(
                                        label
                                    );

                                    block.appendChild(
                                        document.createElement("br")
                                    );

                                    block.appendChild(
                                        value
                                    );


                                    li.appendChild(
                                        block
                                    );


                                    // Add to speech text
                                    speechText +=
                                        match[1] +
                                        ". " +
                                        match[2].trim() +
                                        ". ";

                                }


                                else {

                                    const intro =
                                        document.createElement("div");

                                    intro.className =
                                        "risk-description";

                                    intro.textContent =
                                        part;


                                    li.appendChild(
                                        intro
                                    );


                                    speechText +=
                                        part + ". ";

                                }

                            });

                        }


                        // -------------------------------------
                        // NORMAL BULLET
                        // -------------------------------------

                        else {

                            li.textContent =
                                originalText;

                            speechText +=
                                originalText + ". ";

                        }


                        list.appendChild(
                            li
                        );

                    });

                }


                content.appendChild(
                    list
                );

            }


            // =================================================
            // NUMBERED LIST
            // =================================================

            else if (
                item.type === "numbered_list"
            ) {

                const list =
                    document.createElement("ol");

                list.className =
                    "result-list numbered";


                if (
                    Array.isArray(item.items)
                ) {

                    item.items.forEach(
                        (text) => {

                            const li =
                                document.createElement("li");

                            li.textContent =
                                text;

                            list.appendChild(
                                li
                            );


                            // Add numbered list text to TTS
                            speechText +=
                                text + ". ";

                        }
                    );

                }


                content.appendChild(
                    list
                );

            }


            // =================================================
            // WARNING
            // =================================================

            else if (
                item.type === "warning"
            ) {

                const warning =
                    document.createElement("div");

                warning.className =
                    "result-warning";

                warning.textContent =
                    item.text || "";

                content.appendChild(
                    warning
                );

                speechText +=
                    "Warning. " +
                    (item.text || "") +
                    " ";

            }


            // =================================================
            // UNKNOWN TYPE
            // =================================================

            else {

                console.warn(
                    "Unknown response content type:",
                    item.type,
                    item
                );

            }

        });

    }


    // ========================================================
    // STRING FALLBACK
    // ========================================================

    else if (
        data.answer &&
        typeof data.answer === "string"
    ) {

        const paragraph =
            document.createElement("p");

        paragraph.className =
            "result-paragraph";

        paragraph.textContent =
            data.answer;

        content.appendChild(
            paragraph
        );


        speechText =
            data.answer;

    }


    // ========================================================
    // EMPTY RESPONSE
    // ========================================================

    else {

        const paragraph =
            document.createElement("p");

        paragraph.className =
            "result-paragraph";

        paragraph.textContent =
            "No response content received.";

        content.appendChild(
            paragraph
        );


        speechText =
            "No response content received.";

    }


    // ========================================================
    // TEXT TO SPEECH CONTROLS
    // ========================================================

    if (
        speechText.trim()
    ) {

        // ----------------------------------------------------
        // TTS controls container
        // ----------------------------------------------------

        const ttsControls =
            document.createElement("div");

        ttsControls.className =
            "tts-controls";


        // ----------------------------------------------------
        // Play / Pause button
        // ----------------------------------------------------

        const ttsButton =
            document.createElement("button");

        ttsButton.className =
            "tts-button";

        ttsButton.type =
            "button";

        ttsButton.textContent =
            "🔊";

        ttsButton.title =
            "Listen to response";


        ttsButton.addEventListener(
            "click",
            () => {

                playTextToSpeech(
                    speechText.trim(),
                    ttsButton
                );

            }
        );


        // ----------------------------------------------------
        // Stop button
        // ----------------------------------------------------

        const stopButton =
            document.createElement("button");

        stopButton.className =
            "tts-stop-button";

        stopButton.type =
            "button";

        stopButton.textContent =
            "⏹";

        stopButton.title =
            "Stop";


        stopButton.addEventListener(
            "click",
            () => {

                stopTextToSpeech(
                    ttsButton
                );

            }
        );


        // ----------------------------------------------------
        // Speed selector
        // ----------------------------------------------------

        const speedSelect =
            document.createElement("select");

        speedSelect.className =
            "tts-speed";

        speedSelect.title =
            "Speech speed";


        const speeds = [
            ["0.75", "0.75×"],
            ["1", "1×"],
            ["1.25", "1.25×"],
            ["1.5", "1.5×"],
            ["2", "2×"]
        ];


        speeds.forEach(
            ([value, label]) => {

                const option =
                    document.createElement("option");

                option.value =
                    value;

                option.textContent =
                    label;


                if (
                    value === "1"
                ) {

                    option.selected =
                        true;

                }


                speedSelect.appendChild(
                    option
                );

            }
        );


        speedSelect.addEventListener(
            "change",
            () => {

                changeSpeechSpeed(
                    speedSelect
                );

            }
        );


        // ----------------------------------------------------
        // Add controls
        // ----------------------------------------------------

        ttsControls.appendChild(
            ttsButton
        );

        ttsControls.appendChild(
            stopButton
        );

        ttsControls.appendChild(
            speedSelect
        );


        // ----------------------------------------------------
        // Add after response
        // ----------------------------------------------------

        content.appendChild(
            ttsControls
        );

    }

    // ========================================================
    // ADD MESSAGE
    // ========================================================

    message.appendChild(
        content
    );


    messages.appendChild(
        message
    );


    scrollToBottom();

}


// ============================================================
// TEXT TO SPEECH
// ============================================================

let currentAudio = null;
let currentAudioUrl = null;
let currentTtsButton = null;


// ============================================================
// STOP CURRENT AUDIO
// ============================================================

function stopCurrentAudio() {

    if (currentAudio) {

        currentAudio.pause();

        currentAudio.currentTime = 0;

        currentAudio = null;

    }


    // Revoke old object URL

    if (currentAudioUrl) {

        URL.revokeObjectURL(
            currentAudioUrl
        );

        currentAudioUrl = null;

    }


    // Reset previous button

    if (currentTtsButton) {

        currentTtsButton.textContent =
            "🔊";

        currentTtsButton.title =
            "Listen to response";

        currentTtsButton = null;

    }

}


// ============================================================
// PLAY / PAUSE / RESUME TTS
// ============================================================

async function playTextToSpeech(
    text,
    button
) {

    // --------------------------------------------------------
    // If THIS audio is currently playing
    // --------------------------------------------------------

    if (
        currentAudio &&
        currentTtsButton === button &&
        !currentAudio.paused
    ) {

        currentAudio.pause();

        button.textContent =
            "▶";

        button.title =
            "Resume";

        return;

    }


    // --------------------------------------------------------
    // If THIS audio exists but is paused
    // --------------------------------------------------------

    if (
        currentAudio &&
        currentTtsButton === button &&
        currentAudio.paused
    ) {

        try {

            await currentAudio.play();

            button.textContent =
                "⏸";

            button.title =
                "Pause";

        } catch (error) {

            console.error(
                "TTS Resume Error:",
                error
            );

        }

        return;

    }


    // --------------------------------------------------------
    // Stop any previous audio
    // --------------------------------------------------------

    stopCurrentAudio();


    // --------------------------------------------------------
    // Loading state
    // --------------------------------------------------------

    button.textContent =
        "⏳";

    button.title =
        "Generating speech...";


    try {

        // ----------------------------------------------------
        // Get selected language
        // ----------------------------------------------------

        const language =
            languageSelect
                ? languageSelect.value
                : "en";


        // ----------------------------------------------------
        // Request TTS
        // ----------------------------------------------------

        const response =
            await fetch(
                "/tts",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        text:
                            text,

                        language:
                            language

                    })

                }
            );


        if (!response.ok) {

            let errorMessage =
                "Text-to-speech failed.";

            try {

                const data =
                    await response.json();

                errorMessage =
                    data.error ||
                    errorMessage;

            } catch (e) {

                // Ignore JSON parsing error

            }

            throw new Error(
                errorMessage
            );

        }


        // ----------------------------------------------------
        // Convert response to audio
        // ----------------------------------------------------

        const audioBlob =
            await response.blob();


        const audioUrl =
            URL.createObjectURL(
                audioBlob
            );


        const audio =
            new Audio(
                audioUrl
            );


        // ----------------------------------------------------
        // Store current audio
        // ----------------------------------------------------

        currentAudio =
            audio;

        currentAudioUrl =
            audioUrl;

        currentTtsButton =
            button;


        // ----------------------------------------------------
        // Get selected speed
        // ----------------------------------------------------

        const speedSelect =
            button
                .parentElement
                .querySelector(
                    ".tts-speed"
                );


        if (speedSelect) {

            audio.playbackRate =
                parseFloat(
                    speedSelect.value
                );

        }


        // ----------------------------------------------------
        // Audio ended
        // ----------------------------------------------------

        audio.addEventListener(
            "ended",
            () => {

                button.textContent =
                    "🔊";

                button.title =
                    "Listen to response";


                if (
                    currentAudio === audio
                ) {

                    currentAudio =
                        null;

                    currentTtsButton =
                        null;

                }


                if (
                    currentAudioUrl === audioUrl
                ) {

                    URL.revokeObjectURL(
                        audioUrl
                    );

                    currentAudioUrl =
                        null;

                }

            }
        );


        // ----------------------------------------------------
        // Start playing
        // ----------------------------------------------------

        await audio.play();


        button.textContent =
            "⏸";

        button.title =
            "Pause";


    } catch (error) {

        console.error(
            "TTS Error:",
            error
        );


        button.textContent =
            "🔊";

        button.title =
            "Listen to response";


        if (
            currentAudioUrl
        ) {

            URL.revokeObjectURL(
                currentAudioUrl
            );

        }


        currentAudio =
            null;

        currentAudioUrl =
            null;

        currentTtsButton =
            null;


        alert(
            "Unable to play the response: " +
            error.message
        );

    }

}


// ============================================================
// CHANGE SPEECH SPEED
// ============================================================

function changeSpeechSpeed(
    speedSelect
) {

    if (
        currentAudio &&
        currentTtsButton &&
        currentTtsButton.parentElement
            .contains(speedSelect)
    ) {

        currentAudio.playbackRate =
            parseFloat(
                speedSelect.value
            );

    }

}


// ============================================================
// STOP TTS BUTTON
// ============================================================

function stopTextToSpeech(
    button
) {

    if (
        currentAudio &&
        currentTtsButton ===
            button
    ) {

        stopCurrentAudio();

    }

}

// ============================================================
// SCROLL
// ============================================================

function scrollToBottom() {

    messages.scrollTop =
        messages.scrollHeight;

}


// ============================================================
// INITIALIZE
// ============================================================

updatePlaceholder();