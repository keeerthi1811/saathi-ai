import React, { useState } from "react";

export default function VideoUploader({ setStatus }) {
  const [videoText, setVideoText] = useState("");
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
    setStatus("Finished video explanation");
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

  const handleUpload = async (file) => {
    try {
      setStatus("Processing video...");

      const formData = new FormData();
      formData.append("file", file);
      formData.append("target_lang", language);

      const res = await fetch("http://127.0.0.1:8000/upload-video", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (data.error) {
        setStatus("Error processing video");
        return;
      }

      setVideoText(data.text);

      if (data.audio_chunks) {
        setStatus("Explaining video...");
        playChunks(data.audio_chunks);
      }

    } catch (err) {
      console.error(err);
      setStatus("Upload failed");
    }
  };

  return (
    <div className="mt-6">

      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="mb-4 px-3 py-2 rounded bg-slate-800 text-white"
      >
        <option value="en-IN">English</option>
        <option value="hi-IN">Hindi</option>
        <option value="kn-IN">Kannada</option>
        <option value="te-IN">Telugu</option>
      </select>

      <label className="cursor-pointer bg-blue-600 px-5 py-3 rounded-lg">
        🎥 Upload Video
        <input
          type="file"
          accept="video/*"
          hidden
          onChange={(e) => handleUpload(e.target.files[0])}
        />
      </label>

      {currentAudio && (
        <button
          onClick={stopAudio}
          className="ml-4 bg-red-600 px-4 py-2 rounded"
        >
          ⏹ Stop
        </button>
      )}

      {videoText && (
        <div className="mt-4 p-4 bg-slate-800 rounded">
          <p>{videoText}</p>
        </div>
      )}
    </div>
  );
}