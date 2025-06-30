import React, { useState } from "react";

const HelpButton: React.FC<{ onClick?: () => void }> = ({ onClick }) => {
    const [isHovered, setIsHovered] = useState(false);

    return (
        <div
            onClick={onClick}
            title="使い方ガイド"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            style={{
                position: "fixed",
                top: "1rem",
                right: "1rem",
                width: "44px",
                height: "44px",
                borderRadius: "50%",
                backgroundColor: isHovered ? "#3498db" : "#ffffff", // ホバー時に青く
                border: "1px solid #ccc",
                color: isHovered ? "#ffffff" : "#2c3e50",           // 文字色も反転
                fontSize: "24px",
                fontWeight: "bold",
                textAlign: "center",
                lineHeight: "44px",
                cursor: "pointer",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                transition: "background-color 0.2s, color 0.2s",
                zIndex: 1000,
            }}
        >
            ❔
        </div>
    );
};

export default HelpButton;
