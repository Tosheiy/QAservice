import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import "./QAEdit.css";
import HelpButton from "../components/HelpButton";

interface QAItem {
    qa_id: number;
    question: string;
    options: string[];
    answer: string[];
    satisfaction: number;
}

interface QAInfo {
    created_at: string;
    className: string;
    title: string;
    mode: string;
}

const apiUrl = process.env.REACT_APP_API_URL;
const qaURL = `${apiUrl}/upload_csv/`

const QAEdit: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [qaItems, setQaItems] = useState<QAItem[]>([]);
    const [qaInfo, setQaInfo] = useState<QAInfo | null>(null);
    const [showAdvanced, setShowAdvanced] = useState(false);


    useEffect(() => {
        if (id) {
            Promise.all([
                axios.get<QAItem[]>(`${apiUrl}/qaitem/${id}`),
                axios.get<QAInfo>(`${apiUrl}/qainfo/${id}`)
            ])
                .then(([itemsRes, infoRes]) => {
                    const normalizedItems = itemsRes.data.map((item: any) => ({
                        ...item,
                        answer: Array.isArray(item.answer)
                            ? item.answer
                            : [String(item.answer).trim()] // ここで明確に文字列化＋trim
                    }));
                    setQaItems(normalizedItems);
                    setQaInfo(infoRes.data);
                })
                .catch(err => {
                    console.error("データ取得失敗:", err);
                });
        }
    }, [id]);

    const handleQuestionChange = (index: number, key: keyof QAItem, value: string) => {
        const updated = [...qaItems];
        (updated[index] as any)[key] = value;
        setQaItems(updated);
    };

    const handleOptionChange = (itemIndex: number, optIndex: number, value: string) => {
        const updated = [...qaItems];
        updated[itemIndex].options[optIndex] = value;
        setQaItems(updated);
    };

    const handleAnswerChange = (itemIndex: number, answerIndex: number, value: string) => {
        const updated = [...qaItems];
        updated[itemIndex].answer[answerIndex] = value;
        setQaItems(updated);
    };

    const addAnswerField = (itemIndex: number) => {
        const updated = [...qaItems];
        if (updated[itemIndex].answer.length < updated[itemIndex].options.length) {
            updated[itemIndex].answer.push("");
            setQaItems(updated);
        }
    };

    const removeAnswerField = (itemIndex: number, answerIndex: number) => {
        const updated = [...qaItems];
        if (updated[itemIndex].answer.length > 1) {
            updated[itemIndex].answer.splice(answerIndex, 1);
            setQaItems(updated);
        }
    };

    const handleSave = () => {
        if (!id || !qaInfo) return;

        const preparedItems = qaItems.map(item => ({
            ...item,
            answer: item.answer.map(ans => ans.trim())
        }));

        Promise.all([
            axios.patch(`${apiUrl}/qainfo/${id}`, qaInfo),
            axios.patch(`${apiUrl}/qaitem/${id}`, preparedItems)
        ])
            .then(() => navigate(`/qa/${id}`))
            .catch(err => console.error("保存失敗:", err));
    };

    const handleDelete = () => {
        if (!id) return;

        Promise.all([
            axios.delete(`${apiUrl}/qainfo/${id}`),
            axios.delete(`${apiUrl}/qaitem/${id}`)
        ])
            .then(() => navigate("/qa"))
            .catch(err => console.error("削除失敗:", err));
    };









    const [file, setFile] = useState<File | null>(null);
    const [questionCount, setQuestionCount] = useState<number>(5);
    const [mode, setMode] = useState<string>("");
    const [difficulty, setDifficulty] = useState<string>("易");
    const [isLoading, setIsLoading] = useState<boolean>(false);

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
        formData.append("id", id ?? "");

        try {
            setIsLoading(true); // ローディング開始
            const response = await fetch(qaURL, {
                method: "POST",
                body: formData,
            });
            setIsLoading(false); // ローディング終了
            if (response.ok) {
                alert("アップロード成功！");
                navigate(`/qa/${id}`);
            } else {
                alert("アップロード失敗");
                navigate(`/qa/${id}/edit`); // ← ここで画面遷移
            }
        } catch (error) {
            console.error("送信エラー:", error);
            setIsLoading(false);
            alert("送信エラー");
        }
    };






    const isValidAnswers = (): boolean => {
        if (!qaInfo?.title.trim()) return false;

        return qaItems.every(item => {
            const trimmedAnswers = item.answer.map(ans => ans.trim());

            const hasEmpty = trimmedAnswers.some(ans => ans === "");
            const hasDuplicate = new Set(trimmedAnswers).size !== trimmedAnswers.length;

            if (qaInfo.mode === "記述式問題") {
                return !hasEmpty && !hasDuplicate;
            } else {
                const allValid = trimmedAnswers.every(ans => item.options.includes(ans));
                return !hasEmpty && !hasDuplicate && allValid;
            }
        });
    };

    const handleHelpClick = () => {
        alert("ここに使い方ガイドを表示します。");
      };

    return (
        <div className="qaedit-container">
            <HelpButton onClick={handleHelpClick} />
            <div className="qaedit-title-input">
                <input
                    className={`qaedit-input-title ${!qaInfo?.title.trim() ? "invalid-input" : ""}`}
                    value={qaInfo?.title || ""}
                    onChange={(e) =>
                        setQaInfo(info => info ? { ...info, title: e.target.value } : null)
                    }
                    placeholder="タイトル"
                />
                {!qaInfo?.title.trim() && (
                    <p className="qaedit-warning">※ タイトルを入力してください</p>
                )}
            </div>

            <div className="qaedit-header">
                <div className="qaedit-classname-box">
                    <label className="qaedit-label">授業名</label>
                    <input
                        className="qaedit-input"
                        value={qaInfo?.className || ""}
                        onChange={(e) => setQaInfo(info => info ? { ...info, className: e.target.value } : null)}
                    />
                </div>
                {qaInfo && <p className="qaedit-date">
                    作成日: {
                        qaInfo.created_at.length >= 12
                            ? `${qaInfo.created_at.slice(0, 4)}.${qaInfo.created_at.slice(4, 6)}.${qaInfo.created_at.slice(6, 8)} ${qaInfo.created_at.slice(8, 10)}:${qaInfo.created_at.slice(10, 12)}`
                            : qaInfo.created_at
                    }
                </p>}
            </div>

            <ul className="qaedit-list">
                {qaItems.map((item, index) => (
                    <li key={index} className="qaedit-item">
                        <p className="qaedit-question">Q{index + 1}</p>
                        <label className="qaedit-label">問題</label>
                        <textarea
                            className="qaedit-textarea"
                            value={item.question}
                            onChange={(e) => handleQuestionChange(index, "question", e.target.value)}
                        />
                        {qaInfo?.mode !== "記述式問題" && (
                            <>
                                <label className="qaedit-label">選択肢</label>
                                <ul className="qaedit-option-list">
                                    {item.options.map((opt, optIndex) => (
                                        <li key={optIndex} className="qaedit-option-item">
                                            <input
                                                className="qaedit-input"
                                                value={opt}
                                                onChange={(e) => handleOptionChange(index, optIndex, e.target.value)}
                                                placeholder={`選択肢 ${optIndex + 1}`}
                                            />
                                        </li>
                                    ))}
                                </ul>
                            </>
                        )}

                        <label className="qaedit-label">答え</label>
                        {qaInfo?.mode === "４択複数選択問題" ? (
                            <>
                                {item.answer.map((ans, ansIndex) => (
                                    <div key={ansIndex} className="qaedit-answer-row">
                                        <input
                                            className={`qaedit-input ${!item.options.includes(ans.trim()) ? "invalid-answer" : ""
                                                }`}
                                            value={ans || ""}
                                            onChange={(e) => handleAnswerChange(index, ansIndex, e.target.value)}
                                            placeholder={`答え ${ansIndex + 1}`}
                                        />
                                        {item.answer.length > 1 && (
                                            <button
                                                type="button"
                                                className="qaedit-remove-answer"
                                                onClick={() => removeAnswerField(index, ansIndex)}
                                            >
                                                ×
                                            </button>
                                        )}
                                    </div>
                                ))}
                                {item.answer.length < 4 && (
                                    <button
                                        type="button"
                                        className="qaedit-add-answer"
                                        onClick={() => addAnswerField(index)}
                                    >
                                        ＋ 答えを追加
                                    </button>
                                )}
                                {/* 重複がある場合に警告 */}
                                {(() => {
                                    const trimmed = item.answer.map(ans => ans.trim());
                                    const hasDuplicate = new Set(trimmed).size !== trimmed.length;
                                    return hasDuplicate ? (
                                        <p className="qaedit-warning">※ 同じ答えが複数あります</p>
                                    ) : null;
                                })()}
                            </>
                        ) : (
                            <input
                                className={`qaedit-input ${qaInfo?.mode !== "記述式問題" &&
                                    !item.options.includes(item.answer[0]?.trim?.())
                                    ? "invalid-answer"
                                    : ""
                                    }`}
                                value={item.answer[0] || ""}
                                onChange={(e) => handleAnswerChange(index, 0, e.target.value)}
                                placeholder="答え"
                            />
                        )}

                        {qaInfo?.mode !== "記述式問題" &&
                            item.answer.some(ans => !item.options.includes(ans.trim())) && (
                                <p className="qaedit-warning">※ 答えの中に選択肢と一致しないものがあります</p>
                            )}

                    </li>
                ))}
            </ul>

            {/* 高度な設定トグル */}
            <div className="qaedit-advanced-toggle">
                <button
                    className={`qaedit-toggle-button ${showAdvanced ? "open" : ""}`}
                    onClick={() => setShowAdvanced(prev => !prev)}
                >
                    {showAdvanced ? "▲ 高度な設定を閉じる" : "▼ 高度な設定"}
                </button>

                {showAdvanced && (
                    <div className="qaedit-advanced-settings">
                        <div className="uploader-container">
                            <h2>追加資料アップロード</h2>
                            <h4>（.csvファイルのみ対応、カラム名に"質問"、"回答"が存在すること）</h4>
                            <p className="title">ファイルをアップロードしなければ同じ条件で再生成</p>
                            <p className="title">過去の質問と解答をCSV形式でアップロードすれば、
                                <br />それらを考慮した生成を行う</p>

                            {!file ? (
                                <div
                                    className="upload-box"
                                    onDrop={handleDrop}
                                    onDragOver={handleDragOver}
                                    onClick={() => document.getElementById("hiddenFileInput")?.click()}
                                >
                                    <p>ここにCSVファイルをドラッグ＆ドロップ、<br />またはクリックして選択</p>
                                    <input
                                        type="file"
                                        id="hiddenFileInput"
                                        accept="text/csv"
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
                    </div>
                )}
            </div>

            <div className="qaedit-save-button">
                <button className="qaedit-button delete" onClick={handleDelete}>削除</button>
                <button
                    className="qaedit-button"
                    onClick={handleSave}
                    disabled={!isValidAnswers()}
                    title={!isValidAnswers() ? "タイトルと答えの整合性が必要です" : ""}
                >
                    保存
                </button>
            </div>
        </div>
    );
};

export default QAEdit;
