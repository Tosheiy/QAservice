import React from 'react';
import './styles/App.css';
import Sidebar from './components/Sidebar';
import FileUploader from './components/FileUploader';
import QAList from "./routes/QAList";
import QADetail from "./routes/QADetail";
import QAEdit from "./routes/QAEdit";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<FileUploader />} />
            <Route path="/qa" element={<QAList />} />
            <Route path="/qa/:id" element={<QADetail />} />
            <Route path="/qa/:id/edit" element={<QAEdit />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;