/* ============================================================
   DOCUMENT ACTIONS
============================================================ */
/* ============================================================
   DOWNLOAD BLANK DOCUMENT
============================================================ */
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
        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to generate document."
            );
        }
        if (!data.filename) {
            throw new Error(
                "Document generated but filename was not returned."
            );
        }
        window.location.href =
            `/api/documents/download?filename=${encodeURIComponent(
                data.filename
            )}`;
    }
    catch (error) {
        console.error("Blank document error:", error);
        alert(error.message || "Unable to download document.");
    }
}
/* ============================================================
   OPEN FORM
============================================================ */
function openForm(templateId) {
    if (!templateId) {
        alert("Template ID is missing.");
        return;
    }
    window.location.href =
        `/form-page/${encodeURIComponent(
            templateId
        )}`;
}