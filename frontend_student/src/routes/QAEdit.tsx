import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import "./QAEdit.css";

interface QAItem {
    qa_id: number;
    question: string;
    options: string[];
    answer: string;
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
                    setQaItems(itemsRes.data);
                    setQaInfo(infoRes.data);
                })
                .catch(err => {
                    console.error("データ取得失敗:", err);
                });
        }
    }, [id]);

    const handleQuestionChange = (
        index: number,
        key: keyof QAItem,
        value: string
    ) => {
        const updated = [...qaItems];
        if (key === "options") {
            updated[index][key] = value.split(",").map(v => v.trim());
        } else {
            (updated[index] as any)[key] = value;
        }
        setQaItems(updated);
    };

    const handleSave = () => {
        if (!id || !qaInfo) return;

        Promise.all([
            axios.patch(`http://localhost:8000/qainfo/${id}`, qaInfo),
            axios.patch(`http://localhost:8000/qaitem/${id}`, qaItems)
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

    return (
        <div className="qaedit-container">
            <div className="qaedit-title-input">
                <input
                    className="qaedit-input-title"
                    value={qaInfo?.title || ""}
                    onChange={(e) => setQaInfo(info => info ? { ...info, title: e.target.value } : null)}
                    placeholder="タイトル"
                />
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
                        <label className="qaedit-label">選択肢（カンマ区切り）</label>
                        <input
                            className="qaedit-input"
                            value={item.options.join(", ")}
                            onChange={(e) => handleQuestionChange(index, "options", e.target.value)}
                        />
                        <label className="qaedit-label">答え</label>
                        <input
                            className="qaedit-input"
                            value={item.answer}
                            onChange={(e) => handleQuestionChange(index, "answer", e.target.value)}
                        />
                    </li>
                ))}
            </ul>

            <div className="qaedit-save-button">
                <button className="qaedit-button delete" onClick={handleDelete}>削除</button>
                <button className="qaedit-button" onClick={handleSave}>保存</button>
            </div>
        </div>
    );
};

export default QAEdit;
