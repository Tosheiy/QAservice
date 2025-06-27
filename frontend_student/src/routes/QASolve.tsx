import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import "./QASolve.css";

interface QAItem {
    qa_id: number;
    question: string;
    options: string[];
    answer: string | string[];
    satisfaction: number;
}

interface AnswerState {
    [qa_id: number]: string | string[];
}

const getOrCreateUID = (): string => {
    const stored = localStorage.getItem("uid");
    if (stored) return stored;

    const newUID = Math.random().toString(36).substring(2, 10);
    localStorage.setItem("uid", newUID);
    return newUID;
};

const QASolve: React.FC = () => {
    const { id } = useParams();
    const [questions, setQuestions] = useState<QAItem[]>([]);
    const [mode, setMode] = useState<string>("");
    const [title, setTitle] = useState<string>("");
    const [answers, setAnswers] = useState<AnswerState>({});
    const [submitted, setSubmitted] = useState(false);
    const uid = getOrCreateUID();
    const [satisfaction, setSatisfaction] = useState<{ [qa_id: number]: number }>({});

    useEffect(() => {
        axios.get(`http://localhost:8000/qainfo/${id}`)
            .then((res) => {
                setMode(res.data.mode);
                setTitle(res.data.title);
            });

        axios.get(`http://localhost:8000/qaitem/${id}`)
            .then((res) => {
                setQuestions(res.data);
            })
            .catch((err) => {
                console.error("問題の取得に失敗", err);
            });
    }, [id]);

    const handleChange = (qa_id: number, value: string) => {
        setAnswers(prev => ({ ...prev, [qa_id]: value }));
    };

    const handleMultiSelectChange = (qa_id: number, value: string) => {
        setAnswers(prev => {
            const current = (prev[qa_id] as string[]) || [];
            return current.includes(value)
                ? { ...prev, [qa_id]: current.filter(v => v !== value) }
                : { ...prev, [qa_id]: [...current, value] };
        });
    };

    const handleSatisfaction = (qa_id: number, value: number) => {
        setSatisfaction(prev => ({
            ...prev,
            [qa_id]: prev[qa_id] === value ? 0 : value
        }));
    };

    const handleSubmit = () => {
        const results = questions.map((q) => {
            const userAnswer = answers[q.qa_id];
            return {
                qa_id: q.qa_id,
                select: userAnswer,
                user_answer: userAnswer,
                satisfaction: satisfaction[q.qa_id] ?? 0
            };
        });

        const payload = {
            uid: uid,
            qa_info_id: id,
            results: results
        };

        axios.post("http://localhost:8000/submit", payload)
            .then(() => {
                alert("回答が送信されました");
                setSubmitted(true);
            })
            .catch((err) => {
                console.error("送信に失敗しました", err);
            });
    };

    if (submitted) return <div className="solve-container">回答ありがとうございました。</div>;
    console.log(mode)

    return (
        <div className="solve-container">
            <h2 className="solve-title">{title}</h2>
            <p className="solve-session">セッションID: {uid}</p>

            {questions.map((q, index) => (
                <div key={q.qa_id} className="solve-question-block">
                    <p className="solve-question">{index + 1}. {q.question}</p>

                    {(mode === "４択問題" || mode === "３択問題") && (
                        <div className="solve-options">
                            {q.options.map((opt, i) => (
                                <label key={i} className="solve-option">
                                    <input
                                        type="radio"
                                        name={`option-${q.qa_id}`}
                                        value={opt}
                                        checked={answers[q.qa_id] === opt}
                                        onChange={() => handleChange(q.qa_id, opt)}
                                    />
                                    {opt}
                                </label>
                            ))}
                        </div>
                    )}

                    {mode === "４択複数選択問題" && (
                        <div className="solve-options">
                            {q.options.map((opt, i) => (
                                <label key={i} className="solve-option">
                                    <input
                                        type="checkbox"
                                        value={opt}
                                        checked={Array.isArray(answers[q.qa_id]) && (answers[q.qa_id] as string[]).includes(opt)}
                                        onChange={() => handleMultiSelectChange(q.qa_id, opt)}
                                    />
                                    {opt}
                                </label>
                            ))}
                        </div>
                    )}

                    {mode === "記述式問題" && (
                        <textarea
                            className="solve-textarea"
                            value={(answers[q.qa_id] as string) || ""}
                            onChange={(e) => handleChange(q.qa_id, e.target.value)}
                            placeholder="ここに回答を入力してください"
                        />
                    )}

                    <div className="satisfaction-buttons">
                        <p className="satisfaction-label">この問題の評価をお願いします</p>
                        <button
                            className={`satisfaction-button ${satisfaction[q.qa_id] === 1 ? "selected-good" : ""}`}
                            onClick={() => handleSatisfaction(q.qa_id, 1)}
                        >
                            👍
                        </button>
                        <button
                            className={`satisfaction-button ${satisfaction[q.qa_id] === -1 ? "selected-bad" : ""}`}
                            onClick={() => handleSatisfaction(q.qa_id, -1)}
                        >
                            👎
                        </button>
                    </div>
                </div>
            ))}

            <button className="solve-submit-button" onClick={handleSubmit}>
                送信
            </button>
        </div>
    );
};

export default QASolve;
