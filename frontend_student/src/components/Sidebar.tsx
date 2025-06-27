import React from 'react';
import './Sidebar.css';
import { useNavigate } from 'react-router-dom';

const Sidebar = () => {
    const navigate = useNavigate();
    return (
        <div className="sidebar">
            <h2>生徒用QA回答</h2>
            <nav>
                <ul>
                    <li className="sidebar-item" onClick={() => navigate('/qa')}>
                        QA配信データベース
                    </li>
                </ul>
            </nav>
        </div>
    );
};

export default Sidebar;
