// script.js
document.addEventListener("DOMContentLoaded", () => {
  const speakBtn = document.getElementById("speakBtn");
  const statusEl = document.getElementById("speakStatus");
  const player = document.getElementById("player");
  const micBtn = document.getElementById("micBtn");
  const micStatus = document.getElementById("micStatus");
  const sentenceInput = document.getElementById("sentence");

  // ---------- TTS ----------
  if (speakBtn) {
    speakBtn.addEventListener("click", async () => {
      const textEl = document.getElementById("translatedText") || sentenceInput;
      const text = (textEl?.textContent || textEl?.value || "").trim();
      if (!text) {
        statusEl.textContent = "No text to speak.";
        return;
      }
      statusEl.textContent = "Generating speech...";
      speakBtn.disabled = true;
      try {
        const res = await fetch(`/tts?text=${encodeURIComponent(text)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        player.src = url;
        await player.play();
        statusEl.textContent = "Playing ✅";
      } catch (e) {
        console.error(e);
        statusEl.textContent = "Error generating audio.";
      } finally {
        speakBtn.disabled = false;
      }
    });
  }

  // ---------- STT ----------
  let mediaRecorder;
  let audioChunks = [];
  let isRecording = false;
  let currentStream;
  let chosenMime = "";

  async function startRecording() {
    try {
      currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Pick a supported mime type (no WAV; browsers don't support it with MediaRecorder)
      const candidates = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/ogg"
      ];
      chosenMime = candidates.find(t => MediaRecorder.isTypeSupported?.(t)) || "";

      mediaRecorder = chosenMime
        ? new MediaRecorder(currentStream, { mimeType: chosenMime })
        : new MediaRecorder(currentStream);

      audioChunks = [];
      isRecording = true;

      micStatus.textContent = "🎙 Listening...";
      micBtn.textContent = "⏹ Stop";

      mediaRecorder.addEventListener("dataavailable", (e) => {
        if (e.data && e.data.size > 0) audioChunks.push(e.data);
      });

      mediaRecorder.addEventListener("stop", async () => {
        micStatus.textContent = "Processing...";

        // Build the final Blob from chunks
        const blobType = chosenMime || "audio/webm";
        const audioBlob = new Blob(audioChunks, { type: blobType });
        if (!audioBlob || audioBlob.size === 0) {
          micStatus.textContent = "No audio captured. Try again.";
          micBtn.textContent = "🎙 Start Talking";
          isRecording = false;
          currentStream?.getTracks().forEach(t => t.stop());
          currentStream = null;
          return;
        }

        const ext = audioBlob.type.includes("ogg") ? "ogg" : "webm";
        const formData = new FormData();
        formData.append("audio", audioBlob, `speech.${ext}`);

        try {
          const res = await fetch("/stt", { method: "POST", body: formData });

          // Read JSON even on error to surface the real message
          let data;
          try {
            data = await res.json();
          } catch {
            throw new Error(`Non-JSON response (status ${res.status})`);
          }

          if (!res.ok) {
            const msg =
              (typeof data?.error === "string" && data.error) ||
              (data?.error && JSON.stringify(data.error)) ||
              `HTTP ${res.status}`;
            throw new Error(msg);
          }

          if (data.text) {
            sentenceInput.value = data.text;
            micStatus.textContent = "✅ Recognized!";
          } else {
            micStatus.textContent = "❌ Could not recognize speech.";
          }
        } catch (err) {
          console.error(err);
          micStatus.textContent = `⚠️ ${err.message || "Error sending audio."}`;
        } finally {
          micBtn.textContent = "🎙 Start Talking";
          isRecording = false;
          // Stop the mic
          currentStream?.getTracks().forEach(t => t.stop());
          currentStream = null;
        }
      });

      mediaRecorder.start(); // start AFTER listeners are set
    } catch (err) {
      console.error("Microphone access denied:", err);
      micStatus.textContent = "🎤 Mic access denied.";
    }
  }

  function toggleRecording() {
    if (!isRecording) {
      startRecording();
    } else if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
  }

  if (micBtn) {
    micBtn.addEventListener("click", toggleRecording);
  }
});
