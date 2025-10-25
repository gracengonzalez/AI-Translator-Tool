document.addEventListener("DOMContentLoaded", () => {
  const speakBtn = document.getElementById("speakBtn");
  const statusEl = document.getElementById("speakStatus");
  const player = document.getElementById("player");

  speakBtn.addEventListener("click", async () => {
    const textEl = document.getElementById("translatedText") || document.getElementById("sentence");
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
});
