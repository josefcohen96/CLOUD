import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Recommendations from './components/Recommendations';

const API_URL = "https://ldclmiawsh.execute-api.us-east-1.amazonaws.com/default";

function App() {
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL}/users`)
      .then(res => {
        setUsers(res.data);
        if (res.data.length > 0) setSelectedUserId(res.data[0].user_id);
      })
      .catch(err => console.error("Error fetching users:", err));
  }, []);

  useEffect(() => {
    if (selectedUserId) {
      fetchReport(selectedUserId);
      fetchRecommendations(selectedUserId);
    }
  }, [selectedUserId]);

  const fetchReport = (id) => {
    axios.get(`${API_URL}/report/${id}`)
      .then(res => setReportData(res.data))
      .catch(err => console.error(err));
  };

  const fetchRecommendations = (id) => {
    axios.get(`${API_URL}/recommendations/${id}`)
      .then(res => setRecommendations(res.data))
      .catch(err => console.error(err));
  };

  const handleAnalyze = async () => {
    if (!file || !selectedUserId) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", selectedUserId);

    try {
      await axios.post(`${API_URL}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchReport(selectedUserId);
      fetchRecommendations(selectedUserId);
    } catch (error) {
      // 1. אם זה Timeout (504) או בעיית רשת, ננסה למשוך את הנתונים בכל זאת
      if (error.response?.status === 504 || error.code === 'ECONNABORTED') {
        console.warn("Operation timed out, checking if analysis completed in background...");

        // נחכה 5 שניות ונתן ל-backend לסיים
        await new Promise(resolve => setTimeout(resolve, 5000));

        // ננסה למשוך נתונים
        fetchReport(selectedUserId);
        fetchRecommendations(selectedUserId);
      } else {
        console.error(error);
        alert("Analysis Failed: " + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        users={users}
        selectedUserId={selectedUserId}
        setSelectedUserId={setSelectedUserId}
        setFile={setFile}
        file={file}
        handleAnalyze={handleAnalyze}
        loading={loading}
      />

      <main className="content">
        <header>
          <h1>Nutritional Analysis Report</h1>
          <p>Real-time clinical assessment powered by GenAI</p>
        </header>

        {reportData && (
          <>
            <Dashboard reportData={reportData} />
            <Recommendations recommendations={recommendations} />
          </>
        )}
      </main>
    </div>
  )
}

export default App