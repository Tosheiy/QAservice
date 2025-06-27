import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import "./QAEdit.css";

interface QAItem {
    qa_id: number;
    question: string;
    options: string[];
    answer: string[]; // 複数対応
    satisfaction: number;
}

interface QAInfo {
    created_at: string;
    className: string;
    title: string;
    mode: string;
}

const QAEdit: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [qaItems, setQaItems] = useState<QAItem[]>([]);
    const [qaInfo, setQaInfo] = useState<QAInfo | null>(null);

    useEffect(() => {
        if (id) {
            Promise.all([
                axios.get<QAItem[]>(`http://localhost:8000/qaitem/${id}`),
                axios.get<QAInfo>(`http://localhost:8000/qainfo/${id}`)
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
            axios.patch(`http://localhost:8000/qainfo/${id}`, qaInfo),
            axios.patch(`http://localhost:8000/qaitem/${id}`, preparedItems)
        ])
            .then(() => navigate(`/qa/${id}`))
            .catch(err => console.error("保存失敗:", err));
    };

    const handleDelete = () => {
        if (!id) return;

        Promise.all([
            axios.delete(`http://localhost:8000/qainfo/${id}`),
            axios.delete(`http://localhost:8000/qaitem/${id}`)
        ])
            .then(() => navigate("/qa"))
            .catch(err => console.error("削除失敗:", err));
    };

    const isValidAnswers = (): boolean => {
        return (
            qaInfo?.title.trim() !== "" &&
            qaItems.every(item => {
                if (qaInfo?.mode === "記述式問題") {
                    return item.answer.length > 0 && item.answer.every(ans => ans.trim() !== "");
                } else {
                    return item.answer.length > 0 && item.answer.every(ans => item.options.includes(ans.trim()));
                }
            })
        );
    };

    return (
        <div className="qaedit-container">
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
                        {(qaInfo?.mode === "４択複数選択問題")
                            ? item.answer.map((ans, ansIndex) => (
                                <div key={ansIndex} className="qaedit-answer-row">
                                    <input
                                        className={`qaedit-input ${qaInfo?.mode !== "記述式問題" && !item.options.includes(item.answer[0]?.trim?.())
                                                ? "invalid-answer"
                                                : ""
                                            }`}
                                        value={item.answer[0] || ""}
                                        onChange={(e) => handleAnswerChange(index, 0, e.target.value)}
                                    />
                                    {item.answer.length > 1 && (
                                        <button className="qaedit-remove-answer" onClick={() => removeAnswerField(index, ansIndex)}>×</button>
                                    )}
                                </div>
                            ))
                            : (
                                <input
                                    className={`qaedit-input ${qaInfo?.mode !== "記述式問題" && !item.options.includes(item.answer[0]?.trim?.())
                                            ? "invalid-answer"
                                            : ""
                                        }`}
                                    value={item.answer[0] || ""}
                                    onChange={(e) => handleAnswerChange(index, 0, e.target.value)}
                                />
                            )
                        }

                        {/* 答え追加ボタン（modeが４択複数問題のときのみ） */}
                        {qaInfo?.mode === "４択複数選択問題" && (
                            <button className="qaedit-add-answer" onClick={() => addAnswerField(index)}>＋ 答えを追加</button>
                        )}
                        {qaInfo?.mode !== "記述式問題" &&
                            item.answer.some(ans => !item.options.includes(ans.trim())) && (
                                <p className="qaedit-warning">※ 答えの中に選択肢と一致しないものがあります</p>
                            )}

                    </li>
                ))}
            </ul>

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
