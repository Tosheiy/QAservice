import React from 'react';
import './styles/App.css';
import Sidebar from './components/Sidebar';
import QAList from "./routes/QAList";
import QASolve from "./routes/QASolve"
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<QAList />} />
            <Route path="/qa" element={<QAList />} />
            <Route path="/qa/:id/solve" element={<QASolve />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;