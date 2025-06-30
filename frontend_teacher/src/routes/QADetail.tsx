import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import "./QADetail.css";

import {
    PieChart, Pie, Cell,
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer
} from "recharts";


interface QAItem {
    qa_id: number;
    question: string;
    options: string[];
    answer: string[];
}

interface QAInfo {
    id: number;
    created_at: string;
    className: string;
    title: string;
    mode: string;
    questionCount: number;
}

interface AnalysisData {
    summary: {
        total_answers: number;
        total_correct: number;
        overall_accuracy: number;
    };
    score_distribution: Record<string, number>;
    per_quiz_analysis: {
        qa_id: number;
        correct_rate: number | null;
        option_distribution: Record<string, number>;
        total_answers: number;
        satisfaction_summary?: {
            good: number;
            neutral: number;
            bad: number;
        };
    }[];
}

const QADetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [qaItems, setQaItems] = useState<QAItem[]>([]);
    const [qaInfo, setQaInfo] = useState<QAInfo | null>(null);
    const [analysis, setAnalysis] = useState<AnalysisData | null>(null);

    const apiUrl = process.env.REACT_APP_API_URL;

    useEffect(() => {
        if (id) {
            Promise.all([
                axios.get<QAItem[]>(`${apiUrl}/qaitem/${id}`),
                axios.get<QAInfo>(`${apiUrl}/qainfo/${id}`),
                axios.get<AnalysisData>(`${apiUrl}/qaanalysis/${id}`),
            ])
                .then(([itemsRes, infoRes, analysisRes]) => {
                    setQaItems(itemsRes.data);
                    setQaInfo(infoRes.data);
                    setAnalysis(analysisRes.data);
                })
                .catch(err => {
                    console.error("データ取得失敗:", err);
                });
        }
    }, [id, apiUrl]); // これ

    useEffect(() => {
        const fetchAnalysis = () => {
            axios.get(`${apiUrl}/qaanalysis/${id}`)
                .then((res) => {
                    setAnalysis(res.data);
                })
                .catch((err) => {
                    console.error("分析情報の取得に失敗", err);
                });
        };

        fetchAnalysis(); // 初回呼び出し

        const intervalId = setInterval(fetchAnalysis, 5000); // 5秒ごとに再取得

        return () => clearInterval(intervalId); // クリーンアップ
    }, [id, apiUrl]);

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
                </div>
            )}

            {qaItems.length > 0 && analysis ? (
                <>
                    <div className="qadetail-analysis-graphs">
                        <h2 className="qadetail-analysis-title">分析結果</h2>



                        <div className="qadetail-charts-row">
                            {/* 正解率の一覧 */}
                            <div className="qadetail-chart">
                                <h3>各問題の正解率</h3>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={analysis.per_quiz_analysis.map(q => ({
                                        qa_id: `Q${q.qa_id + 1}`,
                                        accuracy: q.correct_rate !== null ? Math.round(q.correct_rate * 100) : 0,
                                    }))}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="qa_id" />
                                        <YAxis domain={[0, 100]} />
                                        <Tooltip />
                                        <Legend />
                                        <Bar dataKey="accuracy" fill="#28a745" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            {/* 得点分布 */}
                            <div className="qadetail-chart">
                                <h3>点数分布（人数）</h3>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart
                                        data={Array.from({ length: qaInfo?.questionCount! + 1 }, (_, i) => ({
                                            score: i.toString(),
                                            count: analysis.score_distribution[i.toString()] ?? 0
                                        }))}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="score" />
                                        <YAxis allowDecimals={false} />
                                        <Tooltip />
                                        <Legend />
                                        <Bar dataKey="count" fill="#6f42c1" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                        </div>
                    </div>

                    <div className="qadetail-analysis">
                        <p>
                            分析結果: 正解率 {Math.round(analysis.summary.overall_accuracy * 100)}%、回答数 {analysis.summary.total_answers} 件、正解数 {analysis.summary.total_correct} 件
                        </p>
                    </div>

                    <p className="qadetail-history-title">クイズ詳細</p>
                    <div className="qadetail-history-container">

                        <ul className="qadetail-history-list">
                            {qaItems.map((item, index) => {
                                const analysisForItem = analysis?.per_quiz_analysis.find(a => a.qa_id === item.qa_id);
                                const optionDist = analysisForItem?.option_distribution ?? {};
                                const satisf = analysisForItem?.satisfaction_summary;


                                return (
                                    <li key={index} className="qadetail-history-card">
                                        <div className="qa-label">問 {item.qa_id + 1}</div>
                                        <p className="qa-content">{item.question}</p>
                                        {/* 選択肢のリスト（記述式以外の場合のみ表示） */}
                                        {item.options.length > 0 && (
                                            <>
                                            <div className="qa-label">選択肢</div>
                                            <ul className="qa-list">
                                                {item.options.map((opt: string, i: number) => {
                                                    const normalizedOption = opt.trim().replace(/\s+/g, '').toLowerCase();
                                                    const normalizedAnswers = item.answer.map(ans =>
                                                        ans.trim().replace(/\r?\n/g, '').replace(/\s+/g, '').toLowerCase()
                                                    );

                                                    const isCorrect = normalizedAnswers.includes(normalizedOption);

                                                    const rawRate = optionDist[opt.trim()] ?? 0;
                                                    const percentage = Math.round(rawRate * 100);

                                                    return (
                                                        <li
                                                            key={i}
                                                            style={{
                                                                color: isCorrect ? "green" : undefined,
                                                                fontWeight: isCorrect ? "bold" : undefined
                                                            }}
                                                        >
                                                            {opt.trim()}（{percentage}%）
                                                        </li>
                                                    );
                                                })}
                                            </ul>
                                            </>
                                        )}


                                        <div className="qa-label">答え</div>
                                        <ul className="qa-list">
                                            {Array.isArray(item.answer)
                                                ? item.answer.map((ans, i) => <li key={i}>{ans}</li>)
                                                : <li>{item.answer}</li>}
                                        </ul>

                                        <hr className="qa-divider" />

                                        {/* 満足度グラフ（good または bad のいずれかが 1 件以上ある場合のみ表示） */}
                                        {(satisf?.good ?? 0) > 0 || (satisf?.bad ?? 0) > 0 ? (
                                            <div style={{ width: 500, height: 250, margin: '1rem auto' }}>
                                                <h4 style={{ textAlign: 'center' }}>満足度</h4>
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <PieChart>
                                                        <Pie
                                                            data={[
                                                                { name: "Good", value: satisf?.good ?? 0 },
                                                                { name: "Bad", value: satisf?.bad ?? 0 },
                                                            ]}
                                                            dataKey="value"
                                                            nameKey="name"
                                                            cx={150}
                                                            cy="50%"
                                                            outerRadius={80}
                                                            startAngle={90}
                                                            endAngle={-270}
                                                        >
                                                            <Cell fill="#28a745" />
                                                            <Cell fill="#dc3545" />
                                                        </Pie>
                                                        <Tooltip />
                                                        <Legend
                                                            layout="vertical"
                                                            verticalAlign="middle"
                                                            align="right"
                                                            wrapperStyle={{
                                                                fontSize: "12px",
                                                                paddingLeft: "20px",
                                                                paddingTop: "40px",
                                                            }}
                                                        />
                                                    </PieChart>
                                                </ResponsiveContainer>
                                            </div>
                                        ) : null}


                                    </li>
                                );
                            })}
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
