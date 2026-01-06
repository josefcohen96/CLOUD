import { useState, useEffect } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell } from 'recharts';
import { Activity, Utensils, Zap, FileUp, HeartPulse, Droplet, User, Calendar } from 'lucide-react'; // אייקונים חדשים
import './App.css'
import MealHistory from './components/MealHistory'; // <--- ייבוא

// const API_URL = "http://127.0.0.1:8000"; 

const API_URL = "https://ldclmiawsh.execute-api.us-east-1.amazonaws.com/default";

function App() {
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [isCached, setIsCached] = useState(false); // האם התוצאה הגיעה מהקאש
  const [showCacheToast, setShowCacheToast] = useState(false); // האם להציג את ההתראה

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
    setIsCached(false); // איפוס לפני בדיקה חדשה
    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", selectedUserId);

    try {
      const response = await axios.post(`${API_URL}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (response.data.cached) {
        setIsCached(true);
        setShowCacheToast(true);
        // העלמת ההתראה אוטומטית אחרי 4 שניות
        setTimeout(() => setShowCacheToast(false), 4000);
      }
      fetchReport(selectedUserId);
      fetchRecommendations(selectedUserId);
    } catch (error) {
      console.error(error);
      alert("Analysis Failed");
    } finally {
      setLoading(false);
    }
  };

  const getBarColor = (val) => {
    if (val < 90) return "#ef4444"; // אדום מודרני
    if (val > 110) return "#3b82f6"; // כחול מודרני
    return "#10b981"; // ירוק מודרני
  };

  const getMetricValue = (nutrientName) => {
    if (!reportData || !reportData.report) return 0;
    const item = reportData.report.find(i =>
      i.nutrient_name.toLowerCase().replace(/_/g, ' ') ===
      nutrientName.toLowerCase().replace(/_/g, ' ')
    ); return item ? Math.round(item.percentage) : 0;
  };

  const topNutrients = reportData?.report
    ? [...reportData.report]
      .sort((a, b) => b.percentage - a.percentage) // מיון מהגבוה לנמוך לפי אחוז מהקצובה היומית
      .slice(0, 4) // לקיחת 4 הראשונים
    : [];

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">
          <HeartPulse color="#2563eb" size={28} />
          <h2>Clinical AI</h2>
        </div>

        <div className="control-group">
          <label><User size={14} style={{ display: 'inline', marginRight: 5 }} /> Select Patient</label>
          <select onChange={(e) => setSelectedUserId(e.target.value)} value={selectedUserId || ""}>
            {users.map(u => (
              <option key={u.user_id} value={u.user_id}>
                {u.full_name} {u.is_pregnant ? '(Pregnant)' : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label><FileUp size={14} style={{ display: 'inline', marginRight: 5 }} /> Upload Meal Image</label>

          {/* עיצוב כפתור העלאה מותאם אישית */}
          <div className="file-upload-box">
            <input type="file" onChange={(e) => setFile(e.target.files[0])} />
            <div className="upload-placeholder">
              {file ? file.name : "Click or Drag image here"}
            </div>
          </div>
          {selectedUserId && <MealHistory userId={selectedUserId} />}
          <button onClick={handleAnalyze} disabled={loading || !file} className="analyze-btn">
            {loading ? (
              <>Processing...</>
            ) : (
              <><Zap size={18} /> Analyze Meal</>
            )}
          </button>
        </div>
      </aside>

      <main className="content">
        {showCacheToast && (
          <div className="cache-toast">
            <Zap size={16} />
            <span><strong>Cache Hit!</strong> נשלף מיידית מ-Valkey Serverless</span>
          </div>
        )}
        <header>
          <h1>Nutritional Analysis Report</h1>
          <p>Real-time clinical assessment powered by GenAI</p>
        </header>

        {reportData && (
          <>
            <div className="dashboard-grid">
              {/* צד שמאל: סיכום טקסטואלי + מדדים */}
              <section className="card">
                <h3><Activity size={20} color="#2563eb" /> AI Assessment</h3>
                <div className="summary-content">
                  {reportData.summary}
                </div>

                <div className="metrics-container">
                  {topNutrients.length > 0 ? (
                    topNutrients.map((item, idx) => (
                      <div className="metric-item" key={idx}>
                        <span className="metric-label" style={{ textTransform: 'capitalize' }}>
                          {item.nutrient_name.replace(/_/g, ' ')}
                        </span>
                        <span className="metric-val" style={{ color: getBarColor(item.percentage) }}>
                          {Math.round(item.percentage)}%
                        </span>
                      </div>
                    ))
                  ) : (
                    <p style={{ color: '#64748b', fontSize: '0.9rem', textAlign: 'center' }}>
                      No nutrient data available for this meal.
                    </p>
                  )}
                </div>
              </section>

              {/* צד ימין: גרף */}
              <section className="card">
                <h3><Droplet size={20} color="#2563eb" /> Micronutrient Status</h3>
                <div style={{ height: 350, width: '100%' }}>
                  <ResponsiveContainer>
                    <BarChart data={reportData.report} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                      <XAxis dataKey="nutrient_name" angle={-45} textAnchor="end" height={80} interval={0} tick={{ fill: '#6b7280', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                      <Tooltip
                        cursor={{ fill: '#f3f4f6' }}
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      />
                      <ReferenceLine y={100} stroke="#9ca3af" strokeDasharray="3 3" />
                      <Bar dataKey="percentage" radius={[4, 4, 0, 0]}>
                        {reportData.report.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={getBarColor(entry.percentage)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>
            </div>

            {recommendations.length > 0 && (
              <section>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '20px', color: '#111827', display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Utensils size={24} color="#2563eb" />
                  Smart Optimization
                </h3>
                <div className="rec-grid">
                  {recommendations.map((rec, idx) => (
                    <div key={idx} className="rec-card">
                      <h4>{rec.food_name}</h4>
                      <div className="rec-meta">
                        <span>📏 {rec.serving}</span>
                        <span>🔥 {rec.calories} kcal</span>
                      </div>
                      <div className="rec-why">
                        {rec.reason}
                      </div>
                      <div className="tags">
                        {rec.tags.split(',').slice(0, 3).map(t => <span key={t}>{t}</span>)}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App