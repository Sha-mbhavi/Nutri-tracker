document.querySelectorAll('.flash').forEach((flash) => {
  setTimeout(() => flash.classList.add('hidden'), 5000);
});

function startVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    window.alert("Voice recognition is not supported in this browser.");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = false;
  recognition.onresult = event => {
    const field = document.getElementById("voiceText");
    if (field) field.value = event.results[0][0].transcript;
  };
  recognition.onerror = () => window.alert("Voice recognition could not be started. Please try again or type the meal.");
  recognition.start();
}
