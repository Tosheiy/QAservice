import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import "./QAList.css";

interface QAOverview {
    id: number;
    title: string;
}
const apiUrl = process.env.REACT_APP_API_URL;
const QAList: React.FC = () => {
    const [qaList, setQaList] = useState<QAOverview[]>([]);

    useEffect(() => {
        // API からデータを取得
        axios.get(`${apiUrl}/qainfo`)
            .then((response) => {
                setQaList(response.data);
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
                    <Link
                        to={`/qa/${qa.id}`}
                        key={qa.id}
                        className="qa-card-link"
                        style={{ textDecoration: 'none', color: 'inherit' }}
                    >
                        <div className="qa-card">
                            <h2 className="qa-card-title">{qa.title}</h2>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
};

export default QAList;
