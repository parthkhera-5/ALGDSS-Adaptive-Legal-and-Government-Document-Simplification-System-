// /* ============================================================
//    DYNAMIC LEGAL DOCUMENT FORM
// ============================================================ */


// /* ============================================================
//    LOAD FORM
// ============================================================ */

// // async function loadForm(templateId) {

// //     const container =
// //         document.getElementById("dynamicForm");

// //     const title =
// //         document.getElementById("documentTitle");


// //     if (!templateId) {

// //         container.innerHTML = `
// //             <div class="error-message">
// //                 Template ID is missing.
// //             </div>
// //         `;

// //         return;
// //     }


// //     try {

// //         container.innerHTML = `
// //             <div class="loading">
// //                 Loading document fields...
// //             </div>
// //         `;


// //         /* ----------------------------------------------------
// //            Request metadata for ONLY this template
// //         ---------------------------------------------------- */

// //         const response =
// //             await fetch(
// //                 `/form/${encodeURIComponent(templateId)}`
// //             );


// //         const data =
// //             await response.json();


// //         if (!response.ok) {

// //             throw new Error(
// //                 data.error ||
// //                 "Unable to load form."
// //             );

// //         }


// //         /* ----------------------------------------------------
// //            Document title
// //         ---------------------------------------------------- */

// //         title.textContent =
// //             `Fill ${data.document_name || "Legal Document"}`;


// //         /* ----------------------------------------------------
// //            Clear loading message
// //         ---------------------------------------------------- */

// //         container.innerHTML = "";


// //         /* ----------------------------------------------------
// //            Validate fields
// //         ---------------------------------------------------- */

// //         if (
// //             !data.fields ||
// //             !Array.isArray(data.fields)
// //         ) {

// //             throw new Error(
// //                 "No form fields were returned by the server."
// //             );

// //         }


// //         /* ----------------------------------------------------
// //            Generate fields dynamically
// //         ---------------------------------------------------- */

// //         data.fields.forEach(
// //             function (field) {

// //                 createField(
// //                     container,
// //                     field
// //                 );

// //             }
// //         );


// //         /* ----------------------------------------------------
// //            Store template ID
// //         ---------------------------------------------------- */

// //         document.getElementById(
// //             "templateId"
// //         ).value = templateId;


// //     } catch (error) {

// //         console.error(error);


// //         container.innerHTML = `

// //             <div class="error-message">

// //                 ${escapeHtml(
// //                     error.message ||
// //                     "Unable to load form."
// //                 )}

// //             </div>

// //         `;

// //     }
// // }

// async function loadForm(templateId) {

//     try {

//         if (!templateId) {
//             alert("Template ID is missing.");
//             return;
//         }

//         const response = await fetch(
//             `/form/${encodeURIComponent(templateId)}`
//         );

//         const data = await response.json();

//         if (!response.ok) {
//             alert(
//                 data.error ||
//                 "Unable to load form."
//             );
//             return;
//         }

//         // -------------------------------------------------
//         // Document title
//         // -------------------------------------------------

//         const title =
//             document.getElementById("documentTitle");

//         title.textContent =
//             `Fill ${data.document_name}`;


//         // -------------------------------------------------
//         // Form container
//         // -------------------------------------------------

//         const container =
//             document.getElementById("dynamicForm");

//         container.innerHTML = "";


//         // -------------------------------------------------
//         // Check fields
//         // -------------------------------------------------

//         if (
//             !data.fields ||
//             data.fields.length === 0
//         ) {

//             container.innerHTML = `
//                 <p class="error">
//                     No fields are required for this document.
//                 </p>
//             `;

//             return;
//         }


//         // -------------------------------------------------
//         // Create fields dynamically
//         // -------------------------------------------------

//         data.fields.forEach(field => {

//             const wrapper =
//                 document.createElement("div");

//             wrapper.className =
//                 "form-group";


//             // Label
//             const label =
//                 document.createElement("label");

//             label.setAttribute(
//                 "for",
//                 field.name
//             );

//             label.textContent =
//                 field.label;

//             if (field.required) {
//                 label.textContent += " *";
//             }

//             wrapper.appendChild(label);


//             let input;


//             // -------------------------------------------------
//             // TEXTAREA
//             // -------------------------------------------------

//             if (field.type === "textarea") {

//                 input =
//                     document.createElement("textarea");

//                 input.rows = 5;

//             }


//             // -------------------------------------------------
//             // SELECT
//             // -------------------------------------------------

//             else if (field.type === "select") {

//                 input =
//                     document.createElement("select");

//                 const defaultOption =
//                     document.createElement("option");

//                 defaultOption.value = "";

//                 defaultOption.textContent =
//                     `Select ${field.label}`;

//                 defaultOption.disabled = true;

//                 defaultOption.selected = true;

//                 input.appendChild(
//                     defaultOption
//                 );


//                 if (field.options) {

//                     field.options.forEach(
//                         option => {

//                             const optionElement =
//                                 document.createElement(
//                                     "option"
//                                 );

//                             optionElement.value =
//                                 option;

//                             optionElement.textContent =
//                                 option;

//                             input.appendChild(
//                                 optionElement
//                             );
//                         }
//                     );
//                 }

//             }


//             // -------------------------------------------------
//             // NORMAL INPUT
//             // -------------------------------------------------

//             else {

//                 input =
//                     document.createElement("input");

//                 input.type =
//                     field.type || "text";
//             }


//             // -------------------------------------------------
//             // Common attributes
//             // -------------------------------------------------

//             input.name =
//                 field.name;

//             input.id =
//                 field.name;

//             input.className =
//                 "dynamic-input";


//             if (field.required) {

//                 input.required = true;
//             }


//             wrapper.appendChild(input);

//             container.appendChild(wrapper);

//         });


//         // -------------------------------------------------
//         // Store template ID
//         // -------------------------------------------------

//         document.getElementById(
//             "templateId"
//         ).value = templateId;

//     }

//     catch (error) {

//         console.error(
//             "Form loading error:",
//             error
//         );

//         alert(
//             "Unable to load document form."
//         );
//     }
// }


// // ========================================================
// // SUBMIT FORM
// // ========================================================

// async function submitForm() {

//     const form =
//         document.getElementById(
//             "documentForm"
//         );


//     // ----------------------------------------------------
//     // Browser validation
//     // ----------------------------------------------------

//     if (!form.checkValidity()) {

//         form.reportValidity();

//         return;
//     }


//     // ----------------------------------------------------
//     // Collect form data
//     // ----------------------------------------------------

//     const formData =
//         new FormData(form);

//     const data = {};


//     formData.forEach(
//         (value, key) => {

//             if (key !== "template_id") {

//                 data[key] = value;
//             }
//         }
//     );


//     const templateId =
//         document.getElementById(
//             "templateId"
//         ).value;


//     if (!templateId) {

//         alert(
//             "Template ID is missing."
//         );

//         return;
//     }


//     // ----------------------------------------------------
//     // Generate document
//     // ----------------------------------------------------

//     try {

//         const response =
//             await fetch(
//                 "/generate/filled",
//                 {
//                     method: "POST",

//                     headers: {
//                         "Content-Type":
//                             "application/json"
//                     },

//                     body: JSON.stringify({

//                         template_id:
//                             templateId,

//                         data:
//                             data
//                     })
//                 }
//             );


//         const result =
//             await response.json();


//         if (!response.ok) {

//             console.error(result);

//             if (result.errors) {

//                 alert(
//                     Object.values(
//                         result.errors
//                     ).join("\n")
//                 );

//             } else {

//                 alert(
//                     result.error ||
//                     "Document generation failed."
//                 );
//             }

//             return;
//         }


//         // ------------------------------------------------
//         // Redirect to result page
//         // ------------------------------------------------

//         if (!result.filename) {

//             alert(
//                 "Document generated but filename was not returned."
//             );

//             return;
//         }


//         window.location.href =
//             `/result?filename=${
//                 encodeURIComponent(
//                     result.filename
//                 )
//             }`;

//     }

//     catch (error) {

//         console.error(
//             "Generation error:",
//             error
//         );

//         alert(
//             "Unable to generate document."
//         );
//     }
// }








// /* ============================================================
//    CREATE FIELD
// ============================================================ */

// function createField(
//     container,
//     field
// ) {

//     const wrapper =
//         document.createElement("div");

//     wrapper.className =
//         "form-group";


//     /* --------------------------------------------------------
//        Label
//     -------------------------------------------------------- */

//     const label =
//         document.createElement("label");


//     label.htmlFor =
//         field.name;


//     label.textContent =
//         field.label || field.name;


//     /* --------------------------------------------------------
//        Required indicator
//     -------------------------------------------------------- */

//     if (field.required) {

//         const requiredMark =
//             document.createElement("span");

//         requiredMark.className =
//             "required-mark";

//         requiredMark.textContent =
//             " *";

//         label.appendChild(
//             requiredMark
//         );

//     }


//     wrapper.appendChild(label);


//     /* --------------------------------------------------------
//        Create input
//     -------------------------------------------------------- */

//     let input;


//     if (field.type === "textarea") {

//         input =
//             document.createElement("textarea");

//     }

//     else if (field.type === "select") {

//         input =
//             document.createElement("select");


//         /* ----------------------------------------------------
//            Select options
//         ---------------------------------------------------- */

//         if (
//             field.options &&
//             Array.isArray(field.options)
//         ) {

//             field.options.forEach(
//                 function (option) {

//                     const optionElement =
//                         document.createElement("option");

//                     optionElement.value =
//                         option;

//                     optionElement.textContent =
//                         option;

//                     input.appendChild(
//                         optionElement
//                     );

//                 }
//             );

//         }

//     }

//     else {

//         input =
//             document.createElement("input");

//         input.type =
//             field.type || "text";

//     }


//     /* --------------------------------------------------------
//        Common attributes
//     -------------------------------------------------------- */

//     input.name =
//         field.name;

//     input.id =
//         field.name;


//     if (field.required) {

//         input.required = true;

//     }


//     /* --------------------------------------------------------
//        Placeholder
//     -------------------------------------------------------- */

//     if (field.placeholder) {

//         input.placeholder =
//             field.placeholder;

//     }


//     /* --------------------------------------------------------
//        Append input
//     -------------------------------------------------------- */

//     wrapper.appendChild(input);


//     /* --------------------------------------------------------
//        Description
//     -------------------------------------------------------- */

//     if (field.description) {

//         const description =
//             document.createElement("div");

//         description.className =
//             "field-description";

//         description.textContent =
//             field.description;

//         wrapper.appendChild(
//             description
//         );

//     }


//     container.appendChild(wrapper);
// }


// /* ============================================================
//    SUBMIT FORM
// ============================================================ */

// async function submitForm() {

//     const form =
//         document.getElementById(
//             "documentForm"
//         );


//     /* --------------------------------------------------------
//        Browser validation
//     -------------------------------------------------------- */

//     if (!form.checkValidity()) {

//         form.reportValidity();

//         return;
//     }


//     const templateId =
//         document.getElementById(
//             "templateId"
//         ).value;


//     if (!templateId) {

//         alert(
//             "Template ID is missing."
//         );

//         return;
//     }


//     const submitBtn =
//         document.getElementById(
//             "generateBtn"
//         );


//     if (submitBtn) {

//         submitBtn.disabled = true;

//         submitBtn.textContent =
//             "Generating...";

//     }


//     try {

//         /* ----------------------------------------------------
//            Collect form data
//         ---------------------------------------------------- */

//         const formData =
//             new FormData(form);


//         const data = {};


//         formData.forEach(
//             function (value, key) {

//                 if (
//                     key !== "template_id"
//                 ) {

//                     data[key] =
//                         value;

//                 }

//             }
//         );


//         /* ----------------------------------------------------
//            Send data to backend
//         ---------------------------------------------------- */

//         const response =
//             await fetch(
//                 "/generate/filled",
//                 {

//                     method: "POST",

//                     headers: {
//                         "Content-Type":
//                             "application/json"
//                     },

//                     body: JSON.stringify({

//                         template_id:
//                             templateId,

//                         data:
//                             data

//                     })

//                 }
//             );


//         const result =
//             await response.json();


//         /* ----------------------------------------------------
//            Backend error
//         ---------------------------------------------------- */

//         if (!response.ok) {

//             if (result.errors) {

//                 const messages =
//                     Object.values(
//                         result.errors
//                     );

//                 throw new Error(
//                     messages.join("\n")
//                 );

//             }


//             throw new Error(
//                 result.error ||
//                 "Document generation failed."
//             );

//         }


//         /* ----------------------------------------------------
//            Filename validation
//         ---------------------------------------------------- */

//         if (!result.filename) {

//             throw new Error(
//                 "Server did not return generated filename."
//             );

//         }


//         /* ----------------------------------------------------
//            Open result page
//         ---------------------------------------------------- */

//         window.location.href =
//             `/result?filename=${encodeURIComponent(
//                 result.filename
//             )}`;


//     } catch (error) {

//         console.error(error);


//         alert(
//             error.message ||
//             "Unable to generate document."
//         );


//         if (submitBtn) {

//             submitBtn.disabled = false;

//             submitBtn.textContent =
//                 "Generate Document";

//         }

//     }
// }


// /* ============================================================
//    HTML ESCAPE
// ============================================================ */

// function escapeHtml(value) {

//     const div =
//         document.createElement("div");

//     div.textContent =
//         String(value);

//     return div.innerHTML;
// }















// ============================================================
// LOAD FORM FOR SPECIFIC TEMPLATE
// ============================================================

async function loadForm(templateId) {
    if (!templateId) {
        alert("Template ID is missing.");
        return;
    }
    try {
        const response = await fetch(
            `/form/${encodeURIComponent(templateId)}`
        );
        const data = await response.json();
        if (!response.ok) {
            throw new Error(
                data.error || "Unable to load form."
            );
        }
        // ----------------------------------------------------
        // Document title
        // ----------------------------------------------------
        const title = document.getElementById("documentTitle");
        if (title) {
            title.textContent =
                `Fill ${data.document_name}`;
        }
        // ----------------------------------------------------
        // Store template ID
        // ----------------------------------------------------
        document.getElementById("templateId").value = data.template_id;
        // ----------------------------------------------------
        // Form container
        // ---------------------------------------------------
        const container = document.getElementById("dynamicForm");
        container.innerHTML = "";
        // ----------------------------------------------------
        // Generate fields dynamically
        // ----------------------------------------------------
        data.fields.forEach(field => {
            const wrapper = document.createElement("div");
            wrapper.className = "form-group";
            // Label
            const label = document.createElement("label");
            label.textContent = field.label;
            label.setAttribute("for",field.name);
            wrapper.appendChild(label);
            // Input
            let input;
            if (field.type === "textarea") {
                input = document.createElement("textarea");
                input.rows = 4;
            }
            else if (field.type === "select") {
                input = document.createElement("select");
                const defaultOption = document.createElement("option");
                defaultOption.value = "";
                defaultOption.textContent = `Select ${field.label}`;
                defaultOption.disabled = true;
                defaultOption.selected = true;
                input.appendChild(defaultOption);
                if (field.options) {
                    field.options.forEach(
                        option => {
                            const optionElement =
                                document.createElement(
                                    "option"
                                );
                            optionElement.value = option;
                            optionElement.textContent = option;
                            input.appendChild(optionElement);
                        }
                    );
                }
            }
            else {
                input = document.createElement("input");
                input.type = field.type || "text";
            }
            input.name = field.name;
            input.id = field.name;
            if (field.required) {
                input.required = true;
            }
            wrapper.appendChild(input);
            container.appendChild(wrapper);
        });
    }
    catch (error) {
        console.error(error);
        const container = document.getElementById("dynamicForm");
        container.innerHTML = `
            <div class="error">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}

// ============================================================
// SUBMIT FORM
// ============================================================
async function submitForm() {
    const form = document.getElementById("documentForm");
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    const templateId = document.getElementById("templateId").value;
    if (!templateId) {
        alert("Template ID is missing.");
        return;
    }
    const formData = new FormData(form);
    const userData = {};
    formData.forEach(
        (value, key) => {
            if (key !== "template_id") {
                userData[key] = value;
            }
        }
    );
    const generateBtn = document.getElementById("generateBtn");
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.textContent = "Generating...";
    }
    try {
        const response =
            await fetch(
                "/api/generate",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        document_type: templateId,
                        data: userData,
                        use_template: true
                    })
                }
            );
        const result = await response.json();
        if (!response.ok) {
            throw new Error(
                result.error ||
                "Document generation failed."
            );
        }
        console.log("Generated document:",result);
        if (!result.filename) {
            throw new Error("Server did not return the generated filename.");
        }
        // ------------------------------------------------
        // Show success message
        // ------------------------------------------------
        alert("Document generated successfully.");
        // ------------------------------------------------
        // Create Download Button
        // ------------------------------------------------
        const existing = document.getElementById("downloadResult");
        if (existing) {
            existing.remove();
        }
        const downloadContainer = document.createElement("div");
        downloadContainer.id = "downloadResult";
        downloadContainer.style.marginTop = "20px";
        downloadContainer.innerHTML = `
            <div class="success-message">
                <strong>
                    Document generated successfully.
                </strong>
                <p>
                    Your document is ready for download.
                </p>
                <button
                    type="button"
                    class="primary-btn"
                    id="downloadGeneratedBtn"
                >
                    Download Document
                </button>
            </div>
        `;
        form.appendChild(downloadContainer);
        // ------------------------------------------------
        // Download button
        // ------------------------------------------------
        document.getElementById("downloadGeneratedBtn").addEventListener("click",function () {
                    window.location.href =
                        `/api/documents/download?filename=${encodeURIComponent(
                            result.filename
                        )}`;
                }
            );
    }
    catch (error) {
        console.error(error);
        alert(error.message || "Unable to generate document.");
    }
    finally {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = "Generate Document";
        }
    }
}
// ============================================================
// HTML ESCAPE
// ============================================================
function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
}
// ============================================================
// GENERATE AND DOWNLOAD BLANK DOCUMENT
// ============================================================
// ============================================================
// DOWNLOAD BLANK TEMPLATE
// ============================================================
// ============================================================
// DOWNLOAD BLANK TEMPLATE
// ============================================================

async function downloadBlankDocument() {
    const templateId = document.getElementById("templateId").value;
    if (!templateId) {
        alert("Template ID is missing.");
        return;
    }
    try {
        const response =
            await fetch(
                "/generate/blank",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        template_id:
                            templateId
                    })
                }
            );
        const result = await response.json();
        console.log("Blank document response:",result);
        if (!response.ok) {
            throw new Error(
                result.error ||
                "Unable to generate blank template."
            );
        }
        if (!result.filename) {
            throw new Error(
                "Filename was not returned by server."
            );
        }
        // ----------------------------------------------------
        // Download blank document
        // ----------------------------------------------------
        window.location.href =
            "/api/documents/download?filename=" +
            encodeURIComponent(
                result.filename
            );
    }
    catch (error) {
        console.error(
            "Blank document error:",
            error
        );
        alert(
            error.message ||
            "Unable to download blank template."
        );
    }
}
// ============================================================
// HTML ESCAPE
// ============================================================
function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
}