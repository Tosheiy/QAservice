import React from 'react';
import { useLocation } from 'react-router-dom';
import './QADisplay.css';


// QAデータの構造
/*
  {
    "id": 0, // このクイズ固有ID
    "qa_id": 0, // このクイズが属するグループのID
    "created_at": 2022-12-25,
    "question": where is the capital city in Japan?
    "options": ["Tokyo", "Osaka", "Kyoto"],
    "answer": "Tokyo",
    "mode": "multiple-choice"
  },
 */

const QADisplay: React.FC = () => {
    const location = useLocation();
    const qaData = location.state?.qaData;

    return (
        <div className="qa-result-container">
            <h1 className="qa-title">生成されたQA一覧</h1>
            {qaData ? (
                <ul className="qa-list">
                    {qaData.map((item: any, index: number) => (
                        <li key={index} className="qa-item">
                            <p className="qa-question">Q{index + 1}: {item.question}</p>

                            {item.options && item.options.length > 0 && (
                                <ul className="qa-options">
                                    {item.options.map((opt: string, i: number) => (
                                        <li key={i}>・{opt}</li>
                                    ))}
                                </ul>
                            )}

                            <p className="qa-answer">Answer: {item.answer}</p>

                            {item.created_at && (
                                <p className="qa-date">作成日: {item.created_at}</p>
                            )}
                        </li>
                    ))}
                </ul>
            ) : (
                <p>データがありません。</p>
            )}
        </div>
    );
};

export default QADisplay;
