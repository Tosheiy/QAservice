import React, { useState } from "react";
import "./FileUploader.css";
import { useNavigate } from 'react-router-dom';
import axios from "axios";
import HelpButton from "../components/HelpButton";

const apiUrl = process.env.REACT_APP_API_URL;

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

        try {
            setIsLoading(true); // ローディング開始

            // ① プリサインドURL取得
            const response = await axios.get(`${apiUrl}/generate_presigned_url`, {
                params: {
                    filename: file.name,
                    questioncount: questionCount,
                    mode: mode,
                    difficulty: difficulty,
                },
              });
            const { url, key, uuid } = response.data;

            // ② S3に直接アップロード
            const contentType = file.name.endsWith(".pdf")
                ? "application/pdf"
                : file.name.endsWith(".txt")
                    ? "text/plain"
                    : "application/octet-stream"; // 安全なデフォルト


            await fetch(url, {
                method: "PUT",
                headers: {
                    "Content-Type": contentType,
                    "x-amz-meta-questioncount": String(questionCount),
                    "x-amz-meta-mode": mode,
                    "x-amz-meta-difficulty": difficulty,
                    "x-amz-meta-uuid": uuid,
                },
                body: file,
            });
        

            const pollStatus = async (uuid: string) => {
                const startTime = Date.now();
                const maxWait = 180000; // 最大3分

                const interval = setInterval(async () => {
                    try {
                        const res = await fetch(`${apiUrl}/check_status?id=${uuid}`);
                        const data = await res.json();

                        if (data.status === "completed") {
                            clearInterval(interval);
                            setIsLoading(false); // ✅ 成功時にローディング終了
                            navigate(`/qa/${uuid}`);
                        } else if (Date.now() - startTime > maxWait) {
                            clearInterval(interval);
                            setIsLoading(false); // ✅ タイムアウト時にローディング終了
                            alert("処理がタイムアウトしました。もう一度お試しください。");
                        }
                    } catch (error) {
                        clearInterval(interval);
                        setIsLoading(false); // ✅ エラー時にもローディング終了
                        alert("サーバーエラーが発生しました。");
                    }
                }, 5000);
            };

            // ✅ 呼び出し前にローディング開始
            pollStatus(uuid);
            
        } catch (error) {
            console.error("送信エラー:", error);
            setIsLoading(false);
            alert("送信エラー");
        }
    };

    const handleHelpClick = () => {
        alert("ここに使い方ガイドを表示します。");
    };


    return (
        <div className="uploader-container">
            <HelpButton onClick={handleHelpClick} />
            <h1 className="title">QA生成ツール</h1>
            <h2>資料アップロード</h2>
            <h4>（.txt, .pdfファイルのみ対応）</h4>

            {!file ? (
                <div
                    className="upload-box"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onClick={() => document.getElementById("hiddenFileInput")?.click()}
                >
                    <p>ここにPDFやテキストをドラッグ＆ドロップ、<br />またはクリックして選択</p>
                    <input
                        type="file"
                        id="hiddenFileInput"
                        accept="application/pdf,text/plain"
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
                    {[
                        { label: "易", value: "easy" },
                        { label: "中", value: "middle" },
                        { label: "難", value: "hard" }
                    ].map(({ label, value }) => (
                        <button
                            key={value}
                            className={difficulty === value ? "selected" : ""}
                            onClick={() => setDifficulty(value)}
                        >
                            {label}
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
                    <option value="three">３択問題</option>
                    <option value="four">４択問題</option>
                    <option value="multi">４択複数選択問題</option>
                    <option value="script">記述式問題</option>
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
