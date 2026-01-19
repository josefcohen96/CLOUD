import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X, FileText, Calendar } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './MealHistory.css'; // ייבוא העיצוב החדש
import { Sparkles, Scale, Info } from 'lucide-react'; // תוסיף לייבואים

const API_URL = "https://ldclmiawsh.execute-api.us-east-1.amazonaws.com/default";

const MealDetails = ({ meal, onClose, userId }) => {
  const [mealReport, setMealReport] = useState([]);
  const [loadingReport, setLoadingReport] = useState(false);
  let analysisContent = null;

  useEffect(() => {
    if (meal?.meal_id && userId) {
      setLoadingReport(true);
      axios.get(`${API_URL}/report/${userId}?meal_id=${meal.meal_id}`)
        .then(res => setMealReport(res.data.report || []))
        .catch(err => {
          console.error("Error fetching meal report:", err);
          setMealReport([]);
        })
        .finally(() => setLoadingReport(false));
    }
  }, [meal?.meal_id, userId]);


  // בתוך קומפוננטת MealDetails:
  try {
    const data = typeof meal.ai_analysis_summary === 'string'
      ? JSON.parse(meal.ai_analysis_summary)
      : meal.ai_analysis_summary;

    analysisContent = (
      <div className="ai-analysis-container">
        {/* סיכום מקצועי */}
        <div className="professional-summary">
          <div className="summary-header">
            <Sparkles size={18} />
            <span>סיכום קליני</span>
          </div>

          <p className="analysis-paragraph">{data.overall_analysis || data.summary}</p>
        </div>

        {/* פירוט מאכלים */}
        <div className="food-items-grid">
          {data.items?.map((item, idx) => (
            <div key={idx} className="food-item-card">
              <div className="item-header">
                <span className="food-name">{item.food_name}</span>
                <span className="food-weight">
                  <Scale size={12} style={{ marginLeft: '4px' }} />
                  {item.estimated_weight_grams}g
                </span>
              </div>

              <div className="item-details-row">
                <div className="detail-group">
                  <span className="detail-label">קלוריות</span>
                  <span className="detail-value">{item.macros?.calories} kcal</span>
                </div>
                <div className="detail-group">
                  <span className="detail-label">חלבון</span>
                  <span className="detail-value">{item.macros?.protein}g</span>
                </div>
              </div>

              {item.micros && Object.keys(item.micros).length > 0 && (
                <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px dashed #f1f5f9' }}>
                  <span className="detail-label">ויטמינים ומינרלים בולטים:</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '5px' }}>
                    {Object.entries(item.micros).map(([name, val]) => (
                      <span key={name} style={{ fontSize: '0.8rem', background: '#f0f9ff', color: '#0369a1', padding: '2px 8px', borderRadius: '4px', border: '1px solid #bae6fd' }}>
                        {name}: {val}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  } catch (e) {
    // Fallback למקרה שהטקסט הוא לא JSON תקין
    analysisContent = (
      <div className="professional-summary">
        <div className="summary-header"><Info size={18} /><span>ניתוח טקסטואלי</span></div>
        <p className="analysis-paragraph">{meal.ai_analysis_summary}</p>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">
            <FileText size={24} style={{ marginRight: '10px', color: '#2563eb' }} />
            דוח ארוחה מפורט
          </h3>
          <button onClick={onClose} className="close-icon-button">
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="meal-meta">
            <Calendar size={16} style={{ marginRight: '5px' }} />
            <strong>תאריך:</strong> {new Date(meal.created_at).toLocaleDateString('he-IL')}
            <span style={{ margin: '0 10px' }}>|</span>
            <strong>שעה:</strong> {new Date(meal.created_at).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}
          </div>

          {meal.image_url && (
            <div className="image-container">
              <img src={meal.image_url} alt="Meal" className="meal-image" />
            </div>
          )}

          <div className="chart-section">
            <h4 className="section-title">תרומה תזונתית לארוחה זו (%)</h4>
            <div style={{ height: 180, width: '100%' }}>
              <ResponsiveContainer>
                <BarChart data={mealReport}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="nutrient_name" hide />
                  <YAxis fontSize={10} tick={{ fill: '#64748b' }} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }} />
                  <Bar dataKey="percentage" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                    {mealReport.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.percentage > 50 ? '#10b981' : '#3b82f6'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="scrollable-content">
            <h4 className="section-title">ניתוח AI קליני</h4>
            {analysisContent}
          </div>
        </div>
      </div>
    </div>
  );
};

export default function MealHistory({ userId, lastUpdated }) {
  const [meals, setMeals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMeal, setSelectedMeal] = useState(null);

  useEffect(() => {
    if (userId) fetchHistory();
  }, [userId, lastUpdated]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/history/${userId}`);
      setMeals(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading-state">טוען היסטוריה...</div>;
  if (meals.length === 0) return <div className="empty-state">אין עדיין ארוחות שמורות.</div>;

  return (
    <div className="meal-history-container">
      <h2 className="history-title">הארוחות שלי</h2>
      <div className="meal-grid">
        {meals.map((meal) => (
          <div key={meal.meal_id} className="meal-card" onClick={() => setSelectedMeal(meal)}>
            <div className="card-header">
              <span style={{ fontSize: '1.2rem' }}>📅</span> {new Date(meal.created_at).toLocaleDateString('he-IL', { day: 'numeric', month: 'numeric' })}
            </div>
            <div className="card-body">
              <span style={{ fontSize: '1.1rem' }}>🕒</span> {new Date(meal.created_at).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div className="card-footer">
              לחץ לפרטים
            </div>
          </div>
        ))}
      </div>

      {selectedMeal && (
        <MealDetails
          meal={selectedMeal}
          userId={userId}
          onClose={() => setSelectedMeal(null)}
        />
      )}
    </div>
  );
}