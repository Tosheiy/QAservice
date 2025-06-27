import React, { useState } from "react";
import "./FileUploader.css";
import { useNavigate } from 'react-router-dom';


const qaURL = "http://127.0.0.1:8000/upload_pdf/"

const FileUploader: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [questionCount, setQuestionCount] = useState<number>(5);
    const [mode, setMode] = useState<string>("");
    const [difficulty, setDifficulty] = useState<string>("易");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const navigate = useNavigate();  // ← これを useState の近くに追加

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
    };

    const handleSubmit = async () => {
        if (!file || !mode) {
            alert("ファイルとモードを選択してください");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("questionCount", String(questionCount));
        formData.append("mode", mode);
        formData.append("difficulty", difficulty);

        try {
            setIsLoading(true); // ローディング開始
            const response = await fetch(qaURL, {
                method: "POST",
                body: formData,
            });
            setIsLoading(false); // ローディング終了
            if (response.ok) {
                alert("アップロード成功！");
                const data = await response.json(); // ← レスポンスをJSONとして読み込む
                navigate(`/qa/${data.id}`);   
            }else {
                alert("アップロード失敗");
                navigate("/"); // ← ここで画面遷移
            }
        } catch (error) {
            console.error("送信エラー:", error);
            setIsLoading(false);
            alert("送信エラー");
        }
    };

    return (
        <div className="uploader-container">
            <h1 className="title">QA生成ツール</h1>
            <h2>PDFアップロード</h2>

            {!file ? (
                <div
                    className="upload-box"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onClick={() => document.getElementById("hiddenFileInput")?.click()}
                >
                    <p>ここにPDFをドラッグ＆ドロップ、<br />またはクリックして選択</p>
                    <input
                        type="file"
                        id="hiddenFileInput"
                        accept="application/pdf"
                        onChange={handleFileChange}
                        style={{ display: "none" }}
                    />
                </div>
            ) : (
                <div className="file-summary">
                    <p>選択されたファイル: <strong>{file.name}</strong></p>
                    <button className="remove-button" onClick={() => setFile(null)}>削除</button>
                </div>
            )}

            <div className="selector">
                <label>出題数:</label>
                <div className="button-group">
                    {[5, 10, 15, 20].map((count) => (
                        <button
                            key={count}
                            className={questionCount === count ? "selected" : ""}
                            onClick={() => setQuestionCount(count)}
                        >
                            {count}
                        </button>
                    ))}
                </div>
            </div>

            <div className="selector">
                <label>難易度:</label>
                <div className="button-group">
                    {["易", "中", "難"].map((level) => (
                        <button
                            key={level}
                            className={difficulty === level ? "selected" : ""}
                            onClick={() => setDifficulty(level)}
                        >
                            {level}
                        </button>
                    ))}
                </div>
            </div>

            <div className="selector">
                <label htmlFor="modeSelect">出題モード:</label>
                <select
                    id="modeSelect"
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                    className="dropdown"
                >
                    <option value="">モードを選択してください</option>
                    <option value="３択問題">３択問題</option>
                    <option value="４択問題">４択問題</option>
                    <option value="４択複数選択問題">４択複数選択問題</option>
                    <option value="記述式問題">記述式問題</option>
                </select>
            </div>

            <button className="submit-button" onClick={handleSubmit} disabled={isLoading}>
                {isLoading ? "生成中..." : "QAを生成する"}
            </button>

            {isLoading && <div className="loading-bar"></div>}
        </div>
    );
};

export default FileUploader;
