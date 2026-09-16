/* ============================================================
   LEGAL DOCUMENT CHAT
============================================================ */
const CHAT_HISTORY_KEY = "legal_document_chat_history";
/* ============================================================
   SEND QUESTION
============================================================ */
async function sendQuestion() {
    const input = document.getElementById("question");
    const chat = document.getElementById("chat");
    const sendBtn = document.getElementById("sendBtn");
    if (!input || !chat) {
        return;
    }
    const question = input.value.trim();
    const language = document.getElementById("language").value;
    if (!question) {
        return;
    }
    /* --------------------------------------------------------
       Disable button
    -------------------------------------------------------- */
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.textContent = "Searching...";
    }
    /* --------------------------------------------------------
       User message
    -------------------------------------------------------- */
    const userMessage = document.createElement("div");
    userMessage.className = "message user-message";
    userMessage.textContent = question;
    chat.appendChild(userMessage);
    input.value = "";
    /* --------------------------------------------------------
       Loading message
    -------------------------------------------------------- */
    const loading = document.createElement("div");
    loading.className = "message bot-message";
    loading.textContent = "Searching legal document knowledge base...";
    chat.appendChild(loading);
    scrollChat();
    try {
        /* ----------------------------------------------------
           Call backend
        ---------------------------------------------------- */
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question,
                    language: language
                })
            });
        const data = await response.json();
        loading.remove();
        /* ----------------------------------------------------
           Backend error
        ---------------------------------------------------- */
        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to search the legal document knowledge base."
            );
        }
        /* ----------------------------------------------------
           Bot response
        ---------------------------------------------------- */
        const botMessage = document.createElement("div");
        botMessage.className = "message bot-message";
        botMessage.innerHTML = `
            <p>
                ${escapeHtml(data.answer || "")}
            </p>
        `;
        chat.appendChild(botMessage);
        /* ----------------------------------------------------
           Get retrieved template
        ---------------------------------------------------- */
        let template = null;
        if (data.template && data.template.template_id) {
            template = data.template;
        } else if (
            data.templates &&
            Array.isArray(data.templates) &&
            data.templates.length > 0
        ) {
            template = data.templates[0];
        }
        /* ----------------------------------------------------
           Display template
        ---------------------------------------------------- */
        if (template && template.template_id
        ) {
            displayTemplate(template);
        }
        saveChatHistory();
        scrollChat();
    } catch (error) {
        if (loading && loading.parentNode
        ) {
            loading.remove();
        }
        const errorMessage = document.createElement("div");
        errorMessage.className = "message bot-message error";
        errorMessage.textContent = error.message || "Unable to process your request.";
        chat.appendChild(errorMessage);
        saveChatHistory();
        scrollChat();
    } finally {
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.textContent = "Send";
        }
        input.focus();
    }
}
/* ============================================================
   DISPLAY TEMPLATE
============================================================ */

/* ============================================================
   DISPLAY TEMPLATE
============================================================ */
function displayTemplate(template) {
    const chat = document.getElementById("chat");
    if (!chat) {
        return;
    }
    const templateBox = document.createElement("div");
    templateBox.className = "template-result";
    const templateId = escapeHtml(template.template_id);
    const documentName = escapeHtml(
        template.document_name || "Legal Document"
    );
    templateBox.innerHTML = `
        <div class="document-found-title">
            <strong>This is the document I found</strong>
        </div>
        <h3>${documentName}</h3>
        <div class="document-actions">
            <button
                type="button"
                class="secondary-btn"
                onclick="downloadBlank('${templateId}')"
            >
                Download Blank
            </button>
            <button
                type="button"
                class="primary-btn"
                onclick="openForm('${templateId}')"
            >
                Fill & Download
            </button>
        </div>
    `;
    chat.appendChild(templateBox);
    scrollChat();
}
/* ============================================================
   OPEN DYNAMIC FORM
============================================================ */
function openForm(templateId) {
    if (!templateId) {
        alert("Template ID is missing.");
        return;
    }
    window.location.href =
        `/form-page/${encodeURIComponent(templateId)}`;
}
/* ============================================================
   DOWNLOAD BLANK DOCUMENT
============================================================ */

// async function downloadBlank(templateId) {

//     if (!templateId) {

//         alert("Template ID is missing.");

//         return;
//     }


//     try {

//         const response =
//             await fetch("/api/documents/blank", {

//                 method: "POST",

//                 headers: {
//                     "Content-Type":
//                         "application/json"
//                 },

//                 body: JSON.stringify({

//                     template_id:
//                         templateId

//                 })

//             });


//         const data =
//             await response.json();


//         if (!response.ok) {

//             throw new Error(
//                 data.error ||
//                 "Unable to generate blank document."
//             );

//         }


//         if (!data.filename) {

//             throw new Error(
//                 "Server did not return a filename."
//             );

//         }


//        window.location.href =
//     `/api/documents/download?filename=${encodeURIComponent(
//         data.filename
//     )}`;


//     } catch (error) {

//         alert(
//             error.message ||
//             "Unable to download document."
//         );

//     }
// }


async function downloadBlank(templateId) {
    if (!templateId) {
        alert("Template ID is missing.");
        return;
    }
    try {
        const response = await fetch(
            "/generate/blank",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    template_id: templateId
                })
            }
        );
        const data = await response.json();
        console.log("Blank document response:",data);
        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to generate blank document."
            );
        }
        if (!data.filename) {
            throw new Error(
                "Server did not return a filename."
            );
        }
        window.location.href =
            `/api/documents/download?filename=${encodeURIComponent(
                data.filename
            )}`;
    }
    catch (error) {
        console.error("Blank document error:",error);
        alert(error.message || "Unable to download blank document.");
    }
}
/* ============================================================
   SAVE CHAT HISTORY
============================================================ */
function saveChatHistory() {
    const chat = document.getElementById("chat");
    if (!chat) {
        return;
    }
    try {
        localStorage.setItem(
            CHAT_HISTORY_KEY,
            chat.innerHTML
        );
    } catch (error) {
        console.error(
            "Unable to save chat history:",
            error
        );
    }
}
/* ============================================================
   RESTORE CHAT HISTORY
============================================================ */
function restoreChatHistory() {
    const chat = document.getElementById("chat");
    if (!chat) {
        return;
    }
    try {
        const savedHistory =
            localStorage.getItem(
                CHAT_HISTORY_KEY
            );
        if (
            savedHistory &&
            savedHistory.trim() !== ""
        ) {
            chat.innerHTML =
                savedHistory;
        }
        scrollChat();
    } catch (error) {
        console.error(
            "Unable to restore chat history:",
            error
        );
    }
}
/* ============================================================
   CLEAR CHAT
============================================================ */
function clearChat() {
    const confirmed =
        confirm("Are you sure you want to clear this chat?");
    if (!confirmed) {
        return;
    }
    localStorage.removeItem(CHAT_HISTORY_KEY);
    const chat = document.getElementById("chat");
    if (!chat) {
        return;
    }
    chat.innerHTML = `
        <div class="message bot-message">
            Hello! I am your
            <strong>Legal Document Assistant</strong>.
            <br><br>
            You can ask me for legal documents such as:
            <ul>
                <li>Affidavit</li>
                <li>General Legal Notice</li>
                <li>Leave and License Agreement</li>
                <li>Non-Payment Notice</li>
            </ul>
            Ask me which document you need.
        </div>
    `;
    scrollChat();
}
/* ============================================================
   NEW CHAT
============================================================ */

// function newChat() {

//     const confirmed =
//         confirm(
//             "Start a new chat? Your current chat history will be cleared."
//         );


//     if (!confirmed) {
//         return;
//     }


//     localStorage.removeItem(
//         CHAT_HISTORY_KEY
//     );


//     window.location.href =
//         "/chat-page";
// }





function startNewChat() {
    const confirmed = confirm("Start a new chat? Your current chat history will be cleared.");
    if (!confirmed) {
        return;
    }
    // Clear saved chat history
    localStorage.removeItem(CHAT_HISTORY_KEY);
    // Get chat container
    const chat = document.getElementById("chat");
    if (chat) {
        chat.innerHTML = `
            <div class="message bot-message">
                <strong>
                    Hello! I am your Legal Document Assistant.
                </strong>
                <br><br>
                You can ask me for documents such as:
                <ul>
                    <li>Affidavit</li>
                    <li>General Legal Notice</li>
                    <li>Leave and License Agreement</li>
                    <li>Non-Payment Notice</li>
                    <li>Rent Agreement</li>
                </ul>
                Ask me which document you need.
            </div>
        `;
    }
    // Clear input
    const input = document.getElementById("question");
    if (input) {
        input.value = "";
        input.focus();
    }
    scrollChat();
}

/* ============================================================
   SCROLL CHAT
============================================================ */
function scrollChat() {
    const chat = document.getElementById("chat");
    if (!chat) {
        return;
    }
    chat.scrollTop =
        chat.scrollHeight;
}
/* ============================================================
   ESCAPE HTML
============================================================ */
function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
}
/* ============================================================
   PAGE LOAD
============================================================ */
document.addEventListener(
    "DOMContentLoaded",
    function () {
        restoreChatHistory();
        const input = document.getElementById("question");
        if (input) {
            input.addEventListener(
                "keydown",
                function (event) {
                    if (
                        event.key === "Enter" &&
                        !event.shiftKey
                    ) {
                        event.preventDefault();
                        sendQuestion();
                    }
                }
            );
        }
    }
);