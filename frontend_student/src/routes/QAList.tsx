import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import "./QAList.css";

interface QAOverview {
    id: number;
    title: string;
}

interface QAStatus extends QAOverview {
    is_solved: boolean;
}

const QAList: React.FC = () => {
    const [qaList, setQaList] = useState<QAStatus[]>([]);
    const uid = localStorage.getItem("uid") || "guest";

    useEffect(() => {
        axios.get("http://localhost:8000/qainfo")
            .then(async (response) => {
                const list: QAOverview[] = response.data;

                // 各クイズについて is_solved を問い合わせて付加
                const updatedList: QAStatus[] = await Promise.all(
                    list.map(async (qa) => {
                        try {
                            const res = await axios.get(`http://localhost:8000/qaresult/${qa.id}`, {
                                params: { u_id: uid }
                            });
                            return { ...qa, is_solved: res.data.is_solved === 1 };
                        } catch (err) {
                            console.error(`解答状況の取得に失敗: id=${qa.id}`, err);
                            return { ...qa, is_solved: false };
                        }
                    })
                );

                // 🔽 解いていないもの（is_solved: false）を上にソート
                updatedList.sort((a, b) => {
                    return Number(a.is_solved) - Number(b.is_solved);
                });

                setQaList(updatedList);
            })
            .catch((error) => {
                console.error("データの取得に失敗しました", error);
            });
    }, []);
    

    return (
        <div className="qa-container">
            <h1 className="qa-title">QA一覧</h1>
            <p className="qa-description">以下は登録されているQA項目の一覧です。カードをクリックすると詳細ページが表示されます。</p>
            <div className="qa-card-container">
                {qaList.map((qa) => (
                    qa.is_solved ? (
                        <div key={qa.id} className="qa-card solved">
                            <h2 className="qa-card-title">{qa.title}</h2>
                            <p className="qa-status">✅ 解答済み</p>
                        </div>
                    ) : (
                        <Link
                            to={`/qa/${qa.id}/solve`}
                            key={qa.id}
                            className="qa-card-link"
                            style={{ textDecoration: 'none', color: 'inherit' }}
                        >
                            <div className="qa-card">
                                <h2 className="qa-card-title">{qa.title}</h2>
                                <p className="qa-status">📝 解答する</p>
                            </div>
                        </Link>
                    )
                ))}
            </div>
        </div>
    );
};

export default QAList;
