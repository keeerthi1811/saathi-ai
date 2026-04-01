import React, { useState } from "react";

export default function PDFUploader({ setStatus }) {
  const [pdfText, setPdfText] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [isStopped, setIsStopped] = useState(false);
  const [language, setLanguage] = useState("en-IN");

  const playChunks = async (chunks) => {
    setIsStopped(false);

    for (let chunk of chunks) {
      if (isStopped) break;

      await new Promise((resolve) => {
        const byteCharacters = atob(chunk);
        const byteNumbers = new Array(byteCharacters.length)
          .fill(0)
          .map((_, i) => byteCharacters.charCodeAt(i));

        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: "audio/wav" });

        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);

        setCurrentAudio(audio);

        audio.play().catch(() => {
          setStatus("Click screen once & try again");
          resolve();
        });

        audio.onended = resolve;
      });
    }

    setCurrentAudio(null);
    setStatus("Finished reading");
  };

  const stopAudio = () => {
    setIsStopped(true);

    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }

    setCurrentAudio(null);
    setStatus("Stopped");
  };

  const handlePDFUpload = async (file) => {
    try {
      setIsUploading(true);
      setStatus("Uploading PDF...");

      const formData = new FormData();
      formData.append("file", file);
      formData.append("target_lang", language);

      const res = await fetch("http://127.0.0.1:8000/upload-pdf", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.error) {
        setStatus("Error processing PDF");
        return;
      }

      setPdfText(data.text || "");

      if (data.audio_chunks) {
        setStatus("Reading...");
        playChunks(data.audio_chunks);
      }

    } catch (err) {
      console.error(err);
      setStatus("Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full max-w-xl mt-6">

      {/* 🌐 Language Selector */}
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="mb-4 px-3 py-2 rounded-lg bg-slate-800 text-white"
      >
        <option value="en-IN">English</option>
        <option value="hi-IN">Hindi</option>
        <option value="kn-IN">Kannada</option>
        <option value="te-IN">Telugu</option>
      </select>

      {/* Upload */}
      <label className="cursor-pointer bg-indigo-600 hover:bg-indigo-500 px-5 py-3 rounded-xl text-sm font-semibold shadow-lg inline-block">
        📤 Upload PDF
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files[0];
            if (file) handlePDFUpload(file);
          }}
        />
      </label>

      {/* Stop */}
      {currentAudio && (
        <button
          onClick={stopAudio}
          className="ml-4 bg-rose-600 hover:bg-rose-500 px-4 py-2 rounded-lg text-sm font-semibold"
        >
          ⏹ Stop
        </button>
      )}

      {isUploading && (
        <p className="text-xs text-slate-400 mt-2">
          Processing PDF...
        </p>
      )}

      {pdfText && (
        <div className="bg-emerald-600/10 border border-emerald-500/20 p-5 rounded-3xl mt-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-400 mb-2">
            PDF Summary
          </p>
          <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">
            {pdfText}
          </p>
        </div>
      )}
    </div>
  );
}