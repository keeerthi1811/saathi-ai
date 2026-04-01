import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2 } from "lucide-react";

import PDFUploader from "./components/PDFUploader";
import VideoUploader from "./components/VideoUploader";
import StudyTab from "./components/StudyTab";

export default function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("Connecting...");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [isReady, setIsReady] = useState(false);
  const [activeTab, setActiveTab] = useState("home");

  const ws = useRef(null);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const streamRef = useRef(null);

  // 🔌 WebSocket Connection Logic
  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket("ws://127.0.0.1:8000/ws/chat");

      ws.current.onopen = () => {
        setIsReady(true);
        setStatus("Ready! Tap to talk.");
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setTranscript(data.user_text || "");
        setResponse(data.bot_display_text || "");

        if (data.action === "play_youtube" && data.youtube_url) {
          window.open(data.youtube_url, "_blank");
        }

        if (data.audio) {
          const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
          audio.play();
          setStatus("Saathi speaking...");
          audio.onended = () => setStatus("Ready again!");
        }
      };

      ws.current.onclose = () => {
        setIsReady(false);
        setStatus("Reconnecting...");
        setTimeout(connect, 3000);
      };
    };

    connect();
    return () => ws.current?.close();
  }, []);

  // 🎤 START RECORDING
  const startRecording = async () => {
    if (!isReady || isRecording) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      mediaRecorder.current = recorder;
      audioChunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.current.push(e.data);
        }
      };

      // Handle data processing AFTER the recorder stops
      recorder.onstop = async () => {
        if (audioChunks.current.length === 0) return;

        setStatus("Thinking...");
        const blob = new Blob(audioChunks.current, { type: "audio/wav" });
        const reader = new FileReader();

        reader.onloadend = () => {
          const base64Audio = reader.result.split(",")[1];
          if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ audio: base64Audio }));
          } else {
            setStatus("Connection lost. Retrying...");
          }
        };
        reader.readAsDataURL(blob);
      };

      recorder.start();
      setIsRecording(true);
      setStatus("Listening...");
    } catch (err) {
      console.error(err);
      alert("Mic permission needed!");
    }
  };

  // ⏹ STOP RECORDING (Fixed for instant hardware release)
  const stopRecording = () => {
    if (!mediaRecorder.current || mediaRecorder.current.state === "inactive") return;

    try {
      // 1. Stop the recorder (triggers onstop)
      mediaRecorder.current.stop();

      // 2. Kill the microphone tracks immediately (stops the red light)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      // 3. Update UI state
      setIsRecording(false);
      setStatus("Processing...");
    } catch (err) {
      console.error("Stop error:", err);
      setIsRecording(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center py-10 px-6 text-white bg-slate-950">
      
      {/* HEADER */}
      <div className="text-center mb-6">
        <h1 className="text-5xl font-black bg-gradient-to-br from-indigo-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent italic">
          SAATHI
        </h1>
        <p className="text-slate-500 text-xs uppercase tracking-widest">
          Your AI Study Companion
        </p>
      </div>

      {/* NAVBAR */}
      <div className="flex gap-3 mb-8 bg-slate-900 p-2 rounded-xl shadow-lg">
        {["home", "upload", "study"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === tab
                ? "bg-indigo-600"
                : "bg-slate-700 hover:bg-slate-600"
            }`}
          >
            {tab === "home" && "🎤 Assistant"}
            {tab === "upload" && "📄 Upload"}
            {tab === "study" && "🎮 Study Mode"}
          </button>
        ))}
      </div>

      {/* HOME TAB */}
      {activeTab === "home" && (
        <>
          <div className="relative flex items-center justify-center mb-6">
            <AnimatePresence>
              {isRecording && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{
                    scale: [1, 1.3, 1],
                    opacity: [0.3, 0.6, 0.3],
                  }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  transition={{ repeat: Infinity, duration: 2 }}
                  className="absolute w-72 h-72 bg-indigo-600 rounded-full blur-[80px]"
                />
              )}
            </AnimatePresence>

            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={!isReady || status === "Processing..."}
              className={`relative z-10 w-40 h-40 rounded-full flex items-center justify-center transition-all active:scale-95 ${
                isRecording ? "bg-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.4)]" : "bg-indigo-600 shadow-[0_0_30px_rgba(79,70,229,0.4)]"
              } disabled:bg-slate-800 disabled:cursor-not-allowed`}
            >
              {status === "Processing..." ? (
                <Loader2 className="animate-spin" size={40} />
              ) : isRecording ? (
                <MicOff size={40} />
              ) : (
                <Mic size={40} />
              )}
            </button>
          </div>

          <div className="w-full max-w-xl space-y-4">
            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400 mb-1 font-mono">USER TRANSCRIPT</p>
              <p className="text-slate-200">{transcript || "Waiting for audio..."}</p>
            </div>

            <div className="bg-indigo-600/10 p-4 rounded-xl border border-indigo-500/20">
              <p className="text-xs text-indigo-400 mb-1 font-mono">SAATHI RESPONSE</p>
              <p className="text-indigo-100">{response || "Tap the microphone to start learning."}</p>
            </div>
          </div>
        </>
      )}

      {/* UPLOAD TAB */}
      {activeTab === "upload" && (
        <div className="w-full max-w-xl">
          <PDFUploader setStatus={setStatus} />
          <div className="mt-6">
            <VideoUploader setStatus={setStatus} />
          </div>
        </div>
      )}

      {/* STUDY TAB */}
      {activeTab === "study" && <StudyTab />}

      {/* FOOTER STATUS */}
      <div className="mt-8 px-4 py-1 rounded-full bg-slate-900 border border-slate-800 text-[10px] text-slate-400 flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isReady ? "bg-emerald-500" : "bg-rose-500 animate-pulse"}`} />
        {status.toUpperCase()}
      </div>
    </div>
  );
}