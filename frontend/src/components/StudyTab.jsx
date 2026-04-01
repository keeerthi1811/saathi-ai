import React, { useState, useRef } from "react";

export default function StudyTab() {
  const [summary, setSummary] = useState("");
  const [quiz, setQuiz] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [loading, setLoading] = useState(false);

  const [isRecording, setIsRecording] = useState(false);

  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  // 📄 Upload PDF
  const uploadPDF = async (file) => {
    try {
      setLoading(true);

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://127.0.0.1:8000/study-upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      setSummary(data.summary || "");
      setQuiz(data.quiz || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 🎤 START RECORDING
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        audioChunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = sendAudio;

      mediaRecorder.current.start();
      setIsRecording(true);

    } catch (err) {
      alert("Mic permission needed!");
    }
  };

  // ⏹ STOP RECORDING
  const stopRecording = () => {
    mediaRecorder.current.stop();
    setIsRecording(false);
  };

  // 📤 SEND AUDIO TO BACKEND
  const sendAudio = async () => {
    const blob = new Blob(audioChunks.current, { type: "audio/wav" });

    const formData = new FormData();
    formData.append("audio", blob);
    formData.append("correct_answer", quiz[currentQ].answer);

    try {
      const res = await fetch("http://127.0.0.1:8000/voice-quiz", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      console.log("User Answer:", data.user_answer);
      console.log("Feedback:", data.feedback);

      // 🔊 Play feedback audio
      if (data.audio) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
        audio.play();
      }

    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="w-full max-w-2xl relative z-50">

      <h2 className="text-2xl font-bold mb-4 text-center">
        🎮 Study Mode
      </h2>

      {/* 📤 Upload */}
      <label className="bg-indigo-600 px-4 py-2 rounded cursor-pointer">
        📄 Upload PDF
        <input
          type="file"
          hidden
          accept="application/pdf"
          onChange={(e) => uploadPDF(e.target.files[0])}
        />
      </label>

      {loading && <p className="mt-3">Processing...</p>}

      {/* 📄 Summary */}
      {summary && (
        <div className="mt-6 bg-slate-900 p-4 rounded">
          <h3 className="font-semibold mb-2">Summary</h3>
          <p>{summary}</p>
        </div>
      )}

      {/* 🧠 Quiz */}
      {quiz.length > 0 && (
        <div className="mt-6 bg-slate-900 p-4 rounded">

          <h3 className="font-semibold mb-2">Quiz</h3>

          <p className="mb-4">{quiz[currentQ].question}</p>

          {/* 🎤 BUTTON */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`px-4 py-2 rounded ${
              isRecording ? "bg-red-600" : "bg-emerald-600"
            }`}
          >
            {isRecording ? "⏹ Stop Recording" : "🎤 Start Answering"}
          </button>

        </div>
      )}

    </div>
  );
}