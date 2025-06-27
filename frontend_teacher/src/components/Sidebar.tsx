import React from 'react';
import './Sidebar.css';
import { useNavigate } from 'react-router-dom';

const Sidebar = () => {
    const navigate = useNavigate();
    return (
        <div className="sidebar">
            <h2>講師用QA生成分析</h2>
            <nav>
                <ul>
                    <li className="sidebar-item" onClick={() => navigate('/')}>
                        ホーム
                    </li>
                    <li className="sidebar-item" onClick={() => navigate('/qa')}>
                        QAデータベース
                    </li>
                </ul>
            </nav>
        </div>
    );
};

export default Sidebar;
