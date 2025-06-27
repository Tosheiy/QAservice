import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import "./QADetail.css";

import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    LineChart, Line, ResponsiveContainer
} from "recharts";

interface QAItem {
    qa_id: number;
    question: string;
    options: string[];
    answer: string;
    // satisfuction
}

interface QAInfo {
    id: number;
    created_at: string;
    className: string;
    title: string;
    mode: string;
}

const optionStats = [
    { option: "Tokyo", count: 4 },
    { option: "Osaka", count: 2 },
    { option: "Kyoto", count: 2 },
];

const accuracyOverTime = [
    { date: "12/26", accuracy: 100 },
    { date: "12/27", accuracy: 0 },
    { date: "12/28", accuracy: 0 },
    { date: "12/29", accuracy: 100 },
    { date: "12/30", accuracy: 0 },
    { date: "1/1", accuracy: 0 },
    { date: "1/2", accuracy: 100 },
];

const QADetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [qaItems, setQaItems] = useState<QAItem[]>([]);
    const [qaInfo, setQaInfo] = useState<QAInfo | null>(null);

    useEffect(() => {
        if (id) {
            // 並行して両方取得
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

    return (
        <div className="qadetail-result-container">
            <h1 className="qadetail-title">{qaInfo?.title ?? "読み込み中..."}</h1>

            {qaInfo && (
                <div className="qadetail-header-info">
                    <p className="qadetail-classname">授業名: {qaInfo.className}</p>
                    <p className="qadetail-date">            
                        作成日: {
                        qaInfo.created_at.length >= 12
                            ? `${qaInfo.created_at.slice(0, 4)}.${qaInfo.created_at.slice(4, 6)}.${qaInfo.created_at.slice(6, 8)} ${qaInfo.created_at.slice(8, 10)}:${qaInfo.created_at.slice(10, 12)}`
                            : qaInfo.created_at
                    }
                    </p>
                    {/* <p className="qadetail-mode">形式: {qaInfo.mode}</p> */}
                </div>
            )}

            {qaItems.length > 0 ? (
                <>
                    <div className="qadetail-analysis-graphs">
                        <h2 className="qadetail-analysis-title">分析結果</h2>

                        <div className="qadetail-charts-row">
                            <div className="qadetail-chart">
                                <h3>選択肢の選ばれた回数</h3>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={optionStats}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="option" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Bar dataKey="count" fill="#007acc" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="qadetail-chart">
                                <h3>正解率の推移</h3>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart data={accuracyOverTime}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis domain={[0, 100]} />
                                        <Tooltip />
                                        <Legend />
                                        <Line type="monotone" dataKey="accuracy" stroke="#ff6600" />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    <div className="qadetail-analysis">
                        <p>分析結果: 正解率 43%、誤答は「Osaka」「Kyoto」が多い傾向</p>
                    </div>

                    <p className="qadetail-history-title">クイズ詳細</p>
                    <div className="qadetail-history-container">
                        <ul className="qadetail-history-list">
                            {qaItems.map((item, index) => (
                                <li key={index} className="qadetail-history-card">
                                    <p><strong>問題：</strong> {item.question}</p>

                                    {item.options && item.options.length > 0 && (
                                        <ul className="option-list">
                                            {item.options.map((opt: string, i: number) => (
                                                <li key={i}>{opt}</li>
                                            ))}
                                        </ul>
                                    )}

                                    <p><strong>答え：</strong> {item.answer}</p>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="qaedit-save-button">
                        <Link to={`/qa/${id}/edit`} className="qaedit-button">編集する</Link>
                    </div>
                </>
            ) : (
                <p>データが見つかりません。</p>
            )}
        </div>
    );
};

export default QADetail;
