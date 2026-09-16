let recorder;
let stream;
let chunks = [];
let recording = false;

async function startRecording() {

    if (recording) return;

    const micBtn = document.getElementById("micBtn");
    const stopBtn = document.getElementById("stopBtn");

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        recorder = new MediaRecorder(stream);

        chunks = [];

        recorder.ondataavailable = (event) => {
            chunks.push(event.data);
        };

        recorder.start();

        recording = true;
        micBtn.disabled = true;
        micBtn.classList.add("recording");

        stopBtn.disabled = false;

        micBtn.textContent = "🎙 Recording...";

    } catch (error) {

        console.error(error);

        alert("Unable to access microphone.");
    }
}

async function stopRecording() {

    if (!recording) return;

    const micBtn = document.getElementById("micBtn");
    const stopBtn = document.getElementById("stopBtn");

    recorder.onstop = async () => {

        const blob = new Blob(chunks, {
            type: "audio/webm"
        });

        const formData = new FormData();

        formData.append(
            "audio",
            blob,
            "voice.webm"
        );

        stopBtn.textContent = "⏳";

        try {

            const response = await fetch("/api/voice", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (data.success) {

                document.getElementById("question").value =
                    data.transcript;

                sendQuestion();

            } else {

                alert(data.error || "Speech recognition failed.");
            }

        } catch (error) {

            console.error(error);

            alert("Speech recognition failed.");
        }

        recording = false;

        micBtn.disabled = false;
        micBtn.classList.remove("recording");

        stopBtn.disabled = true;

        micBtn.textContent = "🎤 Start";
        stopBtn.textContent = "⏹ Stop";
};

    recorder.stop();

    stream.getTracks().forEach(track => track.stop());
}